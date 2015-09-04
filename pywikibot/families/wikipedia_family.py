# -*- coding: utf-8  -*-
"""Family module for Wikipedia."""
from __future__ import unicode_literals

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikipedia, the Free Encyclopedia
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family module for Wikipedia."""

    name = 'wikipedia'

    closed_wikis = [
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Afar_Wikipedia
        'aa',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Choctaw_Wikipedia
        'cho',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Hiri_Motu_Wikipedia
        'ho',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Herero_Wikipedia
        'hz',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Yi_Wikipedia
        'ii',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kwanyama_Wikipedia
        'kj',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kanuri_Wikipedia
        'kr',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Marshallese_Wikipedia
        'mh',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Moldovan_Wikipedia
        'mo',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Muscogee_Wikipedia
        'mus',
    ]

    removed_wikis = [
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Ndonga_Wikipedia
        'ng',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Siberian_Wikipedia
        'ru-sib',
        # Klingon, locked in 2005, and moved to http://klingon.wikia.com/
        'tlh',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tokipona_Wikipedia
        'tokipona',
    ]

    def __init__(self):
        """Constructor."""
        self.languages_by_size = [
            'en', 'sv', 'nl', 'de', 'fr', 'war', 'ru', 'ceb', 'it', 'es', 'vi',
            'pl', 'ja', 'pt', 'zh', 'uk', 'ca', 'fa', 'no', 'sh', 'fi', 'ar',
            'id', 'cs', 'sr', 'ro', 'ko', 'hu', 'ms', 'tr', 'min', 'eo', 'kk',
            'eu', 'sk', 'da', 'bg', 'he', 'lt', 'hy', 'hr', 'sl', 'et', 'uz',
            'gl', 'nn', 'vo', 'la', 'simple', 'el', 'hi', 'az', 'th', 'ka',
            'ce', 'oc', 'be', 'mk', 'mg', 'new', 'ur', 'tt', 'ta', 'pms', 'cy',
            'tl', 'lv', 'bs', 'te', 'be-x-old', 'br', 'ht', 'sq', 'jv', 'lb',
            'mr', 'is', 'ml', 'zh-yue', 'bn', 'af', 'ba', 'ga', 'pnb', 'cv',
            'fy', 'lmo', 'tg', 'sco', 'my', 'yo', 'an', 'ky', 'sw', 'io', 'ne',
            'gu', 'scn', 'bpy', 'nds', 'ku', 'ast', 'qu', 'als', 'su', 'pa',
            'kn', 'ckb', 'ia', 'mn', 'nap', 'bug', 'arz', 'bat-smg', 'wa',
            'zh-min-nan', 'am', 'map-bms', 'gd', 'yi', 'mzn', 'si', 'fo', 'bar',
            'vec', 'nah', 'sah', 'os', 'sa', 'roa-tara', 'li', 'hsb', 'or',
            'pam', 'mrj', 'mhr', 'se', 'mi', 'ilo', 'hif', 'bcl', 'gan', 'rue',
            'ps', 'glk', 'nds-nl', 'bo', 'vls', 'diq', 'fiu-vro', 'bh', 'xmf',
            'tk', 'gv', 'sc', 'co', 'csb', 'hak', 'km', 'kv', 'vep', 'zea',
            'crh', 'zh-classical', 'frr', 'eml', 'ay', 'stq', 'udm', 'wuu',
            'nrm', 'kw', 'rm', 'szl', 'so', 'koi', 'as', 'lad', 'fur', 'mt',
            'dv', 'gn', 'dsb', 'ie', 'pcd', 'sd', 'lij', 'cbk-zam', 'cdo',
            'ksh', 'ext', 'mwl', 'gag', 'ang', 'ug', 'ace', 'pi', 'pag', 'nv',
            'lez', 'frp', 'sn', 'kab', 'ln', 'myv', 'pfl', 'xal', 'krc', 'haw',
            'rw', 'pdc', 'kaa', 'to', 'kl', 'arc', 'nov', 'kbd', 'av', 'bxr',
            'lo', 'bjn', 'ha', 'tet', 'tpi', 'na', 'pap', 'lbe', 'jbo', 'ty',
            'mdf', 'roa-rup', 'wo', 'tyv', 'ig', 'srn', 'nso', 'kg', 'ab',
            'ltg', 'zu', 'om', 'za', 'chy', 'cu', 'rmy', 'tw', 'tn', 'chr',
            'mai', 'pih', 'got', 'xh', 'bi', 'sm', 'ss', 'rn', 'ki', 'pnt',
            'bm', 'iu', 'ee', 'lg', 'ts', 'fj', 'ak', 'ik', 'st', 'sg', 'ff',
            'dz', 'ny', 'ch', 'ti', 've', 'ks', 'tum', 'cr', 'gom', 'lrc',
            'azb',
        ]

        # Sites we want to edit but not count as real languages
        self.test_codes = ['test', 'test2']

        super(Family, self).__init__()

        self.category_redirect_templates = {
            '_default': (),
            'ar': (u'تحويل تصنيف',
                   u'تحويلة تصنيف',
                   u'Category redirect',),
            'arz': (u'تحويل تصنيف',),
            'cs': (u'Zastaralá kategorie',),
            'da': (u'Kategoriomdirigering',),
            'en': (u'Category redirect',),
            'es': (u'Categoría redirigida',),
            'eu': (u'Kategoria redirect',),
            'fa': (u'رده بهتر',
                   u'انتقال رده',
                   u'فیلم‌های امریکایی',),
            'fr': (u'Redirection de catégorie',),
            'gv': (u'Aastiurey ronney',),
            'hi': (u'श्रेणीअनुप्रेषित',
                   u'Categoryredirect',),
            'hu': (u'Kat-redir',
                   u'Katredir',
                   u'Kat-redirekt',),
            'id': (u'Alih kategori',
                   u'Alihkategori',),
            'ja': (u'Category redirect',),
            'ko': (u'분류 넘겨주기',),
            'mk': (u'Премести категорија',),
            'ml': (u'Category redirect',),
            'ms': (u'Pengalihan kategori',
                   u'Categoryredirect',
                   u'Category redirect',),
            'mt': (u'Redirect kategorija',),
            'no': (u'Category redirect',
                   u'Kategoriomdirigering',
                   u'Kategori-omdirigering',),
            'pl': (u'Przekierowanie kategorii',
                   u'Category redirect',),
            'pt': (u'Redirecionamento de categoria',
                   u'Redircat',
                   u'Redirect-categoria',),
            'ro': (u'Redirect categorie',),
            'ru': (u'Переименованная категория',
                   u'Categoryredirect',
                   u'CategoryRedirect',
                   u'Category redirect',
                   u'Catredirect',),
            'sco': ('Category redirect',),
            'simple': (u'Category redirect',
                       u'Categoryredirect',
                       u'Catredirect',),
            'sh': (u'Prekat',
                   u'Preusmeri kategoriju',
                   u'Preusmjeri kategoriju',
                   u'Prekategorizuj',
                   u'Catred',
                   u'Catredirect',
                   u'Category redirect'),
            'sl': (u'Category redirect',),
            'sq': (u'Kategori e zhvendosur',
                   u'Category redirect',),
            'sv': (u'Kategoriomdirigering',
                   u'Omdirigering kategori',),
            'tl': (u'Category redirect',),
            'tr': (u'Kategori yönlendirme',
                   u'Kat redir',),
            'uk': (u'Categoryredirect',),
            'vi': (u'Đổi hướng thể loại',
                   u'Thể loại đổi hướng',
                   u'Chuyển hướng thể loại',
                   u'Categoryredirect',
                   u'Category redirect',
                   u'Catredirect',),
            'yi': (u'קאטעגאריע אריבערפירן',),
            'zh': (u'分类重定向',
                   u'Cr',
                   u'CR',
                   u'Cat-redirect',),
            'zh-yue': (u'Category redirect',
                       u'分類彈去',
                       u'分類跳轉',),
        }

        self.disambcatname = {
            'af':  u'dubbelsinnig',
            'als': u'Begriffsklärung',
            'ang': u'Scīrung',
            'ast': u'Dixebra',
            'ar':  u'صفحات توضيح',
            'be':  u'Disambig',
            'be-x-old':  u'Вікіпэдыя:Неадназначнасьці',
            'bg':  u'Пояснителни страници',
            'ca':  u'Pàgines de desambiguació',
            'cbk-zam': u'Desambiguo',
            'cs':  u'Rozcestníky',
            'cy':  u'Gwahaniaethu',
            'da':  u'Flertydig',
            'de':  u'Begriffsklärung',
            'el':  u'Αποσαφήνιση',
            'en':  u'All disambiguation pages',
            'eo':  u'Apartigiloj',
            'es':  u'Desambiguación',
            'et':  u'Täpsustusleheküljed',
            'eu':  u'Argipen orriak',
            'fa':  u'صفحه‌های ابهام‌زدایی',
            'fi':  u'Täsmennyssivut',
            'fo':  u'Fleiri týdningar',
            'fr':  u'Homonymie',
            'fy':  u'Trochferwiisside',
            'ga':  u'Idirdhealáin',
            'gl':  u'Homónimos',
            'he':  u'פירושונים',
            'hu':  u'Egyértelműsítő lapok',
            'ia':  u'Disambiguation',
            'id':  u'Disambiguasi',
            'io':  u'Homonimi',
            'is':  u'Aðgreiningarsíður',
            'it':  u'Disambigua',
            'ja':  u'曖昧さ回避',
            'ka':  u'მრავალმნიშვნელოვანი',
            'kw':  u'Folennow klerheans',
            'ko':  u'동음이의어 문서',
            'ku':  u'Rûpelên cudakirinê',
            'krc': u'Кёб магъаналы терминле',
            'ksh': u'Woot met mieh wi ëijnem Senn',
            'la':  u'Discretiva',
            'lb':  u'Homonymie',
            'li':  u'Verdudelikingspazjena',
            'ln':  u'Bokokani',
            'lt':  u'Nuorodiniai straipsniai',
            'ms':  u'Nyahkekaburan',
            'mt':  u'Diżambigwazzjoni',
            'nds': u'Mehrdüdig Begreep',
            'nds-nl': u'Wikipedie:Deurverwiespagina',
            'nl':  u'Wikipedia:Doorverwijspagina',
            'nn':  u'Fleirtydingssider',
            'no':  u'Pekere',
            'pl':  u'Strony ujednoznaczniające',
            'pt':  u'Desambiguação',
            'ro':  u'Dezambiguizare',
            'ru':  u'Многозначные термины',
            'scn': u'Disambigua',
            'sk':  u'Rozlišovacie stránky',
            'sl':  u'Razločitev',
            'sq':  u'Kthjellime',
            'sr':  u'Вишезначна одредница',
            'su':  u'Disambiguasi',
            'sv':  u'Förgreningssider',
            'szl': u'Zajty ujydnoznačńajůnce',
            'th':  u'การแก้ความกำกวม',
            'tl':  u'Paglilinaw',
            'tr':  u'Anlam ayrım',
            'uk':  u'Багатозначні геопункти',
            'vi':  u'Trang định hướng',
            'vo':  u'Telplänovapads',
            'wa':  u'Omonimeye',
            'zea': u'Wikipedia:Deurverwiespagina',
            'zh':  u'消歧义',
            'zh-min-nan': u'Khu-pia̍t-ia̍h',
        }

        # families that redirect their interlanguage links here.
        self.interwiki_forwarded_from = [
            'commons',
            'incubator',
            'meta',
            'species',
            'strategy',
            'test',
        ]

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = [
            'ab', 'ace', 'af', 'ak', 'als', 'am', 'an', 'ang', 'ar', 'arc',
            'arz', 'as', 'ast', 'av', 'ay', 'az', 'ba', 'bar', 'bat-smg', 'bcl',
            'be', 'be-x-old', 'bg', 'bh', 'bi', 'bjn', 'bm', 'bo', 'bpy', 'bug',
            'bxr', 'ca', 'cbk-zam', 'cdo', 'ce', 'ceb', 'ch', 'chr', 'chy',
            'ckb', 'co', 'cr', 'crh', 'csb', 'cu', 'cv', 'cy', 'da', 'diq',
            'dsb', 'dz', 'ee', 'el', 'eml', 'en', 'eo', 'et', 'eu', 'ext', 'fa',
            'ff', 'fi', 'fj', 'fo', 'frp', 'frr', 'fur', 'ga', 'gag', 'gan',
            'gd', 'glk', 'gn', 'got', 'gu', 'gv', 'ha', 'hak', 'haw', 'he',
            'hi', 'hif', 'hr', 'hsb', 'ht', 'hu', 'hy', 'ia', 'ie', 'ig', 'ik',
            'ilo', 'io', 'iu', 'ja', 'jbo', 'jv', 'ka', 'kaa', 'kab', 'kdb',
            'kg', 'ki', 'kk', 'kl', 'km', 'kn', 'ko', 'koi', 'krc', 'ks', 'ku',
            'kv', 'kw', 'ky', 'la', 'lad', 'lb', 'lbe', 'lez', 'lg', 'li',
            'lij', 'lmo', 'ln', 'lo', 'lt', 'ltg', 'lv', 'map-bms', 'mdf', 'mg',
            'mhr', 'mi', 'mk', 'ml', 'mn', 'mrj', 'ms', 'mwl', 'my', 'myv',
            'mzn', 'na', 'nah', 'nap', 'nds-nl', 'ne', 'new', 'nl', 'no', 'nov',
            'nrm', 'nso', 'nv', 'ny', 'oc', 'om', 'or', 'os', 'pa', 'pag',
            'pam', 'pap', 'pdc', 'pfl', 'pi', 'pih', 'pms', 'pnb', 'pnt', 'ps',
            'qu', 'rm', 'rmy', 'rn', 'roa-rup', 'roa-tara', 'ru', 'rue', 'rw',
            'sa', 'sah', 'sc', 'scn', 'sco', 'sd', 'se', 'sg', 'sh', 'si',
            'simple', 'sk', 'sm', 'sn', 'so', 'srn', 'ss', 'st', 'stq', 'su',
            'sv', 'sw', 'szl', 'ta', 'te', 'tet', 'tg', 'th', 'ti', 'tk', 'tl',
            'tn', 'to', 'tpi', 'tr', 'ts', 'tt', 'tum', 'tw', 'ty', 'udm', 'ug',
            'uz', 've', 'vec', 'vep', 'vls', 'vo', 'wa', 'war', 'wo', 'wuu',
            'xal', 'xh', 'yi', 'yo', 'za', 'zea', 'zh', 'zh-classical',
            'zh-min-nan', 'zh-yue', 'zu',
        ]

        # On most Wikipedias page names must start with a capital letter,
        # but some languages don't use this.
        self.nocapitalize = ['jbo']

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are
        # put after those, in code-alphabetical order.

        self.alphabetic_sr = [
            'ace', 'kbd', 'af', 'ak', 'als', 'am', 'ang', 'ab', 'ar', 'an',
            'arc', 'roa-rup', 'frp', 'arz', 'as', 'ast', 'gn', 'av', 'ay', 'az',
            'bjn', 'id', 'ms', 'bg', 'bm', 'zh-min-nan', 'nan', 'map-bms', 'jv',
            'su', 'ba', 'be', 'be-x-old', 'bh', 'bcl', 'bi', 'bn', 'bo', 'bar',
            'bs', 'bpy', 'br', 'bug', 'bxr', 'ca', 'ceb', 'ch', 'cbk-zam', 'sn',
            'tum', 'ny', 'cho', 'chr', 'co', 'cy', 'cv', 'cs', 'da', 'dk',
            'pdc', 'de', 'nv', 'dsb', 'na', 'dv', 'dz', 'mh', 'et', 'el', 'eml',
            'en', 'myv', 'es', 'eo', 'ext', 'eu', 'ee', 'fa', 'hif', 'fo', 'fr',
            'fy', 'ff', 'fur', 'ga', 'gv', 'sm', 'gag', 'gd', 'gl', 'gan', 'ki',
            'glk', 'got', 'gu', 'ha', 'hak', 'xal', 'haw', 'he', 'hi', 'ho',
            'hsb', 'hr', 'hy', 'io', 'ig', 'ii', 'ilo', 'ia', 'ie', 'iu', 'ik',
            'os', 'xh', 'zu', 'is', 'it', 'ja', 'ka', 'kl', 'kr', 'pam', 'krc',
            'csb', 'kk', 'kw', 'rw', 'ky', 'mrj', 'rn', 'sw', 'km', 'kn', 'ko',
            'kv', 'kg', 'ht', 'ks', 'ku', 'kj', 'lad', 'lbe', 'la', 'ltg', 'lv',
            'to', 'lb', 'lez', 'lt', 'lij', 'li', 'ln', 'lo', 'jbo', 'lg',
            'lmo', 'hu', 'mk', 'mg', 'mt', 'mi', 'min', 'cdo', 'mwl', 'ml',
            'mdf', 'mo', 'mn', 'mr', 'mus', 'my', 'mzn', 'nah', 'fj', 'ne',
            'nl', 'nds-nl', 'cr', 'new', 'nap', 'ce', 'frr', 'pih', 'no', 'nb',
            'nn', 'nrm', 'nov', 'oc', 'mhr', 'or', 'om', 'ng', 'hz', 'uz', 'pa',
            'pfl', 'pag', 'pap', 'koi', 'pi', 'pcd', 'pms', 'nds', 'pnb', 'pl',
            'pt', 'pnt', 'ps', 'aa', 'kaa', 'crh', 'ty', 'ksh', 'ro', 'rmy',
            'rm', 'qu', 'ru', 'rue', 'sa', 'sah', 'se', 'sg', 'sc', 'sco', 'sd',
            'stq', 'st', 'nso', 'tn', 'sq', 'si', 'scn', 'simple', 'ss', 'sk',
            'sl', 'cu', 'szl', 'so', 'ckb', 'srn', 'sr', 'sh', 'fi', 'sv', 'ta',
            'shi', 'tl', 'kab', 'roa-tara', 'tt', 'te', 'tet', 'th', 'ti', 'vi',
            'tg', 'tokipona', 'tp', 'tpi', 'chy', 've', 'tr', 'tk', 'tw', 'tyv',
            'udm', 'uk', 'ur', 'ug', 'za', 'vec', 'vep', 'vo', 'fiu-vro', 'wa',
            'vls', 'war', 'wo', 'wuu', 'ts', 'xmf', 'yi', 'yo', 'diq', 'zea',
            'zh', 'zh-tw', 'zh-cn', 'zh-classical', 'zh-yue', 'bat-smg',
        ]

        self.interwiki_putfirst = {
            'be-x-old': self.alphabetic,
            'en': self.alphabetic,
            'et': self.alphabetic_revised,
            'fi': self.alphabetic_revised,
            'fiu-vro': self.alphabetic_revised,
            'fy': self.fyinterwiki,
            'he': ['en'],
            'hu': ['en'],
            'lb': self.alphabetic,
            'mk': self.alphabetic,
            'ms': self.alphabetic_revised,
            'nds': ['nds-nl'],
            'nds-nl': ['nds'],
            'nn': ['no', 'sv', 'da'] + self.alphabetic,
            'no': self.alphabetic,
            'nv': ['en', 'es'] + self.alphabetic,
            'pdc': ['de', 'en'],
            'pl': self.alphabetic,
            'simple': self.alphabetic,
            'sr': self.alphabetic_sr,
            'sv': self.alphabetic,
            'te': ['en', 'hi', 'kn', 'ta', 'ml'],
            'ur': ['ar', 'fa', 'en'] + self.alphabetic,
            'vi': self.alphabetic_revised,
            'yi': ['en', 'he', 'de']
        }

        # Languages that used to be coded in iso-8859-1
        self.latin1old = [
            'de', 'en', 'et', 'es', 'ia', 'la', 'af', 'cs', 'fr', 'pt', 'sl',
            'bs', 'fy', 'vi', 'lt', 'fi', 'it', 'no', 'simple', 'gl', 'eu',
            'nds', 'co', 'mi', 'mr', 'id', 'lv', 'sw', 'tt', 'uk', 'vo', 'ga',
            'na', 'es', 'nl', 'da', 'dk', 'sv', 'test']

    def get_known_families(self, site):
        """Override the family interwiki prefixes for each site."""
        # In Swedish Wikipedia 's:' is part of page title not a family
        # prefix for 'wikisource'.
        if site.code == 'sv':
            d = self.known_families.copy()
            d.pop('s')
            d['src'] = 'wikisource'
            return d
        else:
            return self.known_families

    def code2encodings(self, code):
        """Return a list of historical encodings for a specific site."""
        # Historic compatibility
        if code == 'pl':
            return 'utf-8', 'iso8859-2'
        if code == 'ru':
            return 'utf-8', 'iso8859-5'
        if code in self.latin1old:
            return 'utf-8', 'iso-8859-1'
        return self.code2encoding(code),

        # Subpages for documentation.
        # TODO: List is incomplete, to be completed for missing languages.
        # TODO: Remove comments for appropriate pages
        self.doc_subpages = {
            '_default': ((u'/doc', ),
                         ['ar', 'bn', 'cs', 'da', 'en', 'es', 'fa',
                          'hu', 'id', 'ilo', 'ja', 'ms',
                          'ms', 'pt', 'ro', 'ru', 'simple', 'vi', 'zh']
                         ),
            'ca': (u'/ús', ),
            'de': (u'Doku', u'/Meta'),
            'dsb': (u'/Dokumentacija', ),
            'eu': (u'txantiloi dokumentazioa', u'/dok'),
            # fi: no idea how to handle this type of subpage at :Metasivu:
            'fi': ((), ),
            'fr': (u'/documentation', ),
            'hsb': (u'/Dokumentacija', ),
            'it': (u'/Man', ),
            'ka': (u'/ინფო', ),
            'ko': (u'/설명문서', ),
            'no': (u'/dok', ),
            'nn': (u'/dok', ),
            'pl': (u'/opis', ),
            'sk': (u'/Dokumentácia', ),
            'sv': (u'/dok', ),
            'uk': (u'/Документація', ),
        }

    def shared_data_repository(self, code, transcluded=False):
        """Return the shared data repository for this site."""
        if code in ['test', 'test2']:
            return ('test', 'wikidata')
        else:
            return ('wikidata', 'wikidata')
