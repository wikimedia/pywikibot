#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script adds a missing references section to pages.

It goes over multiple pages, searches for pages where <references />
is missing although a <ref> tag is present, and in that case adds a new
references section.

These command line parameters can be used to specify which pages to work on:

&params;

    -xml          Retrieve information from a local XML dump (pages-articles
                  or pages-meta-current, see https://download.wikimedia.org).
                  Argument can also be given as "-xml:filename".

    -namespace:n  Number or name of namespace to process. The parameter can be
                  used multiple times. It works in combination with all other
                  parameters, except for the -start parameter. If you e.g.
                  want to iterate over all categories starting at M, use
                  -start:Category:M.

    -always       Don't prompt you for each replacement.

    -quiet        Use this option to get less output

If neither a page title nor a page generator is given, it takes all pages from
the default maintenance category.

It is strongly recommended not to run this script over the entire article
namespace (using the -start) parameter, as that would consume too much
bandwidth. Instead, use the -xml parameter, or use another way to generate
a list of affected articles
"""
#
# (C) Pywikibot team, 2007-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import re

from functools import partial

import pywikibot

from pywikibot import i18n, pagegenerators, textlib, Bot
from pywikibot.pagegenerators import (
    XMLDumpPageGenerator,
)

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}

# References sections are usually placed before further reading / external
# link sections. This dictionary defines these sections, sorted by priority.
# For example, on an English wiki, the script would place the "References"
# section in front of the "Further reading" section, if that existed.
# Otherwise, it would try to put it in front of the "External links" section,
# or if that fails, the "See also" section, etc.
placeBeforeSections = {
    'ar': [              # no explicit policy on where to put the references
        u'وصلات خارجية',
        u'انظر أيضا',
        u'ملاحظات'
    ],
    'ca': [
        u'Bibliografia',
        u'Bibliografia complementària',
        u'Vegeu també',
        u'Enllaços externs',
        u'Enllaços',
    ],
    'cs': [
        u'Externí odkazy',
        u'Poznámky',
    ],
    'da': [              # no explicit policy on where to put the references
        u'Eksterne links'
    ],
    'de': [              # no explicit policy on where to put the references
        u'Literatur',
        u'Weblinks',
        u'Siehe auch',
        u'Weblink',      # bad, but common singular form of Weblinks
    ],
    'dsb': [
        u'Nožki',
    ],
    'en': [              # no explicit policy on where to put the references
        u'Further reading',
        u'External links',
        u'See also',
        u'Notes'
    ],
    'ru': [
        u'Ссылки',
        u'Литература',
    ],
    'eo': [
        u'Eksteraj ligiloj',
        u'Ekstera ligilo',
        u'Eksteraj ligoj',
        u'Ekstera ligo',
        u'Rete'
    ],
    'es': [
        u'Enlaces externos',
        u'Véase también',
        u'Notas',
    ],
    'fa': [
        u'پیوند به بیرون',
        u'پانویس',
        u'جستارهای وابسته'
    ],
    'fi': [
        u'Kirjallisuutta',
        u'Aiheesta muualla',
        u'Ulkoiset linkit',
        u'Linkkejä',
    ],
    'fr': [
        u'Liens externes',
        u'Lien externe',
        u'Voir aussi',
        u'Notes'
    ],
    'he': [
        u'ראו גם',
        u'לקריאה נוספת',
        u'קישורים חיצוניים',
        u'הערות שוליים',
    ],
    'hsb': [
        u'Nóžki',
    ],
    'hu': [
        u'Külső hivatkozások',
        u'Lásd még',
    ],
    'it': [
        u'Bibliografia',
        u'Voci correlate',
        u'Altri progetti',
        u'Collegamenti esterni',
        u'Vedi anche',
    ],
    'ja': [
        u'関連項目',
        u'参考文献',
        u'外部リンク',
    ],
    'ko': [              # no explicit policy on where to put the references
        u'외부 링크',
        u'외부링크',
        u'바깥 고리',
        u'바깥고리',
        u'바깥 링크',
        u'바깥링크'
        u'외부 고리',
        u'외부고리'
    ],
    'lt': [              # no explicit policy on where to put the references
        u'Nuorodos'
    ],
    'nl': [              # no explicit policy on where to put the references
        u'Literatuur',
        u'Zie ook',
        u'Externe verwijzingen',
        u'Externe verwijzing',
    ],
    'pdc': [
        u'Beweisunge',
        u'Quelle unn Literatur',
        u'Gwelle',
        u'Gwuelle',
        u'Auswenniche Gleecher',
        u'Gewebbgleecher',
        u'Guckt mol aa',
        u'Seh aa',
    ],
    'pl': [
        u'Źródła',
        u'Bibliografia',
        u'Zobacz też',
        u'Linki zewnętrzne',
    ],
    'pt': [
        u'Ligações externas',
        u'Veja também',
        u'Ver também',
        u'Notas',
    ],
    'sk': [
        u'Pozri aj',
    ],
    'sr': [
        'Даље читање',
        'Спољашње везе',
        'Види још',
        'Напомене',
    ],
    'szl': [
        u'Przipisy',
        u'Připisy',
    ],
    'th': [
        u'อ่านเพิ่มเติม',
        u'แหล่งข้อมูลอื่น',
        u'ดูเพิ่ม',
        u'หมายเหตุ',
    ],
    'zh': [
        u'外部链接',
        u'外部連结',
        u'外部連結',
        u'外部连接',
    ],
}

# Titles of sections where a reference tag would fit into.
# The first title should be the preferred one: It's the one that
# will be used when a new section has to be created.
referencesSections = {
    'ar': [             # not sure about which ones are preferred.
        u'مراجع',
        u'المراجع',
        u'مصادر',
        u'المصادر',
        u'مراجع ومصادر',
        u'مصادر ومراجع',
        u'المراجع والمصادر',
        u'المصادر والمراجع',
    ],
    'ca': [
        u'Referències',
    ],
    'cs': [
        u'Reference',
        u'Poznámky',
    ],
    'da': [
        u'Noter',
    ],
    'de': [             # see [[de:WP:REF]]
        u'Einzelnachweise',
        u'Anmerkungen',
        u'Belege',
        u'Endnoten',
        u'Fußnoten',
        u'Fuß-/Endnoten',
        u'Quellen',
        u'Quellenangaben',
    ],
    'dsb': [
        u'Nožki',
    ],
    'en': [             # not sure about which ones are preferred.
        u'References',
        u'Footnotes',
        u'Notes',
    ],
    'ru': [
        u'Примечания',
        u'Сноски',
        u'Источники',
    ],
    'eo': [
        u'Referencoj',
    ],
    'es': [
        u'Referencias',
        u'Notas',
    ],
    'fa': [
        u'منابع',
        u'منبع'
    ],
    'fi': [
        u'Lähteet',
        u'Viitteet',
    ],
    'fr': [             # [[fr:Aide:Note]]
        u'Notes et références',
        u'Références',
        u'References',
        'Notes',
        'Sources',
    ],
    'he': [
        u'הערות שוליים',
    ],
    'hsb': [
        u'Nóžki',
    ],
    'hu': [
        u'Források és jegyzetek',
        u'Források',
        u'Jegyzetek',
        u'Hivatkozások',
        u'Megjegyzések',
    ],
    'is': [
        u'Heimildir',
        u'Tilvísanir',
    ],
    'it': [
        u'Note',
        u'Riferimenti',
    ],
    'ja': [
        u'脚注',
        u'脚注欄',
        u'脚注・出典',
        u'出典',
        u'注釈',
        u'註',
    ],
    'ko': [
        u'주석',
        u'각주'
        u'주석 및 참고 자료'
        u'주석 및 참고자료',
        u'주석 및 참고 출처'
    ],
    'lt': [             # not sure about which ones are preferred.
        u'Šaltiniai',
        u'Literatūra',
    ],
    'nl': [             # not sure about which ones are preferred.
        u'Voetnoten',
        u'Voetnoot',
        u'Referenties',
        u'Noten',
        u'Bronvermelding',
    ],
    'pdc': [
        u'Aamarrickunge',
    ],
    'pl': [
        u'Przypisy',
        u'Uwagi',
    ],
    'pt': [
        u'Referências',
    ],
    'sk': [
        u'Referencie',
    ],
    'sr': [
        'Референце',
    ],
    'szl': [
        u'Przipisy',
        u'Připisy',
    ],
    'th': [
        u'อ้างอิง',
        u'เชิงอรรถ',
        u'หมายเหตุ',
    ],
    'zh': [
        u'參考資料',
        u'参考资料',
        u'參考文獻',
        u'参考文献',
        u'資料來源',
        u'资料来源',
    ],
}

# Templates which include a <references /> tag. If there is no such template
# on your wiki, you don't have to enter anything here.
referencesTemplates = {
    'wikipedia': {
        'ar': ['Reflist', 'مراجع', 'ثبت المراجع', 'ثبت_المراجع',
               'بداية المراجع', 'نهاية المراجع', 'المراجع'],
        'be': [u'Зноскі', u'Примечания', u'Reflist', u'Спіс заўваг',
               u'Заўвагі'],
        'be-tarask': [u'Зноскі'],
        'ca': [u'Referències', u'Reflist', u'Listaref', u'Referència',
               u'Referencies', u'Referències2',
               u'Amaga', u'Amaga ref', u'Amaga Ref', u'Amaga Ref2', u'Apèndix'],
        'da': [u'Reflist'],
        'dsb': [u'Referency'],
        'en': [u'Reflist', u'Refs', u'FootnotesSmall', u'Reference',
               u'Ref-list', u'Reference list', u'References-small', u'Reflink',
               u'Footnotes', u'FootnotesSmall'],
        'eo': [u'Referencoj'],
        'es': ['Listaref', 'Reflist', 'muchasref'],
        'fa': [u'Reflist', u'Refs', u'FootnotesSmall', u'Reference',
               u'پانویس', u'پانویس‌ها ', u'پانویس ۲', u'پانویس۲',
               u'فهرست منابع'],
        'fi': [u'Viitteet', u'Reflist'],
        'fr': [u'Références', u'Notes', u'References', u'Reflist'],
        'he': [u'הערות שוליים', u'הערה'],
        'hsb': [u'Referency'],
        'hu': [u'reflist', u'források', u'references', u'megjegyzések'],
        'is': [u'reflist'],
        'it': [u'References'],
        'ja': [u'Reflist', u'脚注リスト'],
        'ko': [u'주석', u'Reflist'],
        'lt': [u'Reflist', u'Ref', u'Litref'],
        'nl': [u'Reflist', u'Refs', u'FootnotesSmall', u'Reference',
               u'Ref-list', u'Reference list', u'References-small', u'Reflink',
               u'Referenties', u'Bron', u'Bronnen/noten/referenties', u'Bron2',
               u'Bron3', u'ref', u'references', u'appendix',
               u'Noot', u'FootnotesSmall'],
        'pl': [u'Przypisy', u'Przypisy-lista', u'Uwagi'],
        'pt': [u'Notas', u'ref-section', u'Referências', u'Reflist'],
        'ru': [u'Reflist', u'Ref-list', u'Refs', u'Sources',
               u'Примечания', u'Список примечаний',
               u'Сноска', u'Сноски'],
        'sr': ['Reflist'],
        'szl': [u'Przipisy', u'Připisy'],
        'th': [u'รายการอ้างอิง'],
        'zh': [u'Reflist', u'RefFoot', u'NoteFoot'],
    },
}

# Text to be added instead of the <references /> tag.
# Define this only if required by your wiki.
referencesSubstitute = {
    'wikipedia': {
        'ar': u'{{مراجع}}',
        'be': u'{{зноскі}}',
        'da': u'{{reflist}}',
        'dsb': u'{{referency}}',
        'fa': u'{{پانویس}}',
        'fi': u'{{viitteet}}',
        'fr': u'{{références}}',
        'he': u'{{הערות שוליים}}',
        'hsb': u'{{referency}}',
        'hu': u'{{Források}}',
        'pl': u'{{Przypisy}}',
        'ru': u'{{примечания}}',
        'sr': '{{reflist}}',
        'szl': u'{{Przipisy}}',
        'th': u'{{รายการอ้างอิง}}',
        'zh': u'{{reflist}}',
    },
}

# Sites where no title is required for references template
# as it is already included there
# like pl.wiki where {{Przypisy}} generates
# == Przypisy ==
# <references />
noTitleRequired = [u'pl', u'be', u'szl']

maintenance_category = 'cite_error_refs_without_references_category'

_ref_regex = re.compile('</ref>', re.IGNORECASE)
_references_regex = re.compile('<references.*?/>', re.IGNORECASE)


def _match_xml_page_text(text):
    """Match page text."""
    text = textlib.removeDisabledParts(text)
    return _ref_regex.search(text) and not _references_regex.search(text)


XmlDumpNoReferencesPageGenerator = partial(
    XMLDumpPageGenerator, text_predicate=_match_xml_page_text)


class NoReferencesBot(Bot):

    """References section bot."""

    def __init__(self, generator, **kwargs):
        """Constructor."""
        self.availableOptions.update({
            'verbose': True,
        })
        super(NoReferencesBot, self).__init__(**kwargs)

        self.generator = pagegenerators.PreloadingGenerator(generator)
        self.site = pywikibot.Site()
        self.comment = i18n.twtranslate(self.site, 'noreferences-add-tag')

        self.refR = _ref_regex
        self.referencesR = _references_regex
        self.referencesTagR = re.compile('<references>.*?</references>',
                                         re.IGNORECASE | re.DOTALL)
        try:
            self.referencesTemplates = referencesTemplates[
                self.site.family.name][self.site.code]
        except KeyError:
            self.referencesTemplates = []
        try:
            self.referencesText = referencesSubstitute[
                self.site.family.name][self.site.code]
        except KeyError:
            self.referencesText = u'<references />'

    def lacksReferences(self, text):
        """Check whether or not the page is lacking a references tag."""
        oldTextCleaned = textlib.removeDisabledParts(text)
        if self.referencesR.search(oldTextCleaned) or \
           self.referencesTagR.search(oldTextCleaned):
            if self.getOption('verbose'):
                pywikibot.output(u'No changes necessary: references tag found.')
            return False
        elif self.referencesTemplates:
            templateR = u'{{(' + u'|'.join(self.referencesTemplates) + ')'
            if re.search(templateR, oldTextCleaned, re.IGNORECASE | re.UNICODE):
                if self.getOption('verbose'):
                    pywikibot.output(
                        u'No changes necessary: references template found.')
                return False
        if not self.refR.search(oldTextCleaned):
            if self.getOption('verbose'):
                pywikibot.output(u'No changes necessary: no ref tags found.')
            return False
        else:
            if self.getOption('verbose'):
                pywikibot.output(u'Found ref without references.')
            return True

    def addReferences(self, oldText):
        """
        Add a references tag into an existing section where it fits into.

        If there is no such section, creates a new section containing
        the references tag.
        * Returns : The modified pagetext

        """
        # Do we have a malformed <reference> tag which could be repaired?

        # Repair two opening tags or a opening and an empty tag
        pattern = re.compile(r'< *references *>(.*?)'
                             r'< */?\s*references */? *>', re.DOTALL)
        if pattern.search(oldText):
            pywikibot.output('Repairing references tag')
            return re.sub(pattern, r'<references>\1</references>', oldText)
        # Repair single unclosed references tag
        pattern = re.compile(r'< *references *>')
        if pattern.search(oldText):
            pywikibot.output('Repairing references tag')
            return re.sub(pattern, '<references />', oldText)

        # Is there an existing section where we can add the references tag?
        for section in i18n.translate(self.site, referencesSections):
            sectionR = re.compile(r'\r?\n=+ *%s *=+ *\r?\n' % section)
            index = 0
            while index < len(oldText):
                match = sectionR.search(oldText, index)
                if match:
                    if textlib.isDisabled(oldText, match.start()):
                        pywikibot.output(
                            'Existing %s section is commented out, skipping.'
                            % section)
                        index = match.end()
                    else:
                        pywikibot.output(
                            'Adding references tag to existing %s section...\n'
                            % section)
                        newText = (
                            oldText[:match.end()] + u'\n' +
                            self.referencesText + u'\n' +
                            oldText[match.end():]
                        )
                        return newText
                else:
                    break

        # Create a new section for the references tag
        for section in i18n.translate(self.site, placeBeforeSections):
            # Find out where to place the new section
            sectionR = re.compile(r'\r?\n(?P<ident>=+) *%s *(?P=ident) *\r?\n'
                                  % section)
            index = 0
            while index < len(oldText):
                match = sectionR.search(oldText, index)
                if match:
                    if textlib.isDisabled(oldText, match.start()):
                        pywikibot.output(
                            'Existing %s section is commented out, won\'t add '
                            'the references in front of it.' % section)
                        index = match.end()
                    else:
                        pywikibot.output(
                            u'Adding references section before %s section...\n'
                            % section)
                        index = match.start()
                        ident = match.group('ident')
                        return self.createReferenceSection(oldText, index,
                                                           ident)
                else:
                    break
        # This gets complicated: we want to place the new references
        # section over the interwiki links and categories, but also
        # over all navigation bars, persondata, and other templates
        # that are at the bottom of the page. So we need some advanced
        # regex magic.
        # The strategy is: create a temporary copy of the text. From that,
        # keep removing interwiki links, templates etc. from the bottom.
        # At the end, look at the length of the temp text. That's the position
        # where we'll insert the references section.
        catNamespaces = '|'.join(self.site.namespaces.CATEGORY)
        categoryPattern = r'\[\[\s*(%s)\s*:[^\n]*\]\]\s*' % catNamespaces
        interwikiPattern = r'\[\[([a-zA-Z\-]+)\s?:([^\[\]\n]*)\]\]\s*'
        # won't work with nested templates
        # the negative lookahead assures that we'll match the last template
        # occurrence in the temp text.
        # FIXME:
        # {{commons}} or {{commonscat}} are part of Weblinks section
        # * {{template}} is mostly part of a section
        # so templatePattern must be fixed
        templatePattern = r'\r?\n{{((?!}}).)+?}}\s*'
        commentPattern = r'<!--((?!-->).)*?-->\s*'
        metadataR = re.compile(r'(\r?\n)?(%s|%s|%s|%s)$'
                               % (categoryPattern, interwikiPattern,
                                  templatePattern, commentPattern), re.DOTALL)
        tmpText = oldText
        while True:
            match = metadataR.search(tmpText)
            if match:
                tmpText = tmpText[:match.start()]
            else:
                break
        pywikibot.output(
            u'Found no section that can be preceeded by a new references '
            u'section.\nPlacing it before interwiki links, categories, and '
            u'bottom templates.')
        index = len(tmpText)
        return self.createReferenceSection(oldText, index)

    def createReferenceSection(self, oldText, index, ident='=='):
        """Create a reference section and insert it into the given text."""
        if self.site.code in noTitleRequired:
            newSection = u'\n%s\n' % (self.referencesText)
        else:
            newSection = u'\n%s %s %s\n%s\n' % (ident,
                                                i18n.translate(
                                                    self.site,
                                                    referencesSections)[0],
                                                ident, self.referencesText)
        return oldText[:index] + newSection + oldText[index:]

    def run(self):
        """Run the bot."""
        for page in self.generator:
            self.current_page = page
            try:
                text = page.text
            except pywikibot.NoPage:
                pywikibot.warning('Page %s does not exist?!'
                                  % page.title(asLink=True))
                continue
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"Page %s is a redirect; skipping."
                                 % page.title(asLink=True))
                continue
            except pywikibot.LockedPage:
                pywikibot.warning('Page %s is locked?!'
                                  % page.title(asLink=True))
                continue
            if page.isDisambig():
                pywikibot.output(u"Page %s is a disambig; skipping."
                                 % page.title(asLink=True))
                continue
            if self.site.sitename == 'wikipedia:en' and page.isIpEdit():
                pywikibot.warning(
                    u"Page %s is edited by IP. Possible vandalized"
                    % page.title(asLink=True))
                continue
            if self.lacksReferences(text):
                newText = self.addReferences(text)
                try:
                    self.userPut(page, page.text, newText, summary=self.comment)
                except pywikibot.EditConflict:
                    pywikibot.warning('Skipping %s because of edit conflict'
                                      % page.title(asLink=True))
                except pywikibot.SpamfilterError as e:
                    pywikibot.warning(
                        u'Cannot change %s because of blacklist entry %s'
                        % (page.title(asLink=True), e.url))
                except pywikibot.LockedPage:
                    pywikibot.warning('Skipping %s (locked page)' %
                                      page.title(asLink=True))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    options = {}

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg.startswith('-xml'):
            if len(arg) == 4:
                xmlFilename = i18n.input('pywikibot-enter-xml-filename')
            else:
                xmlFilename = arg[5:]
            genFactory.gens.append(XmlDumpNoReferencesPageGenerator(xmlFilename))
        elif arg == '-always':
            options['always'] = True
        elif arg == '-quiet':
            options['verbose'] = False
        else:
            genFactory.handleArg(arg)

    gen = genFactory.getCombinedGenerator()
    if not gen:
        site = pywikibot.Site()
        try:
            cat = site.expand_text(
                site.mediawiki_message(maintenance_category))
        except:
            pass
        else:
            cat = pywikibot.Category(site, "%s:%s" % (
                site.namespaces.CATEGORY, cat))
            gen = cat.articles(namespaces=genFactory.namespaces or [0])
    if gen:
        bot = NoReferencesBot(gen, **options)
        bot.run()
        return True
    else:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False


if __name__ == "__main__":
    main()
