#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Fetch and add titles for bare links in references.

This bot will search for references which are only made of a link without title
(i.e. <ref>[https://www.google.fr/]</ref> or <ref>https://www.google.fr/</ref>)
and will fetch the html title from the link to use it as the title of the wiki
link in the reference, i.e.
<ref>[https://www.google.fr/search?q=test test - Google Search]</ref>

The bot checks every 20 edits a special stop page. If the page has been edited,
it stops.

Warning: Running this script on German Wikipedia is not allowed anymore.

As it uses it, you need to configure noreferences.py for your wiki, or it will
not work.

pdfinfo is needed for parsing pdf titles.

&params;

-limit:n          Stops after n edits

-xml:dump.xml     Should be used instead of a simple page fetching method from
                  pagegenerators.py for performance and load issues

-xmlstart         Page to start with when using an XML dump

-ignorepdf        Do not handle PDF files (handy if you use Windows and can't
                  get pdfinfo)

-summary          Use a custom edit summary. Otherwise it uses the default
                  one from i18n/reflinks.py
"""
# (C) Nicolas Dumazet (NicDumZ), 2008
# (C) Pywikibot team, 2008-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import codecs
import os
import re
import socket
import subprocess
import sys
import tempfile

from functools import partial

import pywikibot

from pywikibot import comms, i18n, pagegenerators, textlib, Bot
from pywikibot import config2 as config
from pywikibot.pagegenerators import (
    XMLDumpPageGenerator as _XMLDumpPageGenerator,
)
from pywikibot.tools.formatter import color_format

import requests

from scripts import noreferences

if sys.version_info[0] > 2:
    import http.client as httplib
    from urllib.error import URLError
else:
    import httplib
    from urllib2 import URLError

docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

localized_msg = ('fr', 'it', 'pl')  # localized message at MediaWiki

# localized message at specific wikipedia site
# should be moved to MediaWiki Pywikibot manual


stop_page = {
    'fr': u'Utilisateur:DumZiBoT/EditezCettePagePourMeStopper',
    'da': u'Bruger:DumZiBoT/EditThisPageToStopMe',
    'de': u'Benutzer:DumZiBoT/EditThisPageToStopMe',
    'fa': u'کاربر:Amirobot/EditThisPageToStopMe',
    'it': u'Utente:Marco27Bot/EditThisPageToStopMe',
    'ko': u'사용자:GrassnBreadRefBot/EditThisPageToStopMe1',
    'he': u'User:Matanyabot/EditThisPageToStopMe',
    'hu': u'User:Damibot/EditThisPageToStopMe',
    'en': u'User:DumZiBoT/EditThisPageToStopMe',
    'pl': u'Wikipedysta:MastiBot/EditThisPageToStopMe',
    'ru': u'User:Rubinbot/EditThisPageToStopMe',
    'ur': 'صارف:Shuaib-bot/EditThisPageToStopMe',
    'zh': u'User:Sz-iwbot',
}

deadLinkTag = {
    'fr': u'[%s] {{lien mort}}',
    'da': u'[%s] {{dødt link}}',
    'fa': u'[%s] {{پیوند مرده}}',
    'he': u'{{קישור שבור}}',
    'hi': '[%s] {{Dead link}}',
    'hu': u'[%s] {{halott link}}',
    'ko': u'[%s] {{죽은 바깥 고리}}',
    'es': u'{{enlace roto2|%s}}',
    'it': u'{{Collegamento interrotto|%s}}',
    'en': u'[%s] {{dead link}}',
    'pl': u'[%s] {{Martwy link}}',
    'ru': u'[%s] {{subst:dead}}',
    'sr': '[%s] {{dead link}}',
    'ur': '[%s] {{مردہ ربط}}',
}


soft404 = re.compile(
    r'\D404(\D|\Z)|error|errdoc|Not.{0,3}Found|sitedown|eventlog',
    re.IGNORECASE)
# matches an URL at the index of a website
dirIndex = re.compile(
    r'^\w+://[^/]+/((default|index)\.(asp|aspx|cgi|htm|html|phtml|mpx|mspx|php|shtml|var))?$',
    re.IGNORECASE)
# Extracts the domain name
domain = re.compile(r'^(\w+)://(?:www.|)([^/]+)')

globalbadtitles = r"""
# is
(test|
# starts with
    ^\W*(
            register
            |registration
            |(sign|log)[ \-]?in
            |subscribe
            |sign[ \-]?up
            |log[ \-]?on
            |untitled[ ]?(document|page|\d+|$)
            |404[ ]
        ).*
# anywhere
    |.*(
            403[ ]forbidden
            |(404|page|file|information|resource).*not([ ]*be)?[ ]*(available|found)
            |site.*disabled
            |error[ ]404
            |error.+not[ ]found
            |not[ ]found.+error
            |404[ ]error
            |\D404\D
            |check[ ]browser[ ]settings
            |log[ \-]?(on|in)[ ]to
            |site[ ]redirection
     ).*
# ends with
    |.*(
            register
            |registration
            |(sign|log)[ \-]?in
            |subscribe|sign[ \-]?up
            |log[ \-]?on
        )\W*$
)
"""
# Language-specific bad titles
badtitles = {
    'en': '',
    'fr': '.*(404|page|site).*en +travaux.*',
    'es': '.*sitio.*no +disponible.*',
    'it': '((pagina|sito) (non trovat[ao]|inesistente)|accedi|errore)',
    'ru': u'.*(Страница|страница).*(не[ ]*найдена|осутствует).*',
}

# Regex that match bare references
linksInRef = re.compile(
    # bracketed URLs
    r'(?i)<ref(?P<name>[^>]*)>\s*\[?(?P<url>(?:http|https)://(?:' +
    # unbracketed with()
    r'^\[\]\s<>"]+\([^\[\]\s<>"]+[^\[\]\s\.:;\\,<>\?"]+|' +
    # unbracketed without ()
    r'[^\[\]\s<>"]+[^\[\]\s\)\.:;\\,<>\?"]+|[^\[\]\s<>"]+))[!?,\s]*\]?\s*</ref>')

# Download this file :
# http://www.twoevils.org/files/wikipedia/404-links.txt.gz
# ( maintained by User:Dispenser )
listof404pages = '404-links.txt'

XmlDumpPageGenerator = partial(
    _XMLDumpPageGenerator, text_predicate=linksInRef.search)


class RefLink(object):

    """Container to handle a single bare reference."""

    def __init__(self, link, name):
        """Constructor."""
        self.refname = name
        self.link = link
        self.site = pywikibot.Site()
        self.linkComment = i18n.twtranslate(self.site, 'reflinks-comment')
        self.url = re.sub(u'#.*', '', self.link)
        self.title = None

    def refTitle(self):
        """Return the <ref> with its new title."""
        return '<ref%s>[%s %s<!-- %s -->]</ref>' % (self.refname, self.link,
                                                    self.title,
                                                    self.linkComment)

    def refLink(self):
        """No title has been found, return the unbracketed link."""
        return '<ref%s>%s</ref>' % (self.refname, self.link)

    def refDead(self):
        """Dead link, tag it with a {{dead link}}."""
        tag = i18n.translate(self.site, deadLinkTag)
        if not tag:
            dead_link = self.refLink()
        elif '%s' in tag:
            dead_link = '<ref%s>%s</ref>' % (self.refname, tag % self.link)
        else:
            dead_link = '<ref%s>%s</ref>' % (self.refname, tag)
        return dead_link

    def transform(self, ispdf=False):
        """Normalize the title."""
        # convert html entities
        if not ispdf:
            self.title = pywikibot.html2unicode(self.title)
        self.title = re.sub(r'-+', '-', self.title)
        # remove formatting, i.e long useless strings
        self.title = re.sub(r'[\.+\-=]{4,}', ' ', self.title)
        # remove \n and \r and Unicode spaces from titles
        self.title = re.sub(r'(?u)\s', ' ', self.title)
        self.title = re.sub(r'[\n\r\t]', ' ', self.title)
        # remove extra whitespaces
        # remove leading and trailing ./;/,/-/_/+/ /
        self.title = re.sub(r' +', ' ', self.title.strip(r'=.;,-+_ '))

        self.avoid_uppercase()
        # avoid closing the link before the end
        self.title = self.title.replace(']', '&#93;')
        # avoid multiple } being interpreted as a template inclusion
        self.title = self.title.replace('}}', '}&#125;')
        # prevent multiple quotes being interpreted as '' or '''
        self.title = self.title.replace('\'\'', '\'&#39;')
        self.title = pywikibot.unicode2html(self.title, self.site.encoding())
        # TODO : remove HTML when both opening and closing tags are included

    def avoid_uppercase(self):
        """
        Convert to title()-case if title is 70% uppercase characters.

        Skip title that has less than 6 characters.
        """
        if len(self.title) <= 6:
            return
        nb_upper = 0
        nb_letter = 0
        for letter in self.title:
            if letter.isupper():
                nb_upper += 1
            if letter.isalpha():
                nb_letter += 1
            if letter.isdigit():
                return
        if nb_upper / (nb_letter + 1) > .70:
            self.title = self.title.title()


class DuplicateReferences(object):

    """Helper to de-duplicate references in text.

    When some references are duplicated in an article,
    name the first, and remove the content of the others
    """

    def __init__(self):
        """Constructor."""
        # Match references
        self.REFS = re.compile(
            r'(?i)<ref(?P<params>[^>/]*)>(?P<content>.*?)</ref>')
        self.NAMES = re.compile(
            r'(?i).*name\s*=\s*(?P<quote>"?)\s*(?P<name>.+)\s*(?P=quote).*')
        self.GROUPS = re.compile(
            r'(?i).*group\s*=\s*(?P<quote>"?)\s*(?P<group>.+)\s*(?P=quote).*')
        self.autogen = i18n.twtranslate(pywikibot.Site(), 'reflinks-autogen')

    def process(self, text):
        """Process the page."""
        # keys are ref groups
        # values are a dict where :
        #   keys are ref content
        #   values are [name, [list of full ref matches],
        #               quoted, need_to_change]
        foundRefs = {}
        foundRefNames = {}
        # Replace key by [value, quoted]
        namedRepl = {}

        for match in self.REFS.finditer(text):
            content = match.group('content')
            if not content.strip():
                continue

            params = match.group('params')
            group = self.GROUPS.match(params)
            if group not in foundRefs:
                foundRefs[group] = {}

            groupdict = foundRefs[group]
            if content in groupdict:
                v = groupdict[content]
                v[1].append(match.group())
            else:
                v = [None, [match.group()], False, False]
            name = self.NAMES.match(params)
            if name:
                quoted = name.group('quote') == '"'
                name = name.group('name')
                if v[0]:
                    if v[0] != name:
                        namedRepl[name] = [v[0], v[2]]
                else:
                    # First name associated with this content

                    if name == 'population':
                        pywikibot.output(content)
                    if name not in foundRefNames:
                        # first time ever we meet this name
                        if name == 'population':
                            pywikibot.output("in")
                        v[2] = quoted
                        v[0] = name
                    else:
                        # if has_key, means that this name is used
                        # with another content. We'll need to change it
                        v[3] = True
                foundRefNames[name] = 1
            groupdict[content] = v

        id = 1
        while self.autogen + str(id) in foundRefNames:
            id += 1
        for (g, d) in foundRefs.items():
            if g:
                group = u"group=\"%s\" " % group
            else:
                group = u""

            for (k, v) in d.items():
                if len(v[1]) == 1 and not v[3]:
                    continue
                name = v[0]
                if not name:
                    name = '"%s%d"' % (self.autogen, id)
                    id += 1
                elif v[2]:
                    name = u'"%s"' % name
                named = u'<ref %sname=%s>%s</ref>' % (group, name, k)
                text = text.replace(v[1][0], named, 1)

                # make sure that the first (named ref) is not
                # removed later :
                pos = text.index(named) + len(named)
                header = text[:pos]
                end = text[pos:]

                unnamed = u'<ref %sname=%s />' % (group, name)
                for ref in v[1][1:]:
                    end = end.replace(ref, unnamed)
                text = header + end

        for (k, v) in namedRepl.items():
            # TODO : Support ref groups
            name = v[0]
            if v[1]:
                name = u'"%s"' % name
            text = re.sub(
                u'<ref name\\s*=\\s*(?P<quote>"?)\\s*%s\\s*(?P=quote)\\s*/>' % k,
                u'<ref name=%s />' % name, text)
        return text


class ReferencesRobot(Bot):

    """References bot."""

    def __init__(self, generator, **kwargs):
        """- generator : Page generator."""
        self.availableOptions.update({
            'ignorepdf': False,  # boolean
            'limit': None,  # int, stop after n modified pages
            'summary': None,
        })

        super(ReferencesRobot, self).__init__(**kwargs)
        self.generator = generator
        self.site = pywikibot.Site()
        self._use_fake_user_agent = config.fake_user_agent_default.get('reflinks', False)
        # Check
        manual = 'mw:Manual:Pywikibot/refLinks'
        code = None
        for alt in [self.site.code] + i18n._altlang(self.site.code):
            if alt in localized_msg:
                code = alt
                break
        if code:
            manual += '/%s' % code
        if self.getOption('summary') is None:
            self.msg = i18n.twtranslate(self.site, 'reflinks-msg', locals())
        else:
            self.msg = self.getOption('summary')

        local = i18n.translate(self.site, badtitles)
        if local:
            bad = '(' + globalbadtitles + '|' + local + ')'
        else:
            bad = globalbadtitles
        self.titleBlackList = re.compile(bad, re.I | re.S | re.X)
        self.norefbot = noreferences.NoReferencesBot(None, verbose=False)
        self.deduplicator = DuplicateReferences()

        self.site_stop_page = i18n.translate(self.site, stop_page)
        if self.site_stop_page:
            self.stop_page = pywikibot.Page(self.site, self.site_stop_page)
            if self.stop_page.exists():
                self.stop_page_rev_id = self.stop_page.latest_revision_id
            else:
                pywikibot.warning('The stop page %s does not exist'
                                  % self.stop_page.title(asLink=True))

        # Regex to grasp content-type meta HTML tag in HTML source
        self.META_CONTENT = re.compile(br'(?i)<meta[^>]*content\-type[^>]*>')
        # Extract the encoding from a charset property (from content-type !)
        self.CHARSET = re.compile(r'(?i)charset\s*=\s*(?P<enc>[^\'",;>/]*)')
        # Extract html title from page
        self.TITLE = re.compile(r'(?is)(?<=<title>).*?(?=</title>)')
        # Matches content inside <script>/<style>/HTML comments
        self.NON_HTML = re.compile(
            br'(?is)<script[^>]*>.*?</script>|<style[^>]*>.*?</style>|'
            br'<!--.*?-->|<!\[CDATA\[.*?\]\]>')

        # Authorized mime types for HTML pages
        self.MIME = re.compile(
            r'application/(?:xhtml\+xml|xml)|text/(?:ht|x)ml')

    def httpError(self, err_num, link, pagetitleaslink):
        """Log HTTP Error."""
        pywikibot.stdout('HTTP error ({0}) for {1} on {2}'
                         ''.format(err_num, link, pagetitleaslink))

    def getPDFTitle(self, ref, f):
        """Use pdfinfo to retrieve title from a PDF.

        FIXME: Unix-only, I'm afraid.

        """
        pywikibot.output(u'PDF file.')
        fd, infile = tempfile.mkstemp()
        urlobj = os.fdopen(fd, 'w+')
        urlobj.write(f.text)

        try:
            pdfinfo_out = subprocess.Popen([r"pdfinfo", "/dev/stdin"],
                                           stdin=urlobj, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           shell=False).communicate()[0]
            for aline in pdfinfo_out.splitlines():
                if aline.lower().startswith('title'):
                    ref.title = aline.split(None)[1:]
                    ref.title = ' '.join(ref.title)
                    if ref.title != '':
                        pywikibot.output(u'title: %s' % ref.title)
            pywikibot.output(u'PDF done.')
        except ValueError:
            pywikibot.output(u'pdfinfo value error.')
        except OSError:
            pywikibot.output(u'pdfinfo OS error.')
        except Exception:  # Ignore errors
            pywikibot.output(u'PDF processing error.')
            pywikibot.exception()
        finally:
            urlobj.close()
            os.unlink(infile)

    def run(self):
        """Run the Bot."""
        try:
            deadLinks = codecs.open(listof404pages, 'r', 'latin_1').read()
        except IOError:
            raise NotImplementedError(
                '404-links.txt is required for reflinks.py\n'
                'You need to download\n'
                'http://www.twoevils.org/files/wikipedia/404-links.txt.gz\n'
                'and to unzip it in the same directory')

        editedpages = 0
        for page in self.generator:
            try:
                # Load the page's text from the wiki
                new_text = page.get()
                if not page.canBeEdited():
                    pywikibot.output(u"You can't edit page %s"
                                     % page.title(asLink=True))
                    continue
            except pywikibot.NoPage:
                pywikibot.output(u'Page %s not found' % page.title(asLink=True))
                continue
            except pywikibot.IsRedirectPage:
                pywikibot.output(u'Page %s is a redirect'
                                 % page.title(asLink=True))
                continue

            # for each link to change
            for match in linksInRef.finditer(
                    textlib.removeDisabledParts(page.get())):

                link = match.group(u'url')
                # debugging purpose
                # print link
                if u'jstor.org' in link:
                    # TODO: Clean URL blacklist
                    continue

                ref = RefLink(link, match.group('name'))
                f = None

                try:
                    f = comms.http.fetch(
                        ref.url, use_fake_user_agent=self._use_fake_user_agent)

                    # Try to get Content-Type from server
                    contentType = f.response_headers.get('content-type')
                    if contentType and not self.MIME.search(contentType):
                        if ref.link.lower().endswith('.pdf') and \
                           not self.getOption('ignorepdf'):
                            # If file has a PDF suffix
                            self.getPDFTitle(ref, f)
                        else:
                            pywikibot.output(color_format(
                                '{lightyellow}WARNING{default} : '
                                'media : {0} ', ref.link))
                        if ref.title:
                            if not re.match(
                                    u'(?i) *microsoft (word|excel|visio)',
                                    ref.title):
                                ref.transform(ispdf=True)
                                repl = ref.refTitle()
                            else:
                                pywikibot.output(color_format(
                                    '{lightyellow}WARNING{default} : '
                                    'PDF title blacklisted : {0} ', ref.title))
                                repl = ref.refLink()
                        else:
                            repl = ref.refLink()
                        new_text = new_text.replace(match.group(), repl)
                        continue

                    # Get the real url where we end (http redirects !)
                    redir = f.data.url
                    if redir != ref.link and \
                       domain.findall(redir) == domain.findall(link):
                        if soft404.search(redir) and \
                           not soft404.search(ref.link):
                            pywikibot.output(color_format(
                                '{lightyellow}WARNING{default} : '
                                'Redirect 404 : {0} ', ref.link))
                            continue
                        if dirIndex.match(redir) and \
                           not dirIndex.match(ref.link):
                            pywikibot.output(color_format(
                                u'{lightyellow}WARNING{default} : '
                                u'Redirect to root : {0} ', ref.link))
                            continue

                    if f.status != requests.codes.ok:
                        pywikibot.output(u'HTTP error (%s) for %s on %s'
                                         % (f.status, ref.url,
                                            page.title(asLink=True)),
                                         toStdout=True)
                        # 410 Gone, indicates that the resource has been purposely
                        # removed
                        if f.status == 410 or \
                           (f.status == 404 and (u'\t%s\t' % ref.url in deadLinks)):
                            repl = ref.refDead()
                            new_text = new_text.replace(match.group(), repl)
                        continue

                    linkedpagetext = f.raw
                except UnicodeError:
                    # example : http://www.adminet.com/jo/20010615¦/ECOC0100037D.html
                    # in [[fr:Cyanure]]
                    pywikibot.output(color_format(
                        '{lightred}Bad link{default} : {0} in {1}',
                        ref.url, page.title(asLink=True)))
                    continue
                except (URLError,
                        socket.error,
                        IOError,
                        httplib.error,
                        pywikibot.FatalServerError,
                        pywikibot.Server504Error) as e:
                    pywikibot.output(u'Can\'t retrieve page %s : %s'
                                     % (ref.url, e))
                    continue

                # remove <script>/<style>/comments/CDATA tags
                linkedpagetext = self.NON_HTML.sub(b'', linkedpagetext)

                meta_content = self.META_CONTENT.search(linkedpagetext)
                enc = []
                s = None
                if contentType:
                    # use charset from http header
                    s = self.CHARSET.search(contentType)
                if meta_content:
                    tag = meta_content.group()
                    # Prefer the contentType from the HTTP header :
                    if not contentType:
                        contentType = tag
                    if not s:
                        # use charset from html
                        s = self.CHARSET.search(str(tag))
                if s:
                    tmp = s.group('enc').strip("\"' ").lower()
                    naked = re.sub(r'[ _\-]', '', tmp)
                    # Convert to python correct encoding names
                    if naked == "gb2312":
                        enc.append("gbk")
                    elif naked == "shiftjis":
                        enc.append("shift jis 2004")
                        enc.append("cp932")
                    elif naked == "xeucjp":
                        enc.append("euc-jp")
                    else:
                        enc.append(tmp)
                else:
                    pywikibot.output(u'No charset found for %s' % ref.link)
                if not contentType:
                    pywikibot.output(u'No content-type found for %s' % ref.link)
                    continue
                elif not self.MIME.search(contentType):
                    pywikibot.output(color_format(
                        '{lightyellow}WARNING{default} : media : {0} ',
                        ref.link))
                    repl = ref.refLink()
                    new_text = new_text.replace(match.group(), repl)
                    continue

                # Ugly hacks to try to survive when both server and page
                # return no encoding.
                # Uses most used encodings for each national suffix
                if u'.ru' in ref.link or u'.su' in ref.link:
                    # see http://www.sci.aha.ru/ATL/ra13a.htm : no server
                    # encoding, no page encoding
                    enc = enc + ['koi8-r', 'windows-1251']
                elif u'.jp' in ref.link:
                    enc.append("shift jis 2004")
                    enc.append("cp932")
                elif u'.kr' in ref.link:
                    enc.append("euc-kr")
                    enc.append("cp949")
                elif u'.zh' in ref.link:
                    enc.append("gbk")

                if 'utf-8' not in enc:
                    enc.append('utf-8')
                try:
                    u = linkedpagetext.decode(enc[0])   # Bug T69410
                except (UnicodeDecodeError, LookupError) as e:
                    pywikibot.output(u'%s : Decoding error - %s' % (ref.link, e))
                    continue

                # Retrieves the first non empty string inside <title> tags
                for m in self.TITLE.finditer(u):
                    t = m.group()
                    if t:
                        ref.title = t
                        ref.transform()
                        if ref.title:
                            break

                if not ref.title:
                    repl = ref.refLink()
                    new_text = new_text.replace(match.group(), repl)
                    pywikibot.output(u'%s : No title found...' % ref.link)
                    continue

                # XXX Ugly hack
                if u'Ã©' in ref.title:
                    repl = ref.refLink()
                    new_text = new_text.replace(match.group(), repl)
                    pywikibot.output(u'%s : Hybrid encoding...' % ref.link)
                    continue

                if self.titleBlackList.match(ref.title):
                    repl = ref.refLink()
                    new_text = new_text.replace(match.group(), repl)
                    pywikibot.output(color_format(
                        '{lightred}WARNING{default} {0} : '
                        'Blacklisted title ({1})', ref.link, ref.title))
                    continue

                # Truncate long titles. 175 is arbitrary
                if len(ref.title) > 175:
                    ref.title = ref.title[:175] + "..."

                repl = ref.refTitle()
                new_text = new_text.replace(match.group(), repl)

            # Add <references/> when needed, but ignore templates !
            if page.namespace != 10:
                if self.norefbot.lacksReferences(new_text):
                    new_text = self.norefbot.addReferences(new_text)

            new_text = self.deduplicator.process(new_text)
            old_text = page.text

            self.userPut(page, old_text, new_text, summary=self.msg,
                         ignore_save_related_errors=True,
                         ignore_server_errors=True)

            if new_text == old_text:
                continue
            else:
                editedpages += 1

            if self.getOption('limit') and editedpages >= self.getOption('limit'):
                pywikibot.output('Edited %s pages, stopping.' % self.getOption('limit'))
                return

            if self.site_stop_page and editedpages % 20 == 0:
                self.stop_page = pywikibot.Page(self.site, self.site_stop_page)
                if self.stop_page.exists():
                    pywikibot.output(color_format(
                        '{lightgreen}Checking stop page...{default}'))
                    actual_rev = self.stop_page.latest_revision_id
                    if actual_rev != self.stop_page_rev_id:
                        pywikibot.output(
                            '%s has been edited : Someone wants us to stop.'
                            % self.stop_page.title(asLink=True))
                        return


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    xmlFilename = None
    xmlStart = None
    options = {}
    generator = None

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg.startswith('-summary:'):
            options['summary'] = arg[9:]
        elif arg == '-always':
            options['always'] = True
        elif arg == '-ignorepdf':
            options['ignorepdf'] = True
        elif arg.startswith('-limit:'):
            options['limit'] = int(arg[7:])
        elif arg.startswith('-xmlstart'):
            if len(arg) == 9:
                xmlStart = pywikibot.input(
                    u'Please enter the dumped article to start with:')
            else:
                xmlStart = arg[10:]
        elif arg.startswith('-xml'):
            if len(arg) == 4:
                xmlFilename = pywikibot.input(
                    u'Please enter the XML dump\'s filename:')
            else:
                xmlFilename = arg[5:]
        else:
            genFactory.handleArg(arg)

    if xmlFilename:
        generator = XmlDumpPageGenerator(xmlFilename, xmlStart,
                                         genFactory.namespaces)
    if not generator:
        generator = genFactory.getCombinedGenerator()
    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False
    if not genFactory.nopreload:
        generator = pagegenerators.PreloadingGenerator(generator)
    generator = pagegenerators.RedirectFilterPageGenerator(generator)
    bot = ReferencesRobot(generator, **options)
    bot.run()
    return True


if __name__ == "__main__":
    main()
