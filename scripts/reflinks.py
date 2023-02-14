#!/usr/bin/env python3
"""
Fetch and add titles for bare links in references.

This bot will search for references which are only made of a link
without title (i.e. <ref>[https://www.google.fr/]</ref> or
<ref>https://www.google.fr/</ref>) and will fetch the html title from
the link to use it as the title of the wiki link in the reference, i.e.
<ref>[https://www.google.fr/search?q=test test - Google Search]</ref>

The bot checks every 20 edits a special stop page. If the page has been
edited, it stops.

As it uses it, you need to configure noreferences.py for your wiki, or it
will not work.

pdfinfo is needed for parsing pdf titles.

The following parameters are supported:

-xml:dump.xml     Should be used instead of a simple page fetching method
                  from pagegenerators.py for performance and load issues

-xmlstart         Page to start with when using an XML dump

This script is a :py:obj:`ConfigParserBot <bot.ConfigParserBot>`.
The following options can be set within a settings file which is scripts.ini
by default::

-always          Doesn't ask every time whether the bot should make the change.
                 Do it always.

-limit:n          Stops after n edits

-ignorepdf        Do not handle PDF files (handy if you use Windows and
                  can't get pdfinfo)

-summary          Use a custom edit summary. Otherwise it uses the
                  default one from translatewiki

The following generators and filters are supported:

&params;
"""
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import http.client as httplib
import itertools
import os
import re
import subprocess
import tempfile
from contextlib import suppress
from enum import IntEnum
from functools import partial
from http import HTTPStatus
from pathlib import Path
from textwrap import shorten

import pywikibot
from pywikibot import comms, config, i18n, pagegenerators, textlib
from pywikibot.backports import removeprefix
from pywikibot.bot import ConfigParserBot, ExistingPageBot, SingleSiteBot
from pywikibot.comms.http import get_charset_from_content_type
from pywikibot.exceptions import ServerError
from pywikibot.pagegenerators import (
    XMLDumpPageGenerator as _XMLDumpPageGenerator,
)
from pywikibot.textlib import replaceExcept
from pywikibot.tools.chars import string2html
from scripts import noreferences


docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

localized_msg = ('fr', 'it', 'pl')  # localized message at MediaWiki

# localized message at specific Wikipedia site
# should be moved to MediaWiki Pywikibot manual


stop_page = {
    'fr': 'Utilisateur:DumZiBoT/EditezCettePagePourMeStopper',
    'da': 'Bruger:DumZiBoT/EditThisPageToStopMe',
    'de': 'Benutzer:DumZiBoT/EditThisPageToStopMe',
    'fa': 'کاربر:Amirobot/EditThisPageToStopMe',
    'it': 'Utente:Marco27Bot/EditThisPageToStopMe',
    'ko': '사용자:GrassnBreadRefBot/EditThisPageToStopMe1',
    'he': 'User:Matanyabot/EditThisPageToStopMe',
    'hu': 'User:Damibot/EditThisPageToStopMe',
    'en': 'User:DumZiBoT/EditThisPageToStopMe',
    'pl': 'Wikipedysta:MastiBot/EditThisPageToStopMe',
    'ru': 'User:Rubinbot/EditThisPageToStopMe',
    'ur': 'صارف:Shuaib-bot/EditThisPageToStopMe',
    'zh': 'User:Sz-iwbot',
}

deadLinkTag = {
    'ar': '[%s] {{وصلة مكسورة}}',
    'fr': '[%s] {{lien mort}}',
    'da': '[%s] {{dødt link}}',
    'fa': '[%s] {{پیوند مرده}}',
    'he': '{{קישור שבור}}',
    'hi': '[%s] {{Dead link}}',
    'hu': '[%s] {{halott link}}',
    'ko': '[%s] {{죽은 바깥 고리}}',
    'es': '{{enlace roto2|%s}}',
    'it': '{{Collegamento interrotto|%s}}',
    'en': '[%s] {{dead link}}',
    'pl': '[%s] {{Martwy link}}',
    'ru': '[%s] {{Недоступная ссылка}}',
    'sr': '[%s] {{dead link}}',
    'ur': '[%s] {{مردہ ربط}}',
}


soft404 = re.compile(
    r'\D404(\D|\Z)|error|errdoc|Not.{0,3}Found|sitedown|eventlog',
    re.IGNORECASE)
# matches an URL at the index of a website
dirIndex = re.compile(
    r'\w+://[^/]+/((default|index)\.'
    r'(asp|aspx|cgi|htm|html|phtml|mpx|mspx|php|shtml|var))?',
    re.IGNORECASE)
# Extracts the domain name
domain = re.compile(r'^(\w+)://(?:www\.|)([^/]+)')

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
            |(404|page|file|information|resource).*not([ ]*be)?[ ]*
            (available|found)
            |are[ ](?:.+?[ ])?robot
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
    'ru': '.*([Сс]траница.*(не[ ]*найдена|отсутствует)|Вы.*человек).*',
}

# Regex that match bare references
linksInRef = re.compile(
    # bracketed URLs
    r'(?i)<ref(?P<name>[^>]*)>\s*\[?(?P<url>(?:http|https)://(?:'
    # unbracketed with()
    r'^\[\]\s<>"]+\([^\[\]\s<>"]+[^\[\]\s\.:;\\,<>\?"]+|'
    # unbracketed without ()
    r'[^\[\]\s<>"]+[^\[\]\s\)\.:;\\,<>\?"]+|[^\[\]\s<>"]+))'
    r'[!?,\s]*\]?\s*</ref>')

# Download this file :
# http://www.twoevils.org/files/wikipedia/404-links.txt.gz
# ( maintained by User:Dispenser )
listof404pages = '404-links.txt'

XmlDumpPageGenerator = partial(
    _XMLDumpPageGenerator, text_predicate=linksInRef.search)


class RefLink:

    """Container to handle a single bare reference."""

    def __init__(self, link, name, site=None) -> None:
        """Initializer."""
        self.name = name
        self.link = link
        self.site = site or pywikibot.Site()
        self.comment = i18n.twtranslate(self.site, 'reflinks-comment')
        self.url = re.sub('#.*', '', self.link)
        self.title = None

    def refTitle(self) -> str:
        """Return the <ref> with its new title."""
        return '<ref{r.name}>[{r.link} {r.title}<!-- {r.comment} -->]</ref>' \
               .format(r=self)

    def refLink(self) -> str:
        """No title has been found, return the unbracketed link."""
        return '<ref{r.name}>{r.link}</ref>'.format(r=self)

    def refDead(self):
        """Dead link, tag it with a {{dead link}}."""
        tag = i18n.translate(self.site, deadLinkTag)
        if not tag:
            dead_link = self.refLink()
        else:
            if '%s' in tag:
                tag %= self.link
            dead_link = f'<ref{self.name}>{tag}</ref>'
        return dead_link

    def transform(self, ispdf: bool = False) -> None:
        """Normalize the title."""
        # convert html entities
        if not ispdf:
            self.title = pywikibot.html2unicode(self.title)
        self.title = re.sub(r'-+', '-', self.title)
        # remove formatting, i.e long useless strings
        self.title = re.sub(r'[\.+\-=]{4,}', ' ', self.title)
        # remove \n and \r and unicode spaces from titles
        self.title = re.sub(r'\s', ' ', self.title)
        # remove extra whitespaces
        # remove leading and trailing ./;/,/-/_/+/ /
        self.title = re.sub(r' +', ' ', self.title.strip(r'=.;,-+_ '))

        self.avoid_uppercase()
        # avoid closing the link before the end
        self.title = self.title.replace(']', '&#93;')
        # avoid multiple } being interpreted as a template inclusion
        self.title = self.title.replace('}}', '}&#125;')
        # prevent multiple quotes being interpreted as '' or '''
        self.title = self.title.replace("''", "'&#39;")
        self.title = string2html(self.title, self.site.encoding())
        # TODO : remove HTML when both opening and closing tags are included

    def avoid_uppercase(self) -> None:
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
        if nb_upper / (nb_letter + 1) > 0.7:
            self.title = self.title.title()


class IX(IntEnum):

    """Index class for references data."""

    name = 0
    reflist = 1
    quoted = 2
    change_needed = 3


class DuplicateReferences:

    """Helper to de-duplicate references in text.

    When some references are duplicated in an article,
    name the first, and remove the content of the others
    """

    def __init__(self, site=None) -> None:
        """Initializer."""
        if not site:
            site = pywikibot.Site()

        # Match references
        self.REFS = re.compile(
            r'(?is)<ref(?P<params>[^>/]*)>(?P<content>.*?)</ref>')
        fmt = r'(?i){0}\s*=\s*(?P<quote>["\']?)\s*(?P<{0}>.+)\s*(?P=quote)'
        self.NAMES = re.compile(fmt.format('name'))
        self.GROUPS = re.compile(fmt.format('group'))
        self.autogen = i18n.twtranslate(site, 'reflinks-autogen')

    def process(self, text):
        """Process the page."""
        # keys are ref groups
        # values are a dict where :
        #   keys are ref content
        #   values are [name, [list of full ref matches],
        #               quoted, need_to_change]
        found_refs = {}
        found_ref_names = set()
        # Replace key by [value, quoted]
        named_repl = {}

        # Parse references
        for match in self.REFS.finditer(text):
            content = match['content']
            if not content.strip():
                continue

            params = match['params']
            group = self.GROUPS.search(params) or ''
            if group not in found_refs:
                found_refs[group] = {}

            groupdict = found_refs[group]
            if content in groupdict:
                v = groupdict[content]
                v[IX.reflist].append(match.group())
            else:
                v = [None, [match.group()], False, False]

            found = self.NAMES.search(params)
            if found:
                quoted = found['quote'] in ['"', "'"]
                name = found['name']

                if not v[IX.name]:
                    # First name associated with this content
                    if name not in found_ref_names:
                        # first time ever we meet this name
                        v[IX.quoted] = quoted
                        v[IX.name] = name
                    else:
                        # if has_key, means that this name is used
                        # with another content. We'll need to change it
                        v[IX.change_needed] = True
                elif v[IX.name] != name:
                    named_repl[name] = [v[IX.name], v[IX.quoted]]

                found_ref_names.add(name)
            groupdict[content] = v

        # Find used autogenerated numbers
        used_numbers = set()
        for name in found_ref_names:
            number = removeprefix(name, self.autogen)
            with suppress(ValueError):
                used_numbers.add(int(number))

        # generator to give the next free number for autogenerating names
        free_number = (str(i) for i in itertools.count(start=1)
                       if i not in used_numbers)

        # Fix references
        for groupname, references in found_refs.items():
            group = f'group="{groupname}" ' if groupname else ''

            for ref, v in references.items():
                if len(v[IX.reflist]) == 1 and not v[IX.change_needed]:
                    continue

                name = v[IX.name]
                if not name:
                    name = f'"{self.autogen}{next(free_number)}"'
                elif v[IX.quoted]:
                    name = f'"{name}"'

                named = f'<ref {group}name={name}>{ref}</ref>'
                text = text.replace(v[IX.reflist][0], named, 1)

                # make sure that the first (named ref) is not removed later
                pos = text.index(named) + len(named)
                header = text[:pos]
                end = text[pos:]

                # replace multiple identical references with repeated ref
                repeated_ref = f'<ref {group}name={name} />'
                for ref in v[IX.reflist][1:]:
                    # Don't replace inside templates (T266411)
                    end = replaceExcept(end, re.escape(ref), repeated_ref,
                                        exceptions=['template'])
                text = header + end

        # Fix references with different names
        for ref, v in named_repl.items():
            # TODO : Support ref groups
            name = v[IX.name]
            if v[IX.reflist]:
                name = f'"{name}"'

            text = re.sub(
                r'<ref name\s*=\s*(?P<quote>["\']?)\s*{}\s*(?P=quote)\s*/>'
                .format(ref),
                f'<ref name={name} />', text)
        return text


class ReferencesRobot(SingleSiteBot, ConfigParserBot, ExistingPageBot):

    """References bot.

    .. versionchanged:: 7.0
       ReferencesRobot is a ConfigParserBot
    """

    use_redirects = False

    update_options = {
        'ignorepdf': False,
        'limit': 0,  # stop after n modified pages
        'summary': '',
    }

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        self._use_fake_user_agent = config.fake_user_agent_default.get(
            'reflinks', False)
        # Check
        manual = 'mw:Manual:Pywikibot/refLinks'
        code = None
        for alt in [self.site.code] + i18n._altlang(self.site.code):
            if alt in localized_msg:
                code = alt
                break
        if code:
            manual += f'/{code}'

        if self.opt.summary:
            self.msg = self.opt.summary
        else:
            self.msg = i18n.twtranslate(self.site, 'reflinks-msg', locals())

        local = i18n.translate(self.site, badtitles)
        if local:
            bad = f'({globalbadtitles}|{local})'
        else:
            bad = globalbadtitles

        self.titleBlackList = re.compile(bad, re.I | re.S | re.X)
        self.norefbot = noreferences.NoReferencesBot(verbose=False)
        self.deduplicator = DuplicateReferences(self.site)

        self.site_stop_page = i18n.translate(self.site, stop_page)
        if self.site_stop_page:
            self.stop_page = pywikibot.Page(self.site, self.site_stop_page)
            if self.stop_page.exists():
                self.stop_page_rev_id = self.stop_page.latest_revision_id
            else:
                pywikibot.warning('The stop page {} does not exist'
                                  .format(self.stop_page.title(as_link=True)))

        # Regex to grasp content-type meta HTML tag in HTML source
        self.META_CONTENT = re.compile(
            br'(?i)<meta[^>]*(?:content\-type|charset)[^>]*>')
        # Extract html title from page
        self.TITLE = re.compile(r'(?is)(?<=<title>).*?(?=</title>)')
        # Matches content inside <script>/<style>/HTML comments
        self.NON_HTML = re.compile(
            br'(?is)<script[^>]*>.*?</script>|<style[^>]*>.*?</style>|'
            br'<!--.*?-->|<!\[CDATA\[.*?\]\]>')

        # Authorized mime types for HTML pages
        self.MIME = re.compile(
            r'application/(?:xhtml\+xml|xml)|text/(?:ht|x)ml')

    @staticmethod
    def httpError(err_num, link, pagetitleaslink) -> None:
        """Log HTTP Error."""
        pywikibot.stdout('HTTP error ({}) for {} on {}'
                         .format(err_num, link, pagetitleaslink))

    @staticmethod
    def getPDFTitle(ref, response) -> None:
        """Use pdfinfo to retrieve title from a PDF."""
        # pdfinfo is Unix-only
        pywikibot.info('Reading PDF file...')
        infile = None
        try:
            fd, infile = tempfile.mkstemp()
            urlobj = os.fdopen(fd, 'w+')
            urlobj.write(response.text)
            pdfinfo_out = subprocess.Popen([r'pdfinfo', '/dev/stdin'],
                                           stdin=urlobj,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE,
                                           shell=False).communicate()[0]
        except ValueError:
            pywikibot.info('pdfinfo value error.')
        except OSError:
            pywikibot.info('pdfinfo OS error.')
        except Exception as e:  # Ignore errors
            pywikibot.info('PDF processing error.')
            pywikibot.error(e)
        else:
            for aline in pdfinfo_out.splitlines():
                if isinstance(aline, bytes):
                    aline = aline.decode()
                if aline.lower().startswith('title'):
                    ref.title = ' '.join(aline.split()[1:])
                    if ref.title:
                        pywikibot.info('title: ' + ref.title)
                        break
            pywikibot.info('PDF done.')
        finally:
            if infile is not None:
                urlobj.close()
                os.unlink(infile)

    def setup(self):
        """Read dead links from file."""
        try:
            path = Path(listof404pages)
            self.dead_links = path.read_text(encoding='latin_1')
        except OSError:
            raise NotImplementedError(
                '404-links.txt is required for reflinks.py\n'
                'You need to download\n'
                'http://www.twoevils.org/files/wikipedia/404-links.txt.gz\n'
                'and to unzip it in the same directory')

    def skip_page(self, page):
        """Skip unwanted pages."""
        if super().skip_page(page):
            return True

        if not page.has_permission():
            pywikibot.warning("You can't edit page {page}" .format(page=page))
            return True

        return False

    def treat(self, page) -> None:
        """Process one page."""
        # Load the page's text from the wiki
        new_text = page.text
        raw_text = textlib.removeDisabledParts(new_text)
        # for each link to change
        for match in linksInRef.finditer(raw_text):

            link = match['url']
            if 'jstor.org' in link:
                # TODO: Clean URL blacklist
                continue

            ref = RefLink(link, match['name'], site=self.site)

            try:
                r = comms.http.fetch(
                    ref.url, use_fake_user_agent=self._use_fake_user_agent)

                # Try to get Content-Type from server
                content_type = r.headers.get('content-type')
                if content_type and not self.MIME.search(content_type):
                    if ref.link.lower().endswith('.pdf') \
                       and not self.opt.ignorepdf:
                        # If file has a PDF suffix
                        self.getPDFTitle(ref, r)
                    else:
                        pywikibot.info(f'<<lightyellow>>WARNING<<default>> : '
                                       f'media : {ref.link} ')

                    if not ref.title:
                        repl = ref.refLink()
                    elif not re.match('(?i) *microsoft (word|excel|visio)',
                                      ref.title):
                        ref.transform(ispdf=True)
                        repl = ref.refTitle()
                    else:
                        pywikibot.info(f'<<lightyellow>>WARNING<<default>> : '
                                       f'PDF title blacklisted : {ref.title} ')
                        repl = ref.refLink()

                    new_text = new_text.replace(match.group(), repl)
                    continue

                # Get the real url where we end (http redirects !)
                redir = r.url
                if redir != ref.link \
                   and domain.findall(redir) == domain.findall(link):
                    if soft404.search(redir) \
                       and not soft404.search(ref.link):
                        pywikibot.info(f'<<lightyellow>>WARNING<<default>> : '
                                       f'Redirect 404 : {ref.link} ')
                        continue

                    if dirIndex.fullmatch(redir) \
                       and not dirIndex.fullmatch(ref.link):
                        pywikibot.info(f'<<lightyellow>>WARNING<<default>> : '
                                       f'Redirect to root : {ref.link} ')
                        continue

                if r.status_code != HTTPStatus.OK:
                    pywikibot.stdout('HTTP error ({}) for {} on {}'
                                     .format(r.status_code, ref.url,
                                             page.title(as_link=True)))
                    # 410 Gone, indicates that the resource has been
                    # purposely removed
                    if r.status_code == HTTPStatus.GONE \
                       or (r.status_code == HTTPStatus.NOT_FOUND
                           and f'\t{ref.url}\t' in self.dead_links):
                        repl = ref.refDead()
                        new_text = new_text.replace(match.group(), repl)
                    continue

            except UnicodeError:
                # example:
                # http://www.adminet.com/jo/20010615¦/ECOC0100037D.html
                # in [[fr:Cyanure]]
                pywikibot.info(
                    f'<<lightred>>Bad link<<default>> : {ref.url} in {page}')
                continue

            except (ValueError,  # urllib3.LocationParseError derives from it
                    OSError,
                    httplib.error,
                    ServerError) as err:
                pywikibot.info(f"{err.__class__.__name__}: Can't retrieve url "
                               f'{ref.url}: {err}')
                continue

            linkedpagetext = r.content
            # remove <script>/<style>/comments/CDATA tags
            linkedpagetext = self.NON_HTML.sub(b'', linkedpagetext)

            meta_content = self.META_CONTENT.search(linkedpagetext)
            encoding = None
            if content_type:
                encoding = get_charset_from_content_type(content_type)

            if meta_content:
                tag = None
                encodings = [encoding] if encoding else []
                encodings += list(page.site.encodings())
                for enc in encodings:
                    with suppress(UnicodeDecodeError):
                        tag = meta_content.group().decode(enc)
                        break

                # Prefer the content-type from the HTTP header
                if not content_type and tag:
                    content_type = tag
                if not encoding:
                    encoding = get_charset_from_content_type(tag)

            if encoding:
                r.encoding = encoding

            if not content_type:
                pywikibot.info('No content-type found for ' + ref.link)
                continue

            if not self.MIME.search(content_type):
                pywikibot.info(f'<<lightyellow>>WARNING<<default>> : media : '
                               f'{ref.link} ')
                repl = ref.refLink()
                new_text = new_text.replace(match.group(), repl)
                continue

            # Retrieves the first non empty string inside <title> tags
            for m in self.TITLE.finditer(r.text):
                t = m.group()
                if t:
                    ref.title = t
                    ref.transform()
                    if ref.title:
                        break

            if not ref.title:
                repl = ref.refLink()
                new_text = new_text.replace(match.group(), repl)
                pywikibot.info(f'{ref.link} : No title found...')
                continue

            if self.titleBlackList.match(ref.title):
                repl = ref.refLink()
                new_text = new_text.replace(match.group(), repl)
                pywikibot.info(f'<<lightred>>WARNING<<default>> {ref.link} : '
                               f'Blacklisted title ({ref.title})')
                continue

            # Truncate long titles. 175 is arbitrary
            ref.title = shorten(ref.title, width=178, placeholder='...')

            repl = ref.refTitle()
            new_text = new_text.replace(match.group(), repl)

        # Add <references/> when needed, but ignore templates !
        if page.namespace != 10 and self.norefbot.lacksReferences(new_text):
            new_text = self.norefbot.addReferences(new_text)

        new_text = self.deduplicator.process(new_text)
        old_text = page.text

        if old_text == new_text:
            return

        self.userPut(page, old_text, new_text, summary=self.msg,
                     ignore_save_related_errors=True,
                     ignore_server_errors=True)

        if not self.counter['write']:
            return

        if self.opt.limit and self.counter['write'] >= self.opt.limit:
            pywikibot.info(f'Edited {self.opt.limit} pages, stopping.')
            self.generator.close()

        if self.site_stop_page and self.counter['write'] % 20 == 0:
            self.stop_page = pywikibot.Page(self.site, self.site_stop_page)
            if self.stop_page.exists():
                pywikibot.info('<<lightgreen>>Checking stop page...')
                actual_rev = self.stop_page.latest_revision_id
                if actual_rev != self.stop_page_rev_id:
                    pywikibot.info(f'{self.stop_page} has been edited: '
                                   f'Someone wants us to stop.')
                    self.generator.close()


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    xml_filename = None
    xml_start = None
    options = {}
    generator = None

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        opt, _, value = arg.partition(':')
        if opt in ('-summary', '-limit'):
            options[opt[1:]] = value
        elif opt in ('-always', '-ignorepdf'):
            options[opt[1:]] = True
        elif opt == '-xmlstart':
            xml_start = value or pywikibot.input(
                'Please enter the dumped article to start with:')
        elif opt == '-xml':
            xml_filename = value or pywikibot.input(
                "Please enter the XML dump's filename:")
        else:
            gen_factory.handle_arg(arg)

    if xml_filename:
        generator = XmlDumpPageGenerator(xml_filename, xml_start,
                                         gen_factory.namespaces)
    if not generator:
        generator = gen_factory.getCombinedGenerator()
    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return
    if not gen_factory.nopreload:
        generator = pagegenerators.PreloadingGenerator(generator)
    generator = pagegenerators.RedirectFilterPageGenerator(generator)
    bot = ReferencesRobot(generator=generator, **options)
    bot.run()


if __name__ == '__main__':
    main()
