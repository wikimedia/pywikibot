# -*- coding: utf-8  -*-
"""
This module can do slight modifications to a wiki page source code such that
the code looks cleaner. The changes are not supposed to change the look of the
rendered wiki page.

The following parameters are supported:

&params;

-always           Don't prompt you for each replacement. Warning (see below)
                  has not to be confirmed. ATTENTION: Use this with care!

-summary:XYZ      Set the summary message text for the edit to XYZ, bypassing
                  the predefined message texts with original and replacements
                  inserted.

All other parameters will be regarded as part of the title of a single page,
and the bot will only work on that single page.

&warning;

For regular use, it is recommended to put this line into your user-config.py:

    cosmetic_changes = True

There is another config variable: You can set

    cosmetic_changes_mylang_only = False

if you're running a bot on multiple sites and want to do cosmetic changes on
all of them, but be careful if you do.
"""
__version__ = '$Id$'
import pywikibot
import isbn
from pywikibot import pagegenerators, i18n
import sys
import re

warning = """ATTENTION: You can run this script as a stand-alone for testing purposes.
However, the changes are that are made are only minor, and other users
might get angry if you fill the version histories and watchlists with such
irrelevant changes."""

docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
    '&warning;': warning,
}

# Summary message when using this module as a stand-alone script
msg_standalone = 'cosmetic_changes-standalone'

# Summary message  that will be appended to the normal message when
# cosmetic changes are made on the fly
msg_append = 'cosmetic_changes-append'

nn_iw_msg = u'<!--interwiki (no, sv, da first; then other languages alphabetically by name)-->'

# This is from interwiki.py;
# move it to family file and implement global instances
moved_links = {
    'ca' : (u'ús de la plantilla', u'/ús'),
    'cs' : (u'dokumentace',   u'/doc'),
    'de' : (u'dokumentation', u'/Meta'),
    'en' : ([u'documentation',
             u'template documentation',
             u'template doc',
             u'doc',
             u'documentation, template'], u'/doc'),
    'es' : ([u'documentación', u'documentación de plantilla'], u'/doc'),
    'fa' : ([u'documentation',u'توضیحات',u'توضیحات الگو',u'doc'], u'/توضیحات'),
    'fr' : (u'/documentation', u'/Documentation'),
    'hu' : (u'sablondokumentáció', u'/doc'),
    'id' : (u'template doc',  u'/doc'),
    'ja' : (u'documentation', u'/doc'),
    'ka' : (u'თარგის ინფო',   u'/ინფო'),
    'ko' : (u'documentation', u'/설명문서'),
    'ms' : (u'documentation', u'/doc'),
    'pl' : (u'dokumentacja',  u'/opis'),
    'pt' : ([u'documentação', u'/doc'],  u'/doc'),
    'ro' : (u'documentaţie',  u'/doc'),
    'ru' : (u'doc',           u'/doc'),
    'sv' : (u'dokumentation', u'/dok'),
    'vi' : (u'documentation', u'/doc'),
    'zh' : ([u'documentation', u'doc'], u'/doc'),
}

# Template which should be replaced or removed.
# Use a list with two entries. The first entry will be replaced by the second.
# Examples:
# For removing {{Foo}}, the list must be:
#           (u'Foo', None),
#
# The following also works:
#           (u'Foo', ''),
#
# For replacing {{Foo}} with {{Bar}} the list must be:
#           (u'Foo', u'Bar'),
#
# This also removes all template parameters of {{Foo}}
# For replacing {{Foo}} with {{Bar}} but keep the template
# parameters in its original order, please use:
#           (u'Foo', u'Bar\g<parameters>'),

deprecatedTemplates = {
    'wikipedia': {
        'de': [
            (u'Belege', u'Belege fehlen\g<parameters>'),
            (u'Quelle', u'Belege fehlen\g<parameters>'),
            (u'Quellen', u'Belege fehlen\g<parameters>'),
        ],
    }
}

class CosmeticChangesToolkit:
    def __init__(self, site, debug=False, redirect=False, namespace=None, pageTitle=None):
        self.site = site
        self.debug = debug
        self.redirect = redirect
        self.namespace = namespace
        self.template = (self.namespace == 10)
        self.talkpage = self.namespace >= 0 and self.namespace % 2 == 1
        self.title = pageTitle

    def change(self, text):
        """
        Given a wiki source code text, return the cleaned up version.
        """
        oldText = text
        if self.site.sitename()== u'commons:commons' and self.namespace == 6:
            text = self.commonsfiledesc(text)
        text = self.fixSelfInterwiki(text)
        text = self.standardizePageFooter(text)
        text = self.cleanUpLinks(text)
        text = self.cleanUpSectionHeaders(text)
        text = self.putSpacesInLists(text)
        text = self.translateAndCapitalizeNamespaces(text)
        text = self.replaceDeprecatedTemplates(text)
        text = self.resolveHtmlEntities(text)
        text = self.validXhtml(text)
        text = self.removeUselessSpaces(text)
        text = self.removeNonBreakingSpaceBeforePercent(text)
        text = self.fixSyntaxSave(text)
        text = self.fixHtml(text)
        text = self.fixStyle(text)
        text = self.fixTypo(text)
        text = self.fixArabicLetters(text)
        try:
            text = isbn.hyphenateIsbnNumbers(text)
        except isbn.InvalidIsbnException, error:
            pass
        if self.debug:
            pywikibot.showDiff(oldText, text)
        return text

    def fixSelfInterwiki(self, text):
        """
        Interwiki links to the site itself are displayed like local links.
        Remove their language code prefix.
        """
        if not self.talkpage and pywikibot.calledModuleName() <> 'interwiki':
            interwikiR = re.compile(r'\[\[%s\s?:([^\[\]\n]*)\]\]' % self.site.lang)
            text = interwikiR.sub(r'[[\1]]', text)
        return text

    def standardizePageFooter(self, text):
        """
        Makes sure that categories are put to the correct position, but
        does not sort them.
        """
        # The PyWikipediaBot is no longer allowed to touch categories on the German Wikipedia. See http://de.wikipedia.org/wiki/Hilfe_Diskussion:Personendaten/Archiv/bis_2006#Position_der_Personendaten_am_.22Artikelende.22
        if self.site != pywikibot.getSite('de', 'wikipedia') and not self.template:
            categories = pywikibot.getCategoryLinks(text, site = self.site)
            text = pywikibot.replaceCategoryLinks(text, categories, site = self.site)
        return text

    def translateAndCapitalizeNamespaces(self, text):
        """
        Makes sure that localized namespace names are used.
        """
        # arz uses english stylish codes
        if self.site.sitename() == 'wikipedia:arz':
            return text
        family = self.site.family
        # wiki links aren't parsed here.
        exceptions = ['nowiki', 'comment', 'math', 'pre']

        for nsNumber in family.namespaces:
            if not family.isDefinedNSLanguage(nsNumber, self.site.lang):
                # Skip undefined namespaces
                continue
            namespaces = list(family.namespace(self.site.lang, nsNumber, all=True))
            thisNs = namespaces.pop(0)
            if nsNumber == 6 and family.name == 'wikipedia' and \
               self.site.lang in ('en', 'fr'):
                # do not change "Image" on en-wiki and fr-wiki
                for image in [u'Image', u'image']:
                    if image in namespaces:
                        namespaces.remove(image)
            # skip main (article) namespace
            if thisNs and namespaces:
                text = pywikibot.replaceExcept(text, r'\[\[\s*(' + '|'.join(namespaces) + ') *:(?P<nameAndLabel>.*?)\]\]', r'[[' + thisNs + ':\g<nameAndLabel>]]', exceptions)
        return text

    def cleanUpLinks(self, text):
        # helper function which works on one link and either returns it
        # unmodified, or returns a replacement.
        def handleOneLink(match):
            titleWithSection = match.group('titleWithSection')
            label = match.group('label')
            trailingChars = match.group('linktrail')
            newline = match.group('newline')

            if not self.site.isInterwikiLink(titleWithSection):
                # The link looks like this:
                # [[page_title|link_text]]trailing_chars
                # We only work on namespace 0 because pipes and linktrails work
                # differently for images and categories.
                page = pywikibot.Page(pywikibot.Link(titleWithSection, self.site))
                if page.namespace() == 0:
                    # Replace underlines by spaces, also multiple underlines
                    titleWithSection = re.sub('_+', ' ', titleWithSection)
                    # Remove double spaces
                    titleWithSection = re.sub('  +', ' ', titleWithSection)
                    # Remove unnecessary leading spaces from title,
                    # but remember if we did this because we eventually want
                    # to re-add it outside of the link later.
                    titleLength = len(titleWithSection)
                    titleWithSection = titleWithSection.lstrip()
                    hadLeadingSpaces = (len(titleWithSection) != titleLength)
                    hadTrailingSpaces = False
                    # Remove unnecessary trailing spaces from title,
                    # but remember if we did this because it may affect
                    # the linktrail and because we eventually want to
                    # re-add it outside of the link later.
                    if not trailingChars:
                        titleLength = len(titleWithSection)
                        titleWithSection = titleWithSection.rstrip()
                        hadTrailingSpaces = (len(titleWithSection) != titleLength)

                    # Convert URL-encoded characters to unicode
                    titleWithSection = pywikibot.url2unicode(titleWithSection, site = self.site)

                    if titleWithSection == '':
                        # just skip empty links.
                        return match.group()

                    # Remove unnecessary initial and final spaces from label.
                    # Please note that some editors prefer spaces around pipes. (See [[en:Wikipedia:Semi-bots]]). We remove them anyway.
                    if label is not None:
                        # Remove unnecessary leading spaces from label,
                        # but remember if we did this because we want
                        # to re-add it outside of the link later.
                        labelLength = len(label)
                        label = label.lstrip()
                        hadLeadingSpaces = (len(label) != labelLength)
                        # Remove unnecessary trailing spaces from label,
                        # but remember if we did this because it affects
                        # the linktrail.
                        if not trailingChars:
                            labelLength = len(label)
                            label = label.rstrip()
                            hadTrailingSpaces = (len(label) != labelLength)
                    else:
                        label = titleWithSection
                    if trailingChars:
                        label += trailingChars

                    if titleWithSection == label or titleWithSection[0].lower() + titleWithSection[1:] == label:
                        newLink = "[[%s]]" % label
                    # Check if we can create a link with trailing characters instead of a pipelink
                    elif len(titleWithSection) <= len(label) and label[:len(titleWithSection)] == titleWithSection and re.sub(trailR, '', label[len(titleWithSection):]) == '':
                        newLink = "[[%s]]%s" % (label[:len(titleWithSection)], label[len(titleWithSection):])
                    else:
                        # Try to capitalize the first letter of the title.
                        # Maybe this feature is not useful for languages that
                        # don't capitalize nouns...
                        #if not self.site.nocapitalize:
                        if self.site.sitename() == 'wikipedia:de':
                            titleWithSection = titleWithSection[0].upper() + titleWithSection[1:]
                        newLink = "[[%s|%s]]" % (titleWithSection, label)
                    # re-add spaces that were pulled out of the link.
                    # Examples:
                    #   text[[ title ]]text        -> text [[title]] text
                    #   text[[ title | name ]]text -> text [[title|name]] text
                    #   text[[ title |name]]text   -> text[[title|name]]text
                    #   text[[title| name]]text    -> text [[title|name]]text
                    if hadLeadingSpaces and not newline:
                        newLink = ' ' + newLink
                    if hadTrailingSpaces:
                        newLink = newLink + ' '
                    if newline:
                        newLink = newline + newLink
                    return newLink
            # don't change anything
            return match.group()

        trailR = re.compile(self.site.linktrail())
        # The regular expression which finds links. Results consist of four groups:
        # group title is the target page title, that is, everything before | or ].
        # group section is the page section. It'll include the # to make life easier for us.
        # group label is the alternative link title, that's everything between | and ].
        # group linktrail is the link trail, that's letters after ]] which are part of the word.
        # note that the definition of 'letter' varies from language to language.
        linkR = re.compile(r'(?P<newline>[\n]*)\[\[(?P<titleWithSection>[^\]\|]+)(\|(?P<label>[^\]\|]*))?\]\](?P<linktrail>' + self.site.linktrail() + ')')

        text = pywikibot.replaceExcept(text, linkR, handleOneLink, ['comment', 'math', 'nowiki', 'pre', 'startspace'])
        return text

    def resolveHtmlEntities(self, text):
        ignore = [
             38,     # Ampersand (&amp;)
             39,     # Bugzilla 24093
             60,     # Less than (&lt;)
             62,     # Great than (&gt;)
             91,     # Opening bracket - sometimes used intentionally inside links
             93,     # Closing bracket - sometimes used intentionally inside links
            124,     # Vertical bar (??) - used intentionally in navigation bar templates on de:
            160,     # Non-breaking space (&nbsp;) - not supported by Firefox textareas
            173,     # Soft-hypen (&shy;) - enable editing
        ]
        # ignore ' see http://eo.wikipedia.org/w/index.php?title=Liberec&diff=next&oldid=2320801
        #if self.site.lang == 'eo':
        #    ignore += [39]
        text = pywikibot.html2unicode(text, ignore = ignore)
        return text

    def validXhtml(self, text):
        text = pywikibot.replaceExcept(text, r'(?i)<br[ /]*>', r'<br />', ['comment', 'math', 'nowiki', 'pre'])
        return text

    def removeUselessSpaces(self, text):
        result = []
        multipleSpacesR = re.compile('  +')
        spaceAtLineEndR = re.compile(' $')

        exceptions = ['comment', 'math', 'nowiki', 'pre', 'startspace', 'table', 'template']
        text = pywikibot.replaceExcept(text, multipleSpacesR, ' ', exceptions)
        text = pywikibot.replaceExcept(text, spaceAtLineEndR, '', exceptions)

        return text

    def removeNonBreakingSpaceBeforePercent(self, text):
        '''
        Newer MediaWiki versions automatically place a non-breaking space in
        front of a percent sign, so it is no longer required to place it
        manually.
        '''
        text = pywikibot.replaceExcept(text, r'(\d)&nbsp;%', r'\1 %', ['timeline'])
        return text

    def cleanUpSectionHeaders(self, text):
        """
        For better readability of section header source code, puts a space
        between the equal signs and the title.
        Example: ==Section title== becomes == Section title ==

        NOTE: This space is recommended in the syntax help on the English and
        German Wikipedia. It might be that it is not wanted on other wikis.
        If there are any complaints, please file a bug report.
        """
        for level in range(1, 7):
            equals = '=' * level
            text = pywikibot.replaceExcept(text, r'\n' + equals + ' *(?P<title>[^=]+?) *' + equals + ' *\r\n', '\n' + equals + ' \g<title> ' + equals + '\r\n', ['comment', 'math', 'nowiki', 'pre'])
        return text

    def putSpacesInLists(self, text):
        """
        For better readability of bullet list and enumeration wiki source code,
        puts a space between the * or # and the text.

        NOTE: This space is recommended in the syntax help on the English,
        German, and French Wikipedia. It might be that it is not wanted on other
        wikis. If there are any complaints, please file a bug report.
        """
        exceptions = ['comment', 'math', 'nowiki', 'pre', 'source', 'timeline']
        if not (self.redirect or self.template) and \
           pywikibot.calledModuleName() != 'capitalize_redirects':
            text = pywikibot.replaceExcept(
                text,
                r'(?m)^(?P<bullet>[:;]*(\*+|#+)[:;\*#]*)(?P<char>[^\s\*#:;].+?)', '\g<bullet> \g<char>',
                exceptions)
        return text

    def replaceDeprecatedTemplates(self, text):
        exceptions = ['comment', 'math', 'nowiki', 'pre']
        if self.site.family.name in deprecatedTemplates and self.site.lang in deprecatedTemplates[self.site.family.name]:
            for template in deprecatedTemplates[self.site.family.name][self.site.lang]:
                old = template[0]
                new = template[1]
                if new == None:
                    new = ''
                else:
                    new = '{{'+new+'}}'
                if not self.site.nocapitalize:
                    old = '[' + old[0].upper() + old[0].lower() + ']' + old[1:]
                text = pywikibot.replaceExcept(text, r'\{\{([mM][sS][gG]:)?' + old + '(?P<parameters>\|[^}]+|)}}', new, exceptions)
        return text

    #from fixes.py
    def fixSyntaxSave(self, text):
        exceptions = ['nowiki', 'comment', 'math', 'pre', 'source', 'startspace']
        # external link in double brackets
        text = pywikibot.replaceExcept(text, r'\[\[(?P<url>https?://[^\]]+?)\]\]', r'[\g<url>]', exceptions)
        # external link starting with double bracket
        text = pywikibot.replaceExcept(text, r'\[\[(?P<url>https?://.+?)\]', r'[\g<url>]', exceptions)
        # external link and description separated by a dash, with
        # whitespace in front of the dash, so that it is clear that
        # the dash is not a legitimate part of the URL.
        text = pywikibot.replaceExcept(text, r'\[(?P<url>https?://[^\|\] \r\n]+?) +\| *(?P<label>[^\|\]]+?)\]', r'[\g<url> \g<label>]', exceptions)
        # dash in external link, where the correct end of the URL can
        # be detected from the file extension. It is very unlikely that
        # this will cause mistakes.
        text = pywikibot.replaceExcept(text, r'\[(?P<url>https?://[^\|\] ]+?(\.pdf|\.html|\.htm|\.php|\.asp|\.aspx|\.jsp)) *\| *(?P<label>[^\|\]]+?)\]', r'[\g<url> \g<label>]', exceptions)
        return text

    def fixHtml(self, text):
        # Everything case-insensitive (?i)
        # Keep in mind that MediaWiki automatically converts <br> to <br />
        exceptions = ['nowiki', 'comment', 'math', 'pre', 'source', 'startspace']
        text = pywikibot.replaceExcept(text, r'(?i)<b>(.*?)</b>', r"'''\1'''" , exceptions)
        text = pywikibot.replaceExcept(text, r'(?i)<strong>(.*?)</strong>', r"'''\1'''" , exceptions)
        text = pywikibot.replaceExcept(text, r'(?i)<i>(.*?)</i>', r"''\1''" , exceptions)
        text = pywikibot.replaceExcept(text, r'(?i)<em>(.*?)</em>', r"''\1''" , exceptions)
        # horizontal line without attributes in a single line
        text = pywikibot.replaceExcept(text, r'(?i)([\r\n])<hr[ /]*>([\r\n])', r'\1----\2', exceptions)
        # horizontal line with attributes; can't be done with wiki syntax
        # so we only make it XHTML compliant
        text = pywikibot.replaceExcept(text, r'(?i)<hr ([^>/]+?)>', r'<hr \1 />', exceptions)
        # a header where only spaces are in the same line
        for level in range(1, 7):
            equals = '\\1%s \\2 %s\\3' % ("="*level, "="*level)
            text = pywikibot.replaceExcept(text,
                                           r'(?i)([\r\n]) *<h%d> *([^<]+?) *</h%d> *([\r\n])'%(level, level),
                                           r'%s'%equals, exceptions)
        #remove empty <ref/>-tag
        text = pywikibot.replaceExcept(text, r'(?i)<ref\s*/>', r'', exceptions)
        # TODO: maybe we can make the bot replace <p> tags with \r\n's.
        return text

    def fixStyle(self, text):
        exceptions = ['nowiki', 'comment', 'math', 'pre', 'source', 'startspace']
        # convert prettytable to wikitable class
        if self.site.language in ('de', 'en'):
           text = pywikibot.replaceExcept(text, ur'(class="[^"]*)prettytable([^"]*")', ur'\1wikitable\2', exceptions)
        return text

    def fixTypo(self, text):
        exceptions = ['nowiki', 'comment', 'math', 'pre', 'source', 'startspace', 'gallery', 'hyperlink', 'interwiki', 'link']
        # change <number> ccm -> <number> cm³
        text = pywikibot.replaceExcept(text, ur'(\d)\s*&nbsp;ccm', ur'\1&nbsp;cm³', exceptions)
        text = pywikibot.replaceExcept(text, ur'(\d)\s*ccm', ur'\1&nbsp;cm³', exceptions)
        # Solve wrong Nº sign with °C or °F
        # additional exception requested on fr-wiki for this stuff
        pattern = re.compile(u'«.*?»', re.UNICODE)
        exceptions.append(pattern)
        text = pywikibot.replaceExcept(text, ur'(\d)\s*&nbsp;[º°]([CF])', ur'\1&nbsp;°\2', exceptions)
        text = pywikibot.replaceExcept(text, ur'(\d)\s*[º°]([CF])', ur'\1&nbsp;°\2', exceptions)
        text = pywikibot.replaceExcept(text, ur'º([CF])', ur'°\1', exceptions)
        return text

    def fixArabicLetters(self, text):
        if self.site.lang=='ckb' or self.site.lang=='fa':
            exceptions = [
                'gallery',
                'hyperlink',
                'interwiki',
                # but changes letters inside wikilinks
                #'link',
                'math',
                'pre',
                'template',
                'timeline',
                'ref',
                'source',
                'startspace',
                'inputbox',
            ]
            # do not change inside file links
            namespaces = list(self.site.namespace(6, all = True))
            pattern = re.compile(u'\[\[(' + '|'.join(namespaces) + '):.+?\..+?\]\]',
                                 re.UNICODE)
            exceptions.append(pattern)
            text = pywikibot.replaceExcept(text, u',', u'،', exceptions)
            if self.site.lang=='ckb':
                text = pywikibot.replaceExcept(text,
                                               ur'ه([.،_<\]\s])',
                                               ur'ە\1', exceptions)
                text = pywikibot.replaceExcept(text, u'ه‌', u'ە', exceptions)
                text = pywikibot.replaceExcept(text, u'ه', u'ھ', exceptions)
            text = pywikibot.replaceExcept(text, u'ك', u'ک', exceptions)
            text = pywikibot.replaceExcept(text, ur'[ىي]', u'ی', exceptions)
            # replace persian digits
            for i in range(0,10):
                if self.site.lang=='ckb':
                    text = pywikibot.replaceExcept(text,
                                                   u'۰۱۲۳۴۵۶۷۸۹'[i],
                                                   u'٠١٢٣٤٥٦٧٨٩'[i], exceptions)
                else:
                    text = pywikibot.replaceExcept(text,
                                                   u'٠١٢٣٤٥٦٧٨٩'[i],
                                                   u'۰۱۲۳۴۵۶۷۸۹'[i], exceptions)
            # do not change digits in class, style and table params
            pattern = re.compile(u'=".*?"', re.UNICODE)
            exceptions.append(pattern)
            # do not change digits inside html-tags
            pattern = re.compile(u'<[/]*?[^</]+?[/]*?>', re.UNICODE)
            exceptions.append(pattern)
            exceptions.append('table') #exclude tables for now
            for i in range(0,10):
                if self.site.lang=='ckb':
                    text = pywikibot.replaceExcept(text, str(i),
                                                   u'٠١٢٣٤٥٦٧٨٩'[i], exceptions)
                else:
                    text = pywikibot.replaceExcept(text, str(i),
                                                   u'۰۱۲۳۴۵۶۷۸۹'[i], exceptions)
        return text

    # Retrieved from "http://commons.wikimedia.org/wiki/Commons:Tools/pywiki_file_description_cleanup"
    def commonsfiledesc(self, text):
        # section headers to {{int:}} versions
        exceptions = ['comment', 'includeonly', 'math', 'noinclude', 'nowiki',
                      'pre', 'source', 'ref', 'timeline']
        text = pywikibot.replaceExcept(text,
                                       r"([\r\n]|^)\=\= *Summary *\=\=",
                                       r"\1== {{int:filedesc}} ==",
                                       exceptions, True)
        text = pywikibot.replaceExcept(
            text,
            r"([\r\n])\=\= *\[\[Commons:Copyright tags\|Licensing\]\]: *\=\=",
            r"\1== {{int:license}} ==", exceptions, True)
        text = pywikibot.replaceExcept(
            text,
            r"([\r\n])\=\= *(Licensing|License information|{{int:license-header}}) *\=\=",
            r"\1== {{int:license}} ==", exceptions, True)

        # frequent field values to {{int:}} versions
        text = pywikibot.replaceExcept(
            text,
            r'([\r\n]\|[Ss]ource *\= *)(?:[Oo]wn work by uploader|[Oo]wn work|[Ee]igene [Aa]rbeit) *([\r\n])',
            r'\1{{own}}\2', exceptions, True)
        text = pywikibot.replaceExcept(
            text,
            r'(\| *Permission *\=) *(?:[Ss]ee below|[Ss]iehe unten) *([\r\n])',
            r'\1\2', exceptions, True)

        # added to transwikied pages
        text = pywikibot.replaceExcept(text, r'__NOTOC__', '', exceptions, True)

        # tracker element for js upload form
        text = pywikibot.replaceExcept(
            text,
            r'<!-- *{{ImageUpload\|(?:full|basic)}} *-->',
            '', exceptions[1:], True)
        text = pywikibot.replaceExcept(text, r'{{ImageUpload\|(?:basic|full)}}',
                                       '', exceptions, True)

        # duplicated section headers
        text = pywikibot.replaceExcept(
            text,
            r'([\r\n]|^)\=\= *{{int:filedesc}} *\=\=(?:[\r\n ]*)\=\= *{{int:filedesc}} *\=\=',
            r'\1== {{int:filedesc}} ==', exceptions, True)
        text = pywikibot.replaceExcept(
            text,
            r'([\r\n]|^)\=\= *{{int:license}} *\=\=(?:[\r\n ]*)\=\= *{{int:license}} *\=\=',
            r'\1== {{int:license}} ==', exceptions, True)
        return text

class CosmeticChangesBot:
    def __init__(self, generator, acceptall = False,
                 comment=u'Robot: Cosmetic changes'):
        self.generator = generator
        self.acceptall = acceptall
        self.comment = comment
        self.done = False

    def treat(self, page):
        try:
            # Show the title of the page we're working on.
            # Highlight the title in purple.
            pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                             % page.title())
            ccToolkit = CosmeticChangesToolkit(page.site, debug=True,
                                               namespace=page.namespace(),
                                               pageTitle=page.title())
            changedText = ccToolkit.change(page.get())
            if changedText.strip() != page.get().strip():
                if not self.acceptall:
                    choice = pywikibot.inputChoice(
                        u'Do you want to accept these changes?',
                        ['Yes', 'No', 'All', 'Quit'], ['y', 'N', 'a', 'q'], 'N')
                    if choice == 'a':
                        self.acceptall = True
                    elif choice == 'q':
                        self.done = True
                        return
                if self.acceptall or choice == 'y':
                    page.put(changedText, comment=self.comment)
            else:
                pywikibot.output('No changes were necessary in %s'
                                 % page.title())
        except pywikibot.NoPage:
            pywikibot.output("Page %s does not exist?!"
                             % page.title(asLink=True))
        except pywikibot.IsRedirectPage:
            pywikibot.output("Page %s is a redirect; skipping."
                             % page.title(asLink=True))
        except pywikibot.LockedPage:
            pywikibot.output("Page %s is locked?!" % page.title(asLink=True))
        except pywikibot.EditConflict:
            pywikibot.output("An edit conflict has occured at %s."
                             % page.title(asLink=True))

    def run(self):
        try:
            for page in self.generator:
                if self.done: break
                self.treat(page)
        except KeyboardInterrupt:
            raise
            #pywikibot.output('\nQuitting program...')

def main():
    #page generator
    gen = None
    pageTitle = []
    editSummary = ''
    answer = 'y'
    always = False
    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()

    for arg in pywikibot.handleArgs():
        if arg.startswith('-summary:'):
            editSummary = arg[len('-summary:'):]
        elif arg == '-always':
            always = True
        elif not genFactory.handleArg(arg):
            pageTitle.append(arg)

    if editSummary == '':
        # Load default summary message.
        editSummary = i18n.twtranslate(pywikibot.getSite(), msg_standalone)
    if pageTitle:
        site = pywikibot.getSite()
        gen = iter([pywikibot.Page(pywikibot.Link(t, site)) for t in pageTitle])
    if not gen:
        gen = genFactory.getCombinedGenerator()
    if not gen:
        pywikibot.showHelp()
    else:
        if not always:
            answer = pywikibot.inputChoice(
                warning + '\nDo you really want to continue?',
                ['yes', 'no'], ['y', 'N'], 'N')
        if answer == 'y':
            preloadingGen = pagegenerators.PreloadingGenerator(gen)
            bot = CosmeticChangesBot(preloadingGen, acceptall=always,
                                     comment=editSummary)
            bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
