#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This module can do slight modifications to tidy a wiki page's source code.

The changes are not supposed to change the look of the rendered wiki page.

If you wish to run this as an stand-alone script, use scripts/cosmetic_changes.py

For regular use, it is recommended to put this line into your user-config.py:

    cosmetic_changes = True

You may enable cosmetic changes for additional languages by adding the
dictionary cosmetic_changes_enable to your user-config.py. It should contain
a tuple of languages for each site where you wish to enable in addition to
your own langlanguage if cosmetic_changes_mylang_only is True (see below).
Please set your dictionary by adding such lines to your user-config.py:

    cosmetic_changes_enable['wikipedia'] = ('de', 'en', 'fr')

There is another config variable: You can set

    cosmetic_changes_mylang_only = False

if you're running a bot on multiple sites and want to do cosmetic changes on
all of them, but be careful if you do.

You may disable cosmetic changes by adding the all unwanted languages to the
dictionary cosmetic_changes_disable in your user-config.py. It should contain
a tuple of languages for each site where you wish to disable cosmetic changes.
You may use it with cosmetic_changes_mylang_only is False, but you can also
disable your own language. This also overrides the settings in the dictionary
cosmetic_changes_enable. Please set this dictionary by adding such lines to
your user-config.py:

    cosmetic_changes_disable['wikipedia'] = ('de', 'en', 'fr')

You may disable cosmetic changes for a given script by appending the all
unwanted scripts to the list cosmetic_changes_deny_script in your
user-config.py. By default it contains cosmetic_changes.py itself and touch.py.
This overrides all other enabling settings for cosmetic changes. Please modify
the given list by adding such lines to your user-config.py:

    cosmetic_changes_deny_script.append('your_script_name_1')

or by adding a list to the given one:

    cosmetic_changes_deny_script += ['your_script_name_1', 'your_script_name_2']
"""
#
# (C) xqt, 2009-2016
# (C) Pywikibot team, 2006-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import re

from warnings import warn

try:
    import stdnum.isbn as stdnum_isbn
except ImportError:
    stdnum_isbn = None

import pywikibot

from pywikibot import config, textlib
from pywikibot.textlib import _MultiTemplateMatchBuilder, FILE_LINK_REGEX
from pywikibot.tools import deprecated_args, first_lower, first_upper
from pywikibot.tools import MediaWikiVersion


# This is from interwiki.py;
# move it to family file and implement global instances
moved_links = {
    'ca': (u'ús de la plantilla', u'/ús'),
    'cs': (u'dokumentace', u'/doc'),
    'de': (u'dokumentation', u'/Meta'),
    'en': ([u'documentation',
            u'template documentation',
            u'template doc',
            u'doc',
            u'documentation, template'], u'/doc'),
    'es': ([u'documentación', u'documentación de plantilla'], u'/doc'),
    'fa': ([u'documentation', u'توضیحات', u'توضیحات الگو',
            u'doc'], u'/توضیحات'),
    'fr': (u'/documentation', u'/Documentation'),
    'hu': (u'sablondokumentáció', u'/doc'),
    'id': (u'template doc', u'/doc'),
    'ja': (u'documentation', u'/doc'),
    'ka': (u'თარგის ინფო', u'/ინფო'),
    'ko': (u'documentation', u'/설명문서'),
    'ms': (u'documentation', u'/doc'),
    'pl': (u'dokumentacja', u'/opis'),
    'pt': ([u'documentação', u'/doc'], u'/doc'),
    'ro': (u'documentaţie', u'/doc'),
    'ru': (u'doc', u'/doc'),
    'sv': (u'dokumentation', u'/dok'),
    'vi': (u'documentation', u'/doc'),
    'zh': ([u'documentation', u'doc'], u'/doc'),
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
            (u'Belege', u'Belege fehlen\\g<parameters>'),
            (u'Quelle', u'Belege fehlen\\g<parameters>'),
            (u'Quellen', u'Belege fehlen\\g<parameters>'),
            (u'Quellen fehlen', u'Belege fehlen\\g<parameters>'),
        ],
    }
}

CANCEL_ALL = False
CANCEL_PAGE = 1
CANCEL_METHOD = 2
CANCEL_MATCH = 3


def _format_isbn_match(match, strict=True):
    """Helper function to validate and format a single matched ISBN."""
    scripts_isbn = None

    if not stdnum_isbn:
        # For backwards compatibility, if stdnum.isbn is not available
        # attempt loading scripts.isbn as an alternative implementation.
        try:
            import scripts.isbn as scripts_isbn
        except ImportError:
            raise NotImplementedError(
                'ISBN functionality not available. Install stdnum package.')

        warn('package stdnum.isbn not found; using scripts.isbn',
             ImportWarning)

    isbn = match.group('code')
    if stdnum_isbn:
        try:
            stdnum_isbn.validate(isbn)
        except stdnum_isbn.ValidationError as e:
            if strict:
                raise
            pywikibot.log('ISBN "%s" validation error: %s' % (isbn, e))
            return isbn

        return stdnum_isbn.format(isbn)
    else:
        try:
            scripts_isbn.is_valid(isbn)
        except scripts_isbn.InvalidIsbnException as e:
            if strict:
                raise
            pywikibot.log('ISBN "%s" validation error: %s' % (isbn, e))
            return isbn

        isbn = scripts_isbn.getIsbn(isbn)
        try:
            isbn.format()
        except scripts_isbn.InvalidIsbnException as e:
            if strict:
                raise
            pywikibot.log('ISBN "%s" validation error: %s' % (isbn, e))
        return isbn.code


def _reformat_ISBNs(text, strict=True):
    """Helper function to normalise ISBNs in text.

    @raises Exception: Invalid ISBN encountered when strict enabled
    """
    return textlib.reformat_ISBNs(
        text, lambda match: _format_isbn_match(match, strict=strict))


class CosmeticChangesToolkit(object):

    """Cosmetic changes toolkit."""

    @deprecated_args(debug='diff', redirect=None)
    def __init__(self, site, diff=False, namespace=None, pageTitle=None,
                 ignore=CANCEL_ALL):
        """Constructor."""
        self.site = site
        self.diff = diff
        try:
            self.namespace = self.site.namespaces.resolve(namespace).pop(0)
        except (KeyError, TypeError, IndexError):
            raise ValueError('%s needs a valid namespace' % self.__class__.__name__)
        self.template = (self.namespace == 10)
        self.talkpage = self.namespace >= 0 and self.namespace % 2 == 1
        self.title = pageTitle
        self.ignore = ignore

        self.common_methods = (
            self.commonsfiledesc,
            self.fixSelfInterwiki,
            self.standardizePageFooter,
            self.fixSyntaxSave,
            self.cleanUpLinks,
            self.cleanUpSectionHeaders,
            self.putSpacesInLists,
            self.translateAndCapitalizeNamespaces,
            self.translateMagicWords,
            self.replaceDeprecatedTemplates,
            # FIXME: fix bugs and re-enable
            # self.resolveHtmlEntities,
            self.removeUselessSpaces,
            self.removeNonBreakingSpaceBeforePercent,

            self.fixHtml,
            self.fixReferences,
            self.fixStyle,
            self.fixTypo,

            self.fixArabicLetters,
            # FIXME: T144288
            # self.fix_ISBN,
        )

    @classmethod
    def from_page(cls, page, diff, ignore):
        """Create toolkit based on the page."""
        return cls(page.site, diff=diff, namespace=page.namespace(),
                   pageTitle=page.title(), ignore=ignore)

    def safe_execute(self, method, text):
        """Execute the method and catch exceptions if enabled."""
        result = None
        try:
            result = method(text)
        except Exception as e:
            if self.ignore == CANCEL_METHOD:
                pywikibot.warning(u'Unable to perform "{0}" on "{1}"!'.format(
                    method.__name__, self.title))
                pywikibot.exception(e)
            else:
                raise
        return text if result is None else result

    def _change(self, text):
        """Execute all clean up methods."""
        for method in self.common_methods:
            text = self.safe_execute(method, text)
        return text

    def change(self, text):
        """Execute all clean up methods and catch errors if activated."""
        try:
            new_text = self._change(text)
        except Exception as e:
            if self.ignore == CANCEL_PAGE:
                pywikibot.warning(u'Skipped "{0}", because an error occurred.'.format(self.title))
                pywikibot.exception(e)
                return False
            else:
                raise
        else:
            if self.diff:
                pywikibot.showDiff(text, new_text)
            return new_text

    def fixSelfInterwiki(self, text):
        """
        Interwiki links to the site itself are displayed like local links.

        Remove their language code prefix.
        """
        if not self.talkpage and pywikibot.calledModuleName() != 'interwiki':
            interwikiR = re.compile(r'\[\[(?: *:)? *%s *: *([^\[\]\n]*)\]\]'
                                    % self.site.code)
            text = interwikiR.sub(r'[[\1]]', text)
        return text

    def standardizePageFooter(self, text):
        """
        Standardize page footer.

        Makes sure that interwiki links and categories are put to the correct
        position and into the right order. This combines the old instances
        standardizeInterwiki and standardizeCategories.
        The page footer has the following section in that sequence:
        1. categories
        2. ## TODO: template beyond categories ##
        3. additional information depending on local site policy
        4. interwiki links

        """
        categories = None
        interwikiLinks = None

        # Pywikibot is no longer allowed to touch categories on the
        # German Wikipedia. See
        # https://de.wikipedia.org/wiki/Hilfe_Diskussion:Personendaten/Archiv/1#Position_der_Personendaten_am_.22Artikelende.22
        # ignoring nn-wiki of cause of the comment line above iw section
        if not self.template and '{{Personendaten' not in text and \
           '{{SORTIERUNG' not in text and '{{DEFAULTSORT' not in text and \
           self.site.code not in ('et', 'it', 'bg', 'ru'):
            categories = textlib.getCategoryLinks(text, site=self.site)

        if not self.talkpage:  # and pywikibot.calledModuleName() <> 'interwiki':
            subpage = False
            if self.template:
                loc = None
                try:
                    tmpl, loc = moved_links[self.site.code]
                    del tmpl
                except KeyError:
                    pass
                if loc is not None and loc in self.title:
                    subpage = True
            interwikiLinks = textlib.getLanguageLinks(
                text, insite=self.site, template_subpage=subpage)

            # Removing the interwiki
            text = textlib.removeLanguageLinks(text, site=self.site)

        # Adding categories
        if categories:
            # TODO: Sorting categories in alphabetic order.
            # e.g. using categories.sort()

            # TODO: Taking main cats to top
            #   for name in categories:
            #       if (re.search(u"(.+?)\|(.{,1}?)",name.title()) or
            #               name.title() == name.title().split(":")[0] + title):
            #            categories.remove(name)
            #            categories.insert(0, name)
            text = textlib.replaceCategoryLinks(text, categories,
                                                site=self.site)
        # Adding the interwiki
        if interwikiLinks:
            text = textlib.replaceLanguageLinks(text, interwikiLinks,
                                                site=self.site,
                                                template=self.template,
                                                template_subpage=subpage)
        return text

    def translateAndCapitalizeNamespaces(self, text):
        """Use localized namespace names."""
        # arz uses english stylish codes
        if self.site.sitename == 'wikipedia:arz':
            return text
        family = self.site.family
        # wiki links aren't parsed here.
        exceptions = ['nowiki', 'comment', 'math', 'pre']

        for namespace in self.site.namespaces.values():
            if namespace.id in (0, 2, 3):
                # skip main (article) namespace
                # skip user namespace, maybe gender is used
                continue
            # a clone is needed. Won't change the namespace dict
            namespaces = list(namespace)
            thisNs = namespaces.pop(0)
            if namespace.id == 6 and family.name == 'wikipedia':
                if self.site.code in ('en', 'fr') and \
                   MediaWikiVersion(self.site.version()) >= MediaWikiVersion('1.14'):
                    # do not change "Image" on en-wiki and fr-wiki
                    assert u'Image' in namespaces
                    namespaces.remove(u'Image')
                if self.site.code == 'hu':
                    # do not change "Kép" on hu-wiki
                    assert u'Kép' in namespaces
                    namespaces.remove(u'Kép')
                elif self.site.code == 'pt':
                    # TODO: bug T57242
                    continue
            # lowerspaced and underscored namespaces
            for i in range(len(namespaces)):
                item = namespaces[i].replace(' ', '[ _]')
                item = u'[%s%s]' % (item[0], item[0].lower()) + item[1:]
                namespaces[i] = item
            namespaces.append(first_lower(thisNs))
            if thisNs and namespaces:
                text = textlib.replaceExcept(
                    text,
                    r'\[\[\s*(%s) *:(?P<nameAndLabel>.*?)\]\]'
                    % '|'.join(namespaces),
                    r'[[%s:\g<nameAndLabel>]]' % thisNs,
                    exceptions)
        return text

    def translateMagicWords(self, text):
        """Use localized magic words."""
        # not wanted at ru
        # arz uses english stylish codes
        # no need to run on English wikis
        if self.site.code not in ['arz', 'en', 'ru']:
            def replace_magicword(match):
                split = match.group().split('|')
                # push ']]' out and re-add below
                split[-1] = split[-1][:-2]
                for magicword in ['img_thumbnail', 'img_left', 'img_center',
                                  'img_right', 'img_none', 'img_framed',
                                  'img_frameless', 'img_border', 'img_upright',
                                  ]:
                    aliases = list(self.site.getmagicwords(magicword))
                    preferred = aliases.pop(0)
                    if not aliases:
                        continue
                    split[1:] = list(map(
                        lambda x: preferred if x.strip() in aliases else x,
                        split[1:]))
                return '|'.join(split) + ']]'

            exceptions = ['nowiki', 'comment', 'math', 'pre', 'source']
            regex = re.compile(
                FILE_LINK_REGEX % '|'.join(self.site.namespaces[6]),
                flags=re.X)
            text = textlib.replaceExcept(text, regex, replace_magicword,
                                         exceptions)
        return text

    def cleanUpLinks(self, text):
        """Tidy up wikilinks found in a string.

        This function will:
        * Replace underscores with spaces

        * Move leading and trailing spaces out of the wikilink and into the
          surrounding text

        * Convert URL-encoded characters into Unicode-encoded characters

        * Move trailing characters out of the link and make the link without
          using a pipe, if possible

        * Capitalize the article title of the link, if appropriate

        @param text: string to perform the clean-up on
        @type text: str
        @return: text with tidied wikilinks
        @rtype: str
        """
        # helper function which works on one link and either returns it
        # unmodified, or returns a replacement.
        def handleOneLink(match):
            titleWithSection = match.group('titleWithSection')
            label = match.group('label')
            trailingChars = match.group('linktrail')
            newline = match.group('newline')

            try:
                is_interwiki = self.site.isInterwikiLink(titleWithSection)
            except ValueError:  # T111513
                is_interwiki = True

            if not is_interwiki:
                # The link looks like this:
                # [[page_title|link_text]]trailing_chars
                # We only work on namespace 0 because pipes and linktrails work
                # differently for images and categories.
                page = pywikibot.Page(pywikibot.Link(titleWithSection,
                                                     self.site))
                try:
                    namespace = page.namespace()
                except pywikibot.InvalidTitle:
                    return match.group()
                if namespace == 0:
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
                        hadTrailingSpaces = (len(titleWithSection) !=
                                             titleLength)

                    # Convert URL-encoded characters to unicode
                    from pywikibot.page import url2unicode
                    titleWithSection = url2unicode(titleWithSection,
                                                   encodings=self.site)

                    if titleWithSection == '':
                        # just skip empty links.
                        return match.group()

                    # Remove unnecessary initial and final spaces from label.
                    # Please note that some editors prefer spaces around pipes.
                    # (See [[en:Wikipedia:Semi-bots]]). We remove them anyway.
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

                    if self.site.siteinfo['case'] == 'first-letter':
                        firstcase_title = first_lower(titleWithSection)
                        firstcase_label = first_lower(label)
                    else:
                        firstcase_title = titleWithSection
                        firstcase_label = label

                    if firstcase_label == firstcase_title:
                        newLink = '[[%s]]' % label
                    # Check if we can create a link with trailing characters
                    # instead of a pipelink
                    elif (firstcase_label.startswith(firstcase_title) and
                          trailR.sub('', label[len(titleWithSection):]) == ''):
                        newLink = '[[%s]]%s' % (
                            label[:len(titleWithSection)],
                            label[len(titleWithSection):])

                    else:
                        # Try to capitalize the first letter of the title.
                        # Not useful for languages that don't capitalize nouns.
                        # TODO: Add a configuration variable for each site,
                        # which determines if the link target is written in
                        # uppercase
                        if self.site.sitename == 'wikipedia:de':
                            titleWithSection = first_upper(titleWithSection)
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
    # group <newline> depends whether the links starts with a new line.
    # group <titleWithSection> is the page title and section, that is,
    # everything before | or ]. It'll include the # to make life easier for us.
    # group <label> is the alternative link title between | and ].
    # group <linktrail> is the link trail after ]] which are part of the word.
    # note that the definition of 'letter' varies from language to language.
        linkR = re.compile(
            r'(?P<newline>[\n]*)\[\[(?P<titleWithSection>[^\]\|]+)'
            r'(\|(?P<label>[^\]\|]*))?\]\](?P<linktrail>' +
            self.site.linktrail() + ')')

        text = textlib.replaceExcept(text, linkR, handleOneLink,
                                     ['comment', 'math', 'nowiki', 'pre',
                                      'startspace'])
        return text

    def resolveHtmlEntities(self, text):
        """Replace HTML entities with unicode."""
        ignore = [
            38,     # Ampersand (&amp;)
            39,     # Single quotation mark (&quot;) - bug T26093
            60,     # Less than (&lt;)
            62,     # Great than (&gt;)
            91,     # Opening square bracket ([)
                    # - sometimes used intentionally inside links
            93,     # Closing square bracket (])
                    # - used intentionally inside links
            124,    # Vertical bar (|)
                    # - used intentionally in navigation bar templates on w:de
            160,    # Non-breaking space (&nbsp;)
                    # - not supported by Firefox textareas
            173,    # Soft-hypen (&shy;) - enable editing
            8206,   # Left-to-right mark (&ltr;)
            8207,   # Right-to-left mark (&rtl;)
        ]
        if self.template:
            ignore += [58]
        text = pywikibot.html2unicode(text, ignore=ignore)
        return text

    def removeUselessSpaces(self, text):
        """Cleanup multiple or trailing spaces."""
        exceptions = ['comment', 'math', 'nowiki', 'pre', 'startspace', 'table']
        if self.site.sitename != 'wikipedia:cs':
            exceptions.append('template')
        text = textlib.replaceExcept(text, r'(?m)[\t ]+( |$)', r'\1', exceptions,
                                     site=self.site)
        return text

    def removeNonBreakingSpaceBeforePercent(self, text):
        """
        Remove a non-breaking space between number and percent sign.

        Newer MediaWiki versions automatically place a non-breaking space in
        front of a percent sign, so it is no longer required to place it
        manually.
        """
        text = textlib.replaceExcept(text, r'(\d)&nbsp;%', r'\1 %',
                                     ['timeline'])
        return text

    def cleanUpSectionHeaders(self, text):
        """
        Add a space between the equal signs and the section title.

        Example: ==Section title== becomes == Section title ==

        NOTE: This space is recommended in the syntax help on the English and
        German Wikipedia. It is not wanted on Lojban Wiktionary (per T168399)
        and it might be that it is not wanted on other wikis. If there are any
        complaints, please file a bug report.
        """
        if self.site.sitename == 'wiktionary:jbo':
            return text
        return textlib.replaceExcept(
            text,
            r'(?m)^(={1,7}) *(?P<title>[^=]+?) *\1 *\r?\n',
            r'\1 \g<title> \1%s' % config.LS,
            ['comment', 'math', 'nowiki', 'pre'])

    def putSpacesInLists(self, text):
        """
        Add a space between the * or # and the text.

        NOTE: This space is recommended in the syntax help on the English,
        German, and French Wikipedia. It might be that it is not wanted on other
        wikis. If there are any complaints, please file a bug report.
        """
        if not self.template:
            exceptions = ['comment', 'math', 'nowiki', 'pre', 'source', 'template',
                          'timeline', self.site.redirectRegex()]
            text = textlib.replaceExcept(
                text,
                r'(?m)^(?P<bullet>[:;]*(\*+|#+)[:;\*#]*)(?P<char>[^\s\*#:;].+?)',
                r'\g<bullet> \g<char>',
                exceptions)
        return text

    def replaceDeprecatedTemplates(self, text):
        """Replace deprecated templates."""
        exceptions = ['comment', 'math', 'nowiki', 'pre']
        builder = _MultiTemplateMatchBuilder(self.site)

        if self.site.family.name in deprecatedTemplates and \
           self.site.code in deprecatedTemplates[self.site.family.name]:
            for template in deprecatedTemplates[
                    self.site.family.name][self.site.code]:
                old = template[0]
                new = template[1]
                if new is None:
                    new = ''
                else:
                    new = '{{%s}}' % new

                text = textlib.replaceExcept(
                    text,
                    builder.pattern(old),
                    new, exceptions)

        return text

    # from fixes.py
    def fixSyntaxSave(self, text):
        """Convert weblinks to wikilink, fix link syntax."""
        def replace_link(match):
            """Create a string to replace a single link."""
            replacement = '[['
            if re.match(r'(?:' + '|'.join(list(self.site.namespaces[6]) +
                        list(self.site.namespaces[14])) + '):',
                        match.group('link')):
                replacement += ':'
            replacement += match.group('link')
            if match.group('title'):
                replacement += '|' + match.group('title')
            return replacement + ']]'

        exceptions = ['nowiki', 'comment', 'math', 'pre', 'source',
                      'startspace']
        # link to the wiki working on
        # Only use suffixes for article paths
        for suffix in self.site._interwiki_urls(True):
            http_url = self.site.base_url(suffix, 'http')
            if self.site.protocol() == 'http':
                https_url = None
            else:
                https_url = self.site.base_url(suffix, 'https')
            # compare strings without the protocol, if they are empty support
            # also no prefix (//en.wikipedia.org/…)
            if https_url is not None and http_url[4:] == https_url[5:]:
                urls = ['(?:https?:)?' + re.escape(http_url[5:])]
            else:
                urls = [re.escape(url) for url in (http_url, https_url)
                        if url is not None]
            for url in urls:
                # Only include links which don't include the separator as
                # the wikilink won't support additional parameters
                separator = '?'
                if '?' in suffix:
                    separator += '&'
                # Match first a non space in the title to prevent that multiple
                # spaces at the end without title will be matched by it
                text = textlib.replaceExcept(
                    text,
                    r'\[\[?' + url + r'(?P<link>[^' + separator + r']+?)'
                    r'(\s+(?P<title>[^\s].*?))?\s*\]\]?',
                    replace_link, exceptions, site=self.site)
        # external link in/starting with double brackets
        text = textlib.replaceExcept(
            text,
            r'\[\[(?P<url>https?://[^\]]+?)\]\]?',
            r'[\g<url>]', exceptions, site=self.site)
        # external link and description separated by a pipe, with
        # whitespace in front of the pipe, so that it is clear that
        # the dash is not a legitimate part of the URL.
        text = textlib.replaceExcept(
            text,
            r'\[(?P<url>https?://[^\|\] \r\n]+?) +\| *(?P<label>[^\|\]]+?)\]',
            r'[\g<url> \g<label>]', exceptions)
        # dash in external link, where the correct end of the URL can
        # be detected from the file extension. It is very unlikely that
        # this will cause mistakes.
        extensions = [r'\.{0}'.format(ext)
                      for ext in ['pdf', 'html?', 'php', 'aspx?', 'jsp']]
        text = textlib.replaceExcept(
            text,
            r'\[(?P<url>https?://[^\|\] ]+?(' + '|'.join(extensions) + r')) *'
            r'\| *(?P<label>[^\|\]]+?)\]',
            r'[\g<url> \g<label>]', exceptions)
        return text

    def fixHtml(self, text):
        """Relace html markups with wikitext markups."""
        def replace_header(match):
            """Create a header string for replacing."""
            depth = int(match.group(1))
            return r'{0} {1} {0}'.format('=' * depth, match.group(2))

        # Everything case-insensitive (?i)
        # Keep in mind that MediaWiki automatically converts <br> to <br />
        exceptions = ['nowiki', 'comment', 'math', 'pre', 'source',
                      'startspace']
        text = textlib.replaceExcept(text, r'(?i)<(b|strong)>(.*?)</\1>',
                                     r"'''\2'''", exceptions, site=self.site)
        text = textlib.replaceExcept(text, r'(?i)<(i|em)>(.*?)</\1>',
                                     r"''\2''", exceptions, site=self.site)
        # horizontal line without attributes in a single line
        text = textlib.replaceExcept(text, r'(?i)([\r\n])<hr[ /]*>([\r\n])',
                                     r'\1----\2', exceptions)
        # horizontal line with attributes; can't be done with wiki syntax
        # so we only make it XHTML compliant
        text = textlib.replaceExcept(text, r'(?i)<hr ([^>/]+?)>',
                                     r'<hr \1 />',
                                     exceptions)
        # a header where only spaces are in the same line
        text = textlib.replaceExcept(
            text,
            r'(?i)(?<=[\r\n]) *<h([1-7])> *([^<]+?) *</h\1> *(?=[\r\n])',
            replace_header,
            exceptions)
        # TODO: maybe we can make the bot replace <p> tags with \r\n's.
        return text

    def fixReferences(self, text):
        """Fix references tags."""
        # See also https://en.wikipedia.org/wiki/User:AnomieBOT/source/tasks/OrphanReferenceFixer.pm
        exceptions = ['nowiki', 'comment', 'math', 'pre', 'source',
                      'startspace']

        # it should be name = " or name=" NOT name   ="
        text = re.sub(r'(?i)<ref +name(= *| *=)"', r'<ref name="', text)
        # remove empty <ref/>-tag
        text = textlib.replaceExcept(text,
                                     r'(?i)(<ref\s*/>|<ref *>\s*</ref>)',
                                     r'', exceptions)
        text = textlib.replaceExcept(text,
                                     r'(?i)<ref\s+([^>]+?)\s*>\s*</ref>',
                                     r'<ref \1/>', exceptions)
        return text

    def fixStyle(self, text):
        """Convert prettytable to wikitable class."""
        exceptions = ['nowiki', 'comment', 'math', 'pre', 'source',
                      'startspace']
        if self.site.code in ('de', 'en'):
            text = textlib.replaceExcept(text,
                                         r'(class="[^"]*)prettytable([^"]*")',
                                         r'\1wikitable\2', exceptions)
        return text

    def fixTypo(self, text):
        """Fix units."""
        exceptions = ['nowiki', 'comment', 'math', 'pre', 'source',
                      'startspace', 'gallery', 'hyperlink', 'interwiki', 'link']
        # change <number> ccm -> <number> cm³
        text = textlib.replaceExcept(text, r'(\d)\s*(?:&nbsp;)?ccm',
                                     r'\1&nbsp;cm³', exceptions,
                                     site=self.site)
        # Solve wrong Nº sign with °C or °F
        # additional exception requested on fr-wiki for this stuff
        pattern = re.compile(u'«.*?»', re.UNICODE)
        exceptions.append(pattern)
        text = textlib.replaceExcept(text, r'(\d)\s*(?:&nbsp;)?[º°]([CF])',
                                     r'\1&nbsp;°\2', exceptions, site=self.site)
        text = textlib.replaceExcept(text, u'º([CF])', u'°' + r'\1',
                                     exceptions,
                                     site=self.site)
        return text

    def fixArabicLetters(self, text):
        """Fix arabic and persian letters."""
        if self.site.code not in ['ckb', 'fa']:
            return text
        exceptions = [
            'gallery',
            'file',
            'hyperlink',
            'interwiki',
            # FIXME: but changes letters inside wikilinks
            # 'link',
            'math',
            'pre',
            'template',
            'timeline',
            'ref',
            'source',
            'startspace',
            'inputbox',
        ]
        # FIXME: use textlib.NON_LATIN_DIGITS
        # valid digits
        digits = {
            'ckb': u'٠١٢٣٤٥٦٧٨٩',
            'fa': u'۰۱۲۳۴۵۶۷۸۹',
        }
        faChrs = u'ءاآأإئؤبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیةيك' + digits['fa']
        new = digits.pop(self.site.code)
        # This only works if there are only two items in digits dict
        old = digits[list(digits.keys())[0]]
        # not to let bot edits in latin content
        exceptions.append(re.compile(u"[^%(fa)s] *?\"*? *?, *?[^%(fa)s]"
                                     % {'fa': faChrs}))
        text = textlib.replaceExcept(text, ',', '،', exceptions, site=self.site)
        if self.site.code == 'ckb':
            text = textlib.replaceExcept(text,
                                         '\u0647([.\u060c_<\\]\\s])',
                                         '\u06d5\\1', exceptions,
                                         site=self.site)
            text = textlib.replaceExcept(text, 'ه\u200c', 'ە', exceptions,
                                         site=self.site)
            text = textlib.replaceExcept(text, 'ه', 'ھ', exceptions,
                                         site=self.site)
        text = textlib.replaceExcept(text, 'ك', 'ک', exceptions,
                                     site=self.site)
        text = textlib.replaceExcept(text, '[ىي]', 'ی', exceptions,
                                     site=self.site)

        return text

        # FIXME: split this function into two.
        # replace persian/arabic digits
        # deactivated due to bug 55185
        for i in range(0, 10):
            text = textlib.replaceExcept(text, old[i], new[i], exceptions)
        # do not change digits in class, style and table params
        pattern = re.compile(r'\w+=(".+?"|\d+)', re.UNICODE)
        exceptions.append(pattern)
        # do not change digits inside html-tags
        pattern = re.compile(u'<[/]*?[^</]+?[/]*?>', re.UNICODE)
        exceptions.append(pattern)
        exceptions.append('table')  # exclude tables for now
        # replace digits
        for i in range(0, 10):
            text = textlib.replaceExcept(text, str(i), new[i], exceptions)
        return text

    def commonsfiledesc(self, text):
        """
        Clean up file descriptions on the Wikimedia Commons.

        It is working according to [1] and works only on pages in the file
        namespace on the Wikimedia Commons.

        [1]: https://commons.wikimedia.org/wiki/Commons:Tools/pywiki_file_description_cleanup
        """
        if self.site.sitename != 'commons:commons' or self.namespace == 6:
            return
        # section headers to {{int:}} versions
        exceptions = ['comment', 'includeonly', 'math', 'noinclude', 'nowiki',
                      'pre', 'source', 'ref', 'timeline']
        text = textlib.replaceExcept(text,
                                     r"([\r\n]|^)\=\= *Summary *\=\=",
                                     r"\1== {{int:filedesc}} ==",
                                     exceptions, True)
        text = textlib.replaceExcept(
            text,
            r"([\r\n])\=\= *\[\[Commons:Copyright tags\|Licensing\]\]: *\=\=",
            r"\1== {{int:license-header}} ==", exceptions, True)
        text = textlib.replaceExcept(
            text,
            r"([\r\n])\=\= *(Licensing|License information|{{int:license}}) *\=\=",
            r"\1== {{int:license-header}} ==", exceptions, True)

        # frequent field values to {{int:}} versions
        text = textlib.replaceExcept(
            text,
            r'([\r\n]\|[Ss]ource *\= *)'
            r'(?:[Oo]wn work by uploader|[Oo]wn work|[Ee]igene [Aa]rbeit) *([\r\n])',
            r'\1{{own}}\2', exceptions, True)
        text = textlib.replaceExcept(
            text,
            r'(\| *Permission *\=) *(?:[Ss]ee below|[Ss]iehe unten) *([\r\n])',
            r'\1\2', exceptions, True)

        # added to transwikied pages
        text = textlib.replaceExcept(text, r'__NOTOC__', '', exceptions, True)

        # tracker element for js upload form
        text = textlib.replaceExcept(
            text,
            r'<!-- *{{ImageUpload\|(?:full|basic)}} *-->',
            '', exceptions[1:], True)
        text = textlib.replaceExcept(text, r'{{ImageUpload\|(?:basic|full)}}',
                                     '', exceptions, True)

        # duplicated section headers
        text = textlib.replaceExcept(
            text,
            r'([\r\n]|^)\=\= *{{int:filedesc}} *\=\=(?:[\r\n ]*)\=\= *{{int:filedesc}} *\=\=',
            r'\1== {{int:filedesc}} ==', exceptions, True)
        text = textlib.replaceExcept(
            text,
            r'([\r\n]|^)\=\= *{{int:license-header}} *\=\=(?:[\r\n ]*)'
            r'\=\= *{{int:license-header}} *\=\=',
            r'\1== {{int:license-header}} ==', exceptions, True)
        return text

    def fix_ISBN(self, text):
        """Hyphenate ISBN numbers."""
        return _reformat_ISBNs(
            text, strict=False if self.ignore == CANCEL_MATCH else True)
