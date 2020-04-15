#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This module can do slight modifications to tidy a wiki page's source code.

The changes are not supposed to change the look of the rendered wiki page.

If you wish to run this as an stand-alone script, use:

    scripts/cosmetic_changes.py

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

    cosmetic_changes_deny_script += ['your_script_name_1',
                                     'your_script_name_2']
"""
#
# (C) Pywikibot team, 2006-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import re

try:
    import stdnum.isbn as stdnum_isbn
except ImportError:
    stdnum_isbn = None

import pywikibot

from pywikibot.page import url2unicode
from pywikibot import textlib
from pywikibot.textlib import (_MultiTemplateMatchBuilder, FILE_LINK_REGEX,
                               _get_regexes)
from pywikibot.tools import (
    deprecated, deprecated_args, first_lower, first_upper
)


# Subpage templates. Must be in lower case,
# whereas subpage itself must be case sensitive
# This is also used by interwiki.py
# TODO: Maybe move it to family file and implement global instances
moved_links = {
    'ar': (['documentation', 'template documentation', 'شرح', 'توثيق'],
           '/doc'),
    'bn': ('documentation', '/doc'),
    'ca': ('ús de la plantilla', '/ús'),
    'cs': ('dokumentace', '/doc'),
    'da': ('dokumentation', '/doc'),
    'de': ('dokumentation', '/Meta'),
    'dsb': (['dokumentacija', 'doc'], '/Dokumentacija'),
    'en': (['documentation', 'template documentation', 'template doc',
            'doc', 'documentation, template'], '/doc'),
    'es': (['documentación', 'documentación de plantilla'], '/doc'),
    'eu': ('txantiloi dokumentazioa', '/dok'),
    'fa': (['documentation', 'template documentation', 'template doc',
            'doc', 'توضیحات', 'زیرصفحه توضیحات'], '/doc'),
    # fi: no idea how to handle this type of subpage at :Metasivu:
    'fi': ('mallineohje', None),
    'fr': (['/documentation', 'documentation', 'doc_modèle',
            'documentation modèle', 'documentation modèle compliqué',
            'documentation modèle en sous-page',
            'documentation modèle compliqué en sous-page',
            'documentation modèle utilisant les parserfunctions en sous-page',
            ],
           '/Documentation'),
    'hsb': (['dokumentacija', 'doc'], '/Dokumentacija'),
    'hu': ('sablondokumentáció', '/doc'),
    'id': ('template doc', '/doc'),
    'ilo': ('documentation', '/doc'),
    'ja': ('documentation', '/doc'),
    'ka': ('თარგის ინფო', '/ინფო'),
    'ko': ('documentation', '/설명문서'),
    'ms': ('documentation', '/doc'),
    'no': ('dokumentasjon', '/dok'),
    'nn': ('dokumentasjon', '/dok'),
    'pl': ('dokumentacja', '/opis'),
    'pt': (['documentação', '/doc'], '/doc'),
    'ro': ('documentaţie', '/doc'),
    'ru': ('doc', '/doc'),
    'simple': (['documentation',
                'template documentation',
                'template doc',
                'doc',
                'documentation, template'], '/doc'),
    'sk': ('dokumentácia', '/Dokumentácia'),
    'sv': ('dokumentation', '/dok'),
    'uk': (['документація', 'doc', 'documentation'], '/Документація'),
    'ur': (['دستاویز', 'توثيق', 'شرح', 'توضیحات',
            'documentation', 'template doc', 'doc',
            'documentation, template'], '/doc'),
    'vi': ('documentation', '/doc'),
    'zh': (['documentation', 'doc'], '/doc'),
}

# Template which should be replaced or removed.
# Use a list with two entries. The first entry will be replaced by the second.
# Examples:
# For removing {{Foo}}, the list must be:
#           ('Foo', None),
#
# The following also works:
#           ('Foo', ''),
#
# For replacing {{Foo}} with {{Bar}} the list must be:
#           ('Foo', 'Bar'),
#
# This also removes all template parameters of {{Foo}}
# For replacing {{Foo}} with {{Bar}} but keep the template
# parameters in its original order, please use:
#           ('Foo', 'Bar\\g<parameters>'),

deprecatedTemplates = {
    'wikipedia': {
        'de': [
            ('Belege', 'Belege fehlen\\g<parameters>'),
            ('Quelle', 'Belege fehlen\\g<parameters>'),
            ('Quellen', 'Belege fehlen\\g<parameters>'),
            ('Quellen fehlen', 'Belege fehlen\\g<parameters>'),
        ],
        'ur': [
            ('Infobox former country',
             'خانہ معلومات سابقہ ملک\\g<parameters>'),
            ('Infobox Former Country',
             'خانہ معلومات سابقہ ملک\\g<parameters>'),
        ],
    }
}

CANCEL_ALL = False
CANCEL_PAGE = 1
CANCEL_METHOD = 2
CANCEL_MATCH = 3


def _format_isbn_match(match, strict=True):
    """Helper function to validate and format a single matched ISBN."""
    if not stdnum_isbn:
        raise NotImplementedError(
            'ISBN functionality not available. Install stdnum package.')

    isbn = match.group('code')
    try:
        stdnum_isbn.validate(isbn)
    except stdnum_isbn.ValidationError as e:
        if strict:
            raise
        pywikibot.log('ISBN "%s" validation error: %s' % (isbn, e))
        return isbn

    return stdnum_isbn.format(isbn)


def _reformat_ISBNs(text, strict=True):
    """Helper function to normalise ISBNs in text.

    @raises Exception: Invalid ISBN encountered when strict enabled
    """
    return textlib.reformat_ISBNs(
        text, lambda match: _format_isbn_match(match, strict=strict))


class CosmeticChangesToolkit(object):

    """Cosmetic changes toolkit."""

    @deprecated_args(debug='show_diff', redirect=None, diff='show_diff')
    def __init__(self, site, show_diff=False, namespace=None, pageTitle=None,
                 ignore=CANCEL_ALL):
        """Initializer."""
        self.site = site
        self.show_diff = show_diff
        try:
            self.namespace = self.site.namespaces.resolve(namespace).pop(0)
        except (KeyError, TypeError, IndexError):
            raise ValueError('{0} needs a valid namespace'
                             .format(self.__class__.__name__))
        self.template = (self.namespace == 10)
        self.talkpage = self.namespace >= 0 and self.namespace % 2 == 1
        self.title = pageTitle
        self.ignore = ignore

        self.common_methods = [
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
            self.resolveHtmlEntities,
            self.removeEmptySections,
            self.removeUselessSpaces,
            self.removeNonBreakingSpaceBeforePercent,

            self.fixHtml,
            self.fixReferences,
            self.fixStyle,
            self.fixTypo,

            self.fixArabicLetters,
        ]
        if stdnum_isbn:
            self.common_methods.append(self.fix_ISBN)

    @property
    @deprecated('show_diff', since='20200415')
    def diff(self):
        """CosmeticChangesToolkit.diff attribute getter."""
        return self.show_diff

    @diff.setter
    @deprecated('show_diff', since='20200415')
    def diff(self, value):
        """CosmeticChangesToolkit.diff attribute setter."""
        self.show_diff = bool(value)

    @classmethod
    @deprecated_args(diff='show_diff')
    def from_page(cls, page, show_diff=False, ignore=CANCEL_ALL):
        """Create toolkit based on the page."""
        return cls(page.site, show_diff=show_diff, namespace=page.namespace(),
                   pageTitle=page.title(), ignore=ignore)

    def safe_execute(self, method, text):
        """Execute the method and catch exceptions if enabled."""
        result = None
        try:
            result = method(text)
        except Exception as e:
            if self.ignore == CANCEL_METHOD:
                pywikibot.warning('Unable to perform "{0}" on "{1}"!'.format(
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
                pywikibot.warning('Skipped "{0}", because an error occurred.'
                                  .format(self.title))
                pywikibot.exception(e)
                return False
            else:
                raise
        else:
            if self.show_diff:
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

        Makes sure that interwiki links and categories are put
        into the correct position and into the right order. This
        combines the old instances of standardizeInterwiki
        and standardizeCategories.

        The page footer consists of the following parts
        in that sequence:
        1. categories
        2. additional information depending on the local site policy
        3. interwiki
        """
        categories = []
        interwiki_links = []

        # get categories
        if not self.template:
            categories = textlib.getCategoryLinks(text, site=self.site)

        if not self.talkpage:
            subpage = False
            if self.template:
                try:
                    tmpl, loc = moved_links[self.site.code]
                    del tmpl
                except KeyError:
                    loc = None
                if loc is not None and loc in self.title:
                    subpage = True

            # get interwiki
            interwiki_links = textlib.getLanguageLinks(
                text, insite=self.site, template_subpage=subpage)

            # remove interwiki
            text = textlib.removeLanguageLinks(text, site=self.site)

        # add categories, main to top
        if categories:
            # TODO: Sort categories in alphabetic order, e.g. using
            # categories.sort()? (T100265)
            # TODO: Get main categories from Wikidata?
            main = pywikibot.Category(self.site, 'Category:' + self.title,
                                      sort_key=' ')
            if main in categories:
                categories.pop(categories.index(main))
                categories.insert(0, main)
            text = textlib.replaceCategoryLinks(text, categories,
                                                site=self.site)

        # add interwiki
        if interwiki_links:
            text = textlib.replaceLanguageLinks(text, interwiki_links,
                                                site=self.site,
                                                template=self.template,
                                                template_subpage=subpage)

        return text

    def translateAndCapitalizeNamespaces(self, text):
        """Use localized namespace names."""
        # arz uses english stylish codes
        if self.site.sitename == 'wikipedia:arz':
            return text
        # wiki links aren't parsed here.
        exceptions = ['nowiki', 'comment', 'math', 'pre']

        for namespace in self.site.namespaces.values():
            if namespace == 0:
                # skip main (article) namespace
                continue
            # a clone is needed. Won't change the namespace dict
            namespaces = list(namespace)
            if namespace == 6 and self.site.family.name == 'wikipedia':
                if self.site.code in ('en', 'fr') \
                        and self.site.mw_version >= '1.14':
                    # do not change "Image" on en-wiki and fr-wiki
                    assert 'Image' in namespaces
                    namespaces.remove('Image')
                if self.site.code == 'hu':
                    # do not change "Kép" on hu-wiki
                    assert 'Kép' in namespaces
                    namespaces.remove('Kép')
                elif self.site.code == 'pt':
                    # use "Imagem" by default on pt-wiki (per T57242)
                    assert 'Imagem' in namespaces
                    namespaces.insert(
                        0, namespaces.pop(namespaces.index('Imagem')))
            # final namespace variant
            final_ns = namespaces.pop(0)
            if namespace in (2, 3):
                # skip localized user namespace, maybe gender is used
                namespaces = ['User' if namespace == 2 else 'User talk']
            # lowerspaced and underscored namespaces
            for i, item in enumerate(namespaces):
                item = item.replace(' ', '[ _]')
                item = '[%s%s]' % (item[0], item[0].lower()) + item[1:]
                namespaces[i] = item
            namespaces.append(first_lower(final_ns))
            if final_ns and namespaces:
                if self.site.sitename == 'wikipedia:pt' and namespace == 6:
                    # only change on these file extensions (per T57242)
                    extensions = ('png', 'gif', 'jpg', 'jpeg', 'svg', 'tiff',
                                  'tif')
                    text = textlib.replaceExcept(
                        text,
                        r'\[\[\s*({}) *:(?P<name>[^\|\]]*?\.({}))'
                        r'(?P<label>.*?)\]\]'
                        .format('|'.join(namespaces), '|'.join(extensions)),
                        r'[[{}:\g<name>\g<label>]]'.format(final_ns),
                        exceptions)
                else:
                    text = textlib.replaceExcept(
                        text,
                        r'\[\[\s*(%s) *:(?P<nameAndLabel>.*?)\]\]'
                        % '|'.join(namespaces),
                        r'[[%s:\g<nameAndLabel>]]' % final_ns,
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

            if is_interwiki:
                return match.group()

            # The link looks like this:
            # [[page_title|link_text]]trailing_chars
            # We only work on namespace 0 because pipes and linktrails work
            # differently for images and categories.
            page = pywikibot.Page(pywikibot.Link(titleWithSection, self.site))
            try:
                in_main_namespace = page.namespace() == 0
            except pywikibot.InvalidTitle:
                in_main_namespace = False
            if not in_main_namespace:
                return match.group()

            # Replace underlines by spaces, also multiple underlines
            titleWithSection = re.sub('_+', ' ', titleWithSection)
            # Remove double spaces
            titleWithSection = re.sub('  +', ' ', titleWithSection)
            # Remove unnecessary leading spaces from title,
            # but remember if we did this because we eventually want
            # to re-add it outside of the link later.
            titleLength = len(titleWithSection)
            titleWithSection = titleWithSection.lstrip()
            hadLeadingSpaces = len(titleWithSection) != titleLength
            hadTrailingSpaces = False
            # Remove unnecessary trailing spaces from title,
            # but remember if we did this because it may affect
            # the linktrail and because we eventually want to
            # re-add it outside of the link later.
            if not trailingChars:
                titleLength = len(titleWithSection)
                titleWithSection = titleWithSection.rstrip()
                hadTrailingSpaces = len(titleWithSection) != titleLength

            # Convert URL-encoded characters to unicode
            titleWithSection = url2unicode(titleWithSection,
                                           encodings=self.site)

            if not titleWithSection:
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
                hadLeadingSpaces = len(label) != labelLength
                # Remove unnecessary trailing spaces from label,
                # but remember if we did this because it affects
                # the linktrail.
                if not trailingChars:
                    labelLength = len(label)
                    label = label.rstrip()
                    hadTrailingSpaces = len(label) != labelLength
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
            elif (firstcase_label.startswith(firstcase_title)
                  and trailR.sub('', label[len(titleWithSection):]) == ''):
                newLink = '[[%s]]%s' % (label[:len(titleWithSection)],
                                        label[len(titleWithSection):])

            else:
                # Try to capitalize the first letter of the title.
                # Not useful for languages that don't capitalize nouns.
                # TODO: Add a configuration variable for each site,
                # which determines if the link target is written in
                # uppercase
                if self.site.sitename == 'wikipedia:de':
                    titleWithSection = first_upper(titleWithSection)
                newLink = '[[%s|%s]]' % (titleWithSection, label)
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
            r'(\|(?P<label>[^\]\|]*))?\]\](?P<linktrail>'
            + self.site.linktrail() + ')')

        text = textlib.replaceExcept(text, linkR, handleOneLink,
                                     ['comment', 'math', 'nowiki', 'pre',
                                      'startspace'])
        return text

    def resolveHtmlEntities(self, text):
        """Replace HTML entities with unicode."""
        ignore = [
            38,     # Ampersand (&amp;)
            39,     # Single quotation mark (&quot;) per T26093
            60,     # Less than (&lt;)
            62,     # Greater than (&gt;)
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
            ignore += [32]  # Space ( )
            ignore += [58]  # Colon (:)
        text = pywikibot.html2unicode(text, ignore=ignore, exceptions=['code'])
        return text

    def removeEmptySections(self, text):
        """Cleanup empty sections."""
        # userspace contains article stubs without nobots/in use templates
        if self.namespace == 2:
            return text

        skippings = ['comment', 'category']
        skip_regexes = _get_regexes(skippings, self.site)
        # site defined templates
        skip_templates = {
            'cs': ('Pahýl[ _]část',),  # stub section
        }
        if self.site.code in skip_templates:
            for template in skip_templates[self.site.code]:
                skip_regexes.append(
                    re.compile(r'\{\{\s*%s\s*\}\}' % template, re.I))
        # empty lists
        skip_regexes.append(re.compile(r'(?m)^[\*#] *$'))

        # get stripped sections
        stripped_text = textlib.removeLanguageLinks(text, self.site, '\n')
        for reg in skip_regexes:
            stripped_text = reg.sub(r'', stripped_text)
        strip_sections = textlib.extract_sections(
            stripped_text, self.site)[1]

        # get proper sections
        header, sections, footer = textlib.extract_sections(text, self.site)

        # iterate stripped sections and create a new page body
        new_body = []
        for i, strip_section in enumerate(strip_sections):
            current_heading = sections[i][0]
            try:
                next_heading = sections[i + 1][0]
            except IndexError:
                next_heading = ''
            current_dep = (len(current_heading)
                           - len(current_heading.lstrip('=')))
            next_dep = len(next_heading) - len(next_heading.lstrip('='))
            if strip_section[1].strip() or current_dep < next_dep:
                new_body.extend(sections[i])
        return header + ''.join(new_body) + footer

    def removeUselessSpaces(self, text):
        """Cleanup multiple or trailing spaces."""
        exceptions = ['comment', 'math', 'nowiki', 'pre', 'startspace',
                      'source', 'table']
        if self.site.sitename != 'wikipedia:cs':
            exceptions.append('template')
        text = textlib.replaceExcept(text, r'(?m)[\t ]+( |$)', r'\1',
                                     exceptions, site=self.site)
        return text

    def removeNonBreakingSpaceBeforePercent(self, text):
        """
        Remove a non-breaking space between number and percent sign.

        Newer MediaWiki versions automatically place a non-breaking space in
        front of a percent sign, so it is no longer required to place it
        manually.
        """
        text = textlib.replaceExcept(
            text, r'(\d)&(?:nbsp|#160|#x[Aa]0);%', r'\1 %', ['timeline'])
        return text

    def cleanUpSectionHeaders(self, text):
        """
        Add a space between the equal signs and the section title.

        Example: ==Section title== becomes == Section title ==

        NOTE: This space is recommended in the syntax help on the English and
        German Wikipedia. It is not wanted on Lojban and English Wiktionary
        (T168399, T169064) and it might be that it is not wanted on other
        wikis. If there are any complaints, please file a bug report.
        """
        if self.site.sitename in ['wiktionary:jbo', 'wiktionary:en']:
            return text
        return textlib.replaceExcept(
            text,
            r'(?m)^(={1,6})[ \t]*(?P<title>.*[^\s=])[ \t]*\1[ \t]*\r?\n',
            r'\1 \g<title> \1\n',
            ['comment', 'math', 'nowiki', 'pre'])

    def putSpacesInLists(self, text):
        """
        Add a space between the * or # and the text.

        NOTE: This space is recommended in the syntax help on the English,
        German, and French Wikipedia. It might be that it is not wanted on
        other wikis. If there are any complaints, please file a bug report.
        """
        if not self.template:
            exceptions = ['comment', 'math', 'nowiki', 'pre', 'source',
                          'template', 'timeline', self.site.redirectRegex()]
            text = textlib.replaceExcept(
                text,
                r'(?m)'
                r'^(?P<bullet>[:;]*(\*+|#+)[:;\*#]*)(?P<char>[^\s\*#:;].+?)',
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
                old, new = template
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
            if re.match(r'(?:' + '|'.join(list(self.site.namespaces[6])
                        + list(self.site.namespaces[14])) + '):',
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
        # See also
        # https://en.wikipedia.org/wiki/User:AnomieBOT/source/tasks/OrphanReferenceFixer.pm
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
                      'startspace', 'gallery', 'hyperlink', 'interwiki',
                      'link']
        # change <number> ccm -> <number> cm³
        text = textlib.replaceExcept(text, r'(\d)\s*(?:&nbsp;)?ccm',
                                     r'\1&nbsp;cm³', exceptions,
                                     site=self.site)
        # Solve wrong Nº sign with °C or °F
        # additional exception requested on fr-wiki for this stuff
        pattern = re.compile('«.*?»', re.UNICODE)
        exceptions.append(pattern)
        text = textlib.replaceExcept(text, r'(\d)\s*(?:&nbsp;)?[º°]([CF])',
                                     r'\1&nbsp;°\2', exceptions,
                                     site=self.site)
        text = textlib.replaceExcept(text, 'º([CF])', '°' + r'\1',
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
            'ckb': '٠١٢٣٤٥٦٧٨٩',
            'fa': '۰۱۲۳۴۵۶۷۸۹',
        }
        faChrs = 'ءاآأإئؤبپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیةيك' + digits['fa']
        new = digits.pop(self.site.code)
        # This only works if there are only two items in digits dict
        old = digits[list(digits.keys())[0]]
        # not to let bot edits in latin content
        exceptions.append(re.compile('[^%(fa)s] *?\"*? *?, *?[^%(fa)s]'
                                     % {'fa': faChrs}))
        text = textlib.replaceExcept(text, ',', '،', exceptions,
                                     site=self.site)
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
        # deactivated due to bug T57185
        for i in range(0, 10):
            text = textlib.replaceExcept(text, old[i], new[i], exceptions)
        # do not change digits in class, style and table params
        pattern = re.compile(r'\w+=(".+?"|\d+)', re.UNICODE)
        exceptions.append(pattern)
        # do not change digits inside html-tags
        pattern = re.compile('<[/]*?[^</]+?[/]*?>', re.UNICODE)
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

        [1]:
        https://commons.wikimedia.org/wiki/Commons:Tools/pywiki_file_description_cleanup
        """
        if self.site.sitename != 'commons:commons' or self.namespace == 6:
            return
        # section headers to {{int:}} versions
        exceptions = ['comment', 'includeonly', 'math', 'noinclude', 'nowiki',
                      'pre', 'source', 'ref', 'timeline']
        text = textlib.replaceExcept(text,
                                     r'([\r\n]|^)\=\= *Summary *\=\=',
                                     r'\1== {{int:filedesc}} ==',
                                     exceptions, True)
        text = textlib.replaceExcept(
            text,
            r'([\r\n])\=\= *\[\[Commons:Copyright tags\|Licensing\]\]: *\=\=',
            r'\1== {{int:license-header}} ==', exceptions, True)
        text = textlib.replaceExcept(
            text,
            r'([\r\n])'
            r'\=\= *(Licensing|License information|{{int:license}}) *\=\=',
            r'\1== {{int:license-header}} ==', exceptions, True)

        # frequent field values to {{int:}} versions
        text = textlib.replaceExcept(
            text,
            r'([\r\n]\|[Ss]ource *\= *)'
            r'(?:[Oo]wn work by uploader|[Oo]wn work|[Ee]igene [Aa]rbeit) *'
            r'([\r\n])',
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
            r'([\r\n]|^)\=\= *{{int:filedesc}} *\=\=(?:[\r\n ]*)\=\= *'
            r'{{int:filedesc}} *\=\=',
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
