#!/usr/bin/env python3
"""
This script adds a missing references section to pages.

It goes over multiple pages, searches for pages where <references />
is missing although a <ref> tag is present, and in that case adds a new
references section.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-xml          Retrieve information from a local XML dump (pages-articles
              or pages-meta-current, see https://dumps.wikimedia.org).
              Argument can also be given as "-xml:filename".

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
# (C) Pywikibot team, 2007-2022
#
# Distributed under the terms of the MIT license.
#
import re
from functools import partial

import pywikibot
from pywikibot import i18n, pagegenerators, textlib
from pywikibot.bot import ExistingPageBot, SingleSiteBot
from pywikibot.exceptions import LockedPageError
from pywikibot.pagegenerators import XMLDumpPageGenerator


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
        'وصلات خارجية',
        'انظر أيضا',
        'ملاحظات'
    ],
    'arz': [              # no explicit policy on where to put the references
        'لينكات برانيه',
        'لينكات',
        'شوف كمان'
    ],
    'ca': [
        'Bibliografia',
        'Bibliografia complementària',
        'Vegeu també',
        'Enllaços externs',
        'Enllaços',
    ],
    'cs': [
        'Externí odkazy',
        'Poznámky',
    ],
    'da': [              # no explicit policy on where to put the references
        'Eksterne links'
    ],
    'de': [              # no explicit policy on where to put the references
        'Literatur',
        'Weblinks',
        'Siehe auch',
        'Weblink',      # bad, but common singular form of Weblinks
    ],
    'dsb': [
        'Nožki',
    ],
    'en': [              # no explicit policy on where to put the references
        'Further reading',
        'External links',
        'See also',
        'Notes'
    ],
    'eo': [
        'Eksteraj ligiloj',
        'Ekstera ligilo',
        'Eksteraj ligoj',
        'Ekstera ligo',
        'Rete'
    ],
    'es': [
        'Enlaces externos',
        'Véase también',
        'Notas',
    ],
    'fa': [
        'پیوند به بیرون',
        'پانویس',
        'جستارهای وابسته'
    ],
    'fi': [
        'Kirjallisuutta',
        'Aiheesta muualla',
        'Ulkoiset linkit',
        'Linkkejä',
    ],
    'fr': [
        'Liens externes',
        'Lien externe',
        'Voir aussi',
        'Notes'
    ],
    'he': [
        'ראו גם',
        'לקריאה נוספת',
        'קישורים חיצוניים',
        'הערות שוליים',
    ],
    'hsb': [
        'Nóžki',
    ],
    'hu': [
        'Külső hivatkozások',
        'Lásd még',
    ],
    'it': [
        'Bibliografia',
        'Voci correlate',
        'Altri progetti',
        'Collegamenti esterni',
        'Vedi anche',
    ],
    'ja': [
        '関連項目',
        '参考文献',
        '外部リンク',
    ],
    'ko': [              # no explicit policy on where to put the references
        '외부 링크',
        '외부링크',
        '바깥 고리',
        '바깥고리',
        '바깥 링크',
        '바깥링크'
        '외부 고리',
        '외부고리'
    ],
    'lt': [              # no explicit policy on where to put the references
        'Nuorodos'
    ],
    'nl': [              # no explicit policy on where to put the references
        'Literatuur',
        'Zie ook',
        'Externe verwijzingen',
        'Externe verwijzing',
    ],
    'pdc': [
        'Beweisunge',
        'Quelle unn Literatur',
        'Gwelle',
        'Gwuelle',
        'Auswenniche Gleecher',
        'Gewebbgleecher',
        'Guckt mol aa',
        'Seh aa',
    ],
    'pl': [
        'Źródła',
        'Bibliografia',
        'Zobacz też',
        'Linki zewnętrzne',
    ],
    'pt': [
        'Ligações externas',
        'Veja também',
        'Ver também',
        'Notas',
    ],
    'ru': [
        'Ссылки',
        'Литература',
    ],
    'sd': [
        'وڌيڪ ڏسو',
        'حوالا',
        'خارجي ڳنڌڻا',
    ],
    'sk': [
        'Pozri aj',
    ],
    'sr': [
        'Даље читање',
        'Спољашње везе',
        'Види још',
        'Напомене',
        'Литература',
    ],
    'szl': [
        'Przipisy',
        'Připisy',
    ],
    'th': [
        'อ่านเพิ่มเติม',
        'แหล่งข้อมูลอื่น',
        'ดูเพิ่ม',
        'หมายเหตุ',
    ],
    'ur': [              # no explicit policy on where to put the references
        'مزید دیکھیے',
        'حوالہ جات',
        'بیرونی روابط',
    ],
    'zh': [
        '外部链接',
        '外部連结',
        '外部連結',
        '外部连接',
    ],
}

# Titles of sections where a reference tag would fit into.
# The first title should be the preferred one: It's the one that will be
# used when a new section has to be created. Section titles can be regex
# patterns except of the first.
referencesSections = {
    'wikipedia': {
        'ar': [             # not sure about which ones are preferred.
            'مراجع',
            'المراجع',
            'مصادر',
            'المصادر',
            'مراجع ومصادر',
            'مصادر ومراجع',
            'المراجع والمصادر',
            'المصادر والمراجع',
        ],
        'ary': [
            'لمصادر',
            'مصادر',
        ],
        'arz': [
            'مراجع',
            'المراجع',
            'مصادر',
            'المصادر',
        ],
        'ca': [
            'Referències',
        ],
        'cs': [
            'Reference',
            'Poznámky',
        ],
        'da': [
            'Noter',
        ],
        'de': [             # see [[de:WP:REF]]
            'Einzelnachweise',
            'Anmerkungen',
            'Belege',
            'Endnoten',
            'Fußnoten',
            'Fuß-/Endnoten',
            'Quellen',
            'Quellenangaben',
        ],
        'dsb': [
            'Nožki',
        ],
        'en': [             # not sure about which ones are preferred.
            'References',
            'Footnotes',
            'Notes',
        ],
        'ru': [
            'Примечания',
            'Сноски',
            'Источники',
        ],
        'eo': [
            'Referencoj',
        ],
        'es': [
            'Referencias',
            'Notas',
        ],
        'fa': [
            'منابع',
            'منبع'
        ],
        'fi': [
            'Lähteet',
            'Viitteet',
        ],
        'fr': [             # [[fr:Aide:Note]]
            'Notes et références',
            'Notes? et r[ée]f[ée]rences?',
            'R[ée]f[ée]rences?',
            'Notes?',
            'Sources?',
        ],
        'he': [
            'הערות שוליים',
        ],
        'hsb': [
            'Nóžki',
        ],
        'hu': [
            'Források és jegyzetek',
            'Források',
            'Jegyzetek',
            'Hivatkozások',
            'Megjegyzések',
        ],
        'is': [
            'Heimildir',
            'Tilvísanir',
        ],
        'it': [
            'Note',
            'Riferimenti',
        ],
        'ja': [
            '脚注',
            '脚注欄',
            '脚注・出典',
            '出典',
            '注釈',
            '註',
        ],
        'ko': [
            '주석',
            '각주'
            '주석 및 참고 자료'
            '주석 및 참고자료',
            '주석 및 참고 출처'
        ],
        'lt': [             # not sure about which ones are preferred.
            'Šaltiniai',
            'Literatūra',
        ],
        'nl': [             # not sure about which ones are preferred.
            'Voetnoten',
            'Voetnoot',
            'Referenties',
            'Noten',
            'Bronvermelding',
        ],
        'pdc': [
            'Aamarrickunge',
        ],
        'pl': [
            'Przypisy',
            'Uwagi',
        ],
        'pt': [
            'Referências',
        ],
        'sd': [
            'حوالا',
        ],
        'sk': [
            'Referencie',
        ],
        'sr': [
            'Референце',
            'Извори',
        ],
        'szl': [
            'Przipisy',
            'Připisy',
        ],
        'th': [
            'อ้างอิง',
            'เชิงอรรถ',
            'หมายเหตุ',
        ],
        'ur': [
            'حوالہ جات',
            'حوالہ',
        ],
        'zh': [
            '參考資料',
            '参考资料',
            '參考文獻',
            '参考文献',
            '資料來源',
            '资料来源',
        ],
    },
}
# Header on Czech Wiktionary should be different (T123091)
referencesSections['wiktionary'] = dict(referencesSections['wikipedia'])
referencesSections['wiktionary'].update(cs=['poznámky', 'reference'])

# Templates which include a <references /> tag. If there is no such template
# on your wiki, you don't have to enter anything here.
referencesTemplates = {
    'wikipedia': {
        'ar': ['مراجع', 'المراجع', 'ثبت المراجع',
               'ثبت المصادر', 'قائمة مصادر', 'Reflist'],
        'ary': ['مراجع', 'المراجع', 'المصادر',
                'Reflist', 'Refs'],
        'arz': ['مصادر', 'مراجع', 'المراجع', 'ثبت المراجع',
                'Reflist', 'Refs'],
        'be': ['Зноскі', 'Примечания', 'Reflist', 'Спіс заўваг',
               'Заўвагі'],
        'be-tarask': ['Зноскі'],
        'ca': ['Referències', 'Reflist', 'Listaref', 'Referència',
               'Referencies', 'Referències2',
               'Amaga', 'Amaga ref', 'Amaga Ref', 'Amaga Ref2', 'Apèndix'],
        'da': ['Reflist'],
        'dsb': ['Referency'],
        'en': ['Reflist', 'Refs', 'FootnotesSmall', 'Reference',
               'Ref-list', 'Reference list', 'References-small', 'Reflink',
               'Footnotes', 'FootnotesSmall'],
        'eo': ['Referencoj'],
        'es': ['Listaref', 'Reflist', 'muchasref'],
        'fa': ['Reflist', 'Refs', 'FootnotesSmall', 'Reference',
               'پانویس', 'پانویس‌ها ', 'پانویس ۲', 'پانویس۲',
               'فهرست منابع'],
        'fi': ['Viitteet', 'Reflist'],
        'fr': ['Références', 'Notes', 'References', 'Reflist'],
        'he': ['הערות שוליים', 'הערה'],
        'hsb': ['Referency'],
        'hu': ['reflist', 'források', 'references', 'megjegyzések'],
        'is': ['reflist'],
        'it': ['References'],
        'ja': ['Reflist', '脚注リスト'],
        'ko': ['주석', 'Reflist'],
        'lt': ['Reflist', 'Ref', 'Litref'],
        'nl': ['Reflist', 'Refs', 'FootnotesSmall', 'Reference',
               'Ref-list', 'Reference list', 'References-small', 'Reflink',
               'Referenties', 'Bron', 'Bronnen/noten/referenties', 'Bron2',
               'Bron3', 'ref', 'references', 'appendix',
               'Noot', 'FootnotesSmall'],
        'pl': ['Przypisy', 'Przypisy-lista', 'Uwagi'],
        'pt': ['Notas', 'ref-section', 'Referências', 'Reflist'],
        'ru': ['Reflist', 'Ref-list', 'Refs', 'Sources',
               'Примечания', 'Список примечаний',
               'Сноска', 'Сноски'],
        'sd': ['Reflist', 'Refs', 'Reference',
               'حوالا'],
        'sr': ['Reflist', 'Референце', 'Извори', 'Рефлист'],
        'szl': ['Przipisy', 'Připisy'],
        'th': ['รายการอ้างอิง'],
        'ur': ['Reflist', 'Refs', 'Reference',
               'حوالہ جات', 'حوالے'],
        'zh': ['Reflist', 'RefFoot', 'NoteFoot'],
    },
}

# Text to be added instead of the <references /> tag.
# Define this only if required by your wiki.
referencesSubstitute = {
    'wikipedia': {
        'ar': '{{مراجع}}',
        'ary': '{{مراجع}}',
        'arz': '{{مصادر}}',
        'be': '{{зноскі}}',
        'da': '{{reflist}}',
        'dsb': '{{referency}}',
        'fa': '{{پانویس}}',
        'fi': '{{viitteet}}',
        'fr': '{{références}}',
        'he': '{{הערות שוליים}}',
        'hsb': '{{referency}}',
        'hu': '{{Források}}',
        'pl': '{{Przypisy}}',
        'ru': '{{примечания}}',
        'sd': '{{حوالا}}',
        'sr': '{{reflist}}',
        'szl': '{{Przipisy}}',
        'th': '{{รายการอ้างอิง}}',
        'ur': '{{حوالہ جات}}',
        'zh': '{{reflist}}',
    },
}

# Sites where no title is required for references template
# as it is already included there
noTitleRequired = ['be', 'szl']

maintenance_category = 'Q6483427'

_ref_regex = re.compile('</ref>', re.IGNORECASE)
_references_regex = re.compile('<references.*?/>', re.IGNORECASE)


def _match_xml_page_text(text) -> bool:
    """Match page text."""
    text = textlib.removeDisabledParts(text)
    return _ref_regex.search(text) and not _references_regex.search(text)


XmlDumpNoReferencesPageGenerator = partial(
    XMLDumpPageGenerator, text_predicate=_match_xml_page_text)


class NoReferencesBot(SingleSiteBot, ExistingPageBot):

    """References section bot."""

    use_disambigs = False
    use_redirects = False

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        self.available_options.update({
            'verbose': True,
        })
        super().__init__(**kwargs)

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
            self.referencesText = '<references />'

    def lacksReferences(self, text) -> bool:
        """Check whether or not the page is lacking a references tag."""
        oldTextCleaned = textlib.removeDisabledParts(text)
        if self.referencesR.search(oldTextCleaned) \
           or self.referencesTagR.search(oldTextCleaned):
            if self.opt.verbose:
                pywikibot.info('No changes necessary: references tag found.')
            return False

        if self.referencesTemplates:
            templateR = '{{(' + '|'.join(self.referencesTemplates) + ')'
            if re.search(templateR, oldTextCleaned, re.IGNORECASE):
                if self.opt.verbose:
                    pywikibot.info(
                        'No changes necessary: references template found.')
                return False

        if not self.refR.search(oldTextCleaned):
            if self.opt.verbose:
                pywikibot.info('No changes necessary: no ref tags found.')
            return False

        if self.opt.verbose:
            pywikibot.info('Found ref without references.')
        return True

    def addReferences(self, oldText) -> str:
        """
        Add a references tag into an existing section where it fits into.

        If there is no such section, creates a new section containing
        the references tag. Also repair malformed references tags.
        Set the edit summary accordingly.

        :param oldText: page text to be modified
        :type oldText: str
        :return: The modified pagetext
        """
        # Do we have a malformed <reference> tag which could be repaired?
        # Set the edit summary for this case
        self.comment = i18n.twtranslate(self.site, 'noreferences-fix-tag')

        # Repair two opening tags or an opening and an empty tag
        pattern = re.compile(r'< *references *>(.*?)'
                             r'< */?\s*references */? *>', re.DOTALL)
        if pattern.search(oldText):
            pywikibot.info('Repairing references tag')
            return re.sub(pattern, r'<references>\1</references>', oldText)
        # Repair single unclosed references tag
        pattern = re.compile(r'< *references *>')
        if pattern.search(oldText):
            pywikibot.info('Repairing references tag')
            return re.sub(pattern, '<references />', oldText)

        # Is there an existing section where we can add the references tag?
        # Set the edit summary for this case
        self.comment = i18n.twtranslate(self.site, 'noreferences-add-tag')
        for section in i18n.translate(self.site, referencesSections):
            sectionR = re.compile(fr'\r?\n=+ *{section} *=+ *\r?\n')
            index = 0
            while index < len(oldText):
                match = sectionR.search(oldText, index)
                if match:
                    if textlib.isDisabled(oldText, match.start()):
                        pywikibot.info(f'Existing {section} section is '
                                       f'commented out, skipping.')
                        index = match.end()
                    else:
                        pywikibot.info(f'Adding references tag to existing'
                                       f'{section} section...\n')
                        templates_or_comments = re.compile(
                            r'^((?:\s*(?:\{\{[^\{\}]*?\}\}|<!--.*?-->))*)',
                            flags=re.DOTALL)
                        new_text = (
                            oldText[:match.end() - 1]
                            + templates_or_comments.sub(
                                fr'\1\n{self.referencesText}\n',
                                oldText[match.end() - 1:]))
                        return new_text
                else:
                    break

        # Create a new section for the references tag
        for section in i18n.translate(self.site, placeBeforeSections):
            # Find out where to place the new section
            sectionR = re.compile(r'\r?\n(?P<ident>=+) *{} *(?P=ident) *\r?\n'
                                  .format(section))
            index = 0
            while index < len(oldText):
                match = sectionR.search(oldText, index)
                if match:
                    if textlib.isDisabled(oldText, match.start()):
                        pywikibot.info(
                            'Existing {} section is commented out, '
                            "won't add the references in front of it."
                            .format(section))
                        index = match.end()
                    else:
                        pywikibot.info(
                            'Adding references section before {} section...\n'
                            .format(section))
                        index = match.start()
                        ident = match['ident']
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
        categoryPattern = fr'\[\[\s*({catNamespaces})\s*:[^\n]*\]\]\s*'
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
        metadataR = re.compile(r'(\r?\n)?({}|{}|{}|{})$'
                               .format(categoryPattern, interwikiPattern,
                                       templatePattern, commentPattern),
                               re.DOTALL)
        tmpText = oldText
        while True:
            match = metadataR.search(tmpText)
            if match:
                tmpText = tmpText[:match.start()]
            else:
                break
        pywikibot.info(
            'Found no section that can be preceded by a new references '
            'section.\nPlacing it before interwiki links, categories, and '
            'bottom templates.')
        index = len(tmpText)
        return self.createReferenceSection(oldText, index)

    def createReferenceSection(self, oldText, index, ident: str = '==') -> str:
        """Create a reference section and insert it into the given text.

        :param oldText: page text that is going to be be amended
        :type oldText: str
        :param index: the index of oldText where the reference section should
            be inserted at
        :type index: int
        :param ident: symbols to be inserted before and after reference section
            title
        :return: the amended page text with reference section added
        """
        if self.site.code in noTitleRequired:
            ref_section = f'\n\n{self.referencesText}\n'
        else:
            ref_section = '\n\n{ident} {title} {ident}\n{text}\n'.format(
                title=i18n.translate(self.site, referencesSections)[0],
                ident=ident, text=self.referencesText)
        return oldText[:index].rstrip() + ref_section + oldText[index:]

    def skip_page(self, page):
        """Check whether the page could be processed."""
        if super().skip_page(page):
            return True

        if self.site.sitename == 'wikipedia:en' and page.isIpEdit():
            pywikibot.warning(
                'Page {} is edited by IP. Possible vandalized'
                .format(page.title(as_link=True)))
            return True

        return False

    def treat_page(self) -> None:
        """Run the bot."""
        page = self.current_page
        try:
            text = page.text
        except LockedPageError:
            pywikibot.warning('Page {} is locked?!'
                              .format(page.title(as_link=True)))
            return

        if self.lacksReferences(text):
            self.put_current(self.addReferences(text), summary=self.comment)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}
    gen = None

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        opt, _, value = arg.partition(':')
        if opt == '-xml':
            xmlFilename = value or i18n.input('pywikibot-enter-xml-filename')
            gen = XmlDumpNoReferencesPageGenerator(xmlFilename)
        elif opt == '-always':
            options['always'] = True
        elif opt == '-quiet':
            options['verbose'] = False
        else:
            genFactory.handle_arg(arg)

    gen = genFactory.getCombinedGenerator(gen, preload=True)
    if not gen:
        site = pywikibot.Site()
        cat = site.page_from_repository(maintenance_category)
        if cat:
            gen = cat.articles(namespaces=genFactory.namespaces or [0])

    if gen:
        bot = NoReferencesBot(generator=gen, **options)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
