# -*- coding: utf-8  -*-
"""Family module for Wikipedia."""

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikipedia, the Free Encyclopedia
class Family(family.WikimediaFamily):

    """Family module for Wikipedia."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'wikipedia'

        self.languages_by_size = [
            'en', 'sv', 'nl', 'de', 'fr', 'ru', 'it', 'es', 'vi', 'war', 'ceb',
            'pl', 'ja', 'pt', 'zh', 'uk', 'ca', 'no', 'fa', 'fi', 'id', 'ar',
            'cs', 'ko', 'ms', 'hu', 'ro', 'sr', 'tr', 'min', 'sh', 'kk', 'eo',
            'sk', 'eu', 'da', 'lt', 'bg', 'he', 'hr', 'sl', 'uz', 'hy', 'et',
            'vo', 'nn', 'gl', 'simple', 'hi', 'la', 'el', 'az', 'th', 'oc',
            'ka', 'mk', 'be', 'new', 'tt', 'pms', 'tl', 'ta', 'te', 'cy', 'lv',
            'be-x-old', 'ht', 'ur', 'ce', 'bs', 'sq', 'br', 'jv', 'mg', 'lb',
            'mr', 'is', 'ml', 'pnb', 'ba', 'af', 'my', 'zh-yue', 'bn', 'ga',
            'lmo', 'yo', 'fy', 'an', 'cv', 'tg', 'ky', 'sw', 'ne', 'io', 'gu',
            'bpy', 'sco', 'scn', 'nds', 'ku', 'ast', 'qu', 'su', 'als', 'gd',
            'kn', 'am', 'ckb', 'ia', 'nap', 'bug', 'bat-smg', 'wa', 'map-bms',
            'mn', 'arz', 'pa', 'mzn', 'si', 'zh-min-nan', 'yi', 'sah', 'fo',
            'vec', 'sa', 'bar', 'nah', 'os', 'roa-tara', 'pam', 'or', 'hsb',
            'se', 'li', 'mrj', 'mi', 'ilo', 'co', 'hif', 'bcl', 'gan', 'frr',
            'bo', 'rue', 'glk', 'mhr', 'nds-nl', 'fiu-vro', 'ps', 'tk', 'pag',
            'vls', 'gv', 'xmf', 'diq', 'km', 'kv', 'zea', 'csb', 'crh', 'hak',
            'vep', 'sc', 'ay', 'dv', 'so', 'zh-classical', 'nrm', 'rm', 'udm',
            'koi', 'kw', 'ug', 'stq', 'lad', 'wuu', 'lij', 'eml', 'fur', 'mt',
            'bh', 'as', 'cbk-zam', 'gn', 'pi', 'pcd', 'szl', 'gag', 'ksh',
            'nov', 'ang', 'ie', 'nv', 'ace', 'ext', 'frp', 'mwl', 'ln', 'sn',
            'lez', 'dsb', 'pfl', 'krc', 'haw', 'pdc', 'kab', 'xal', 'rw', 'myv',
            'to', 'arc', 'kl', 'bjn', 'kbd', 'lo', 'ha', 'pap', 'tpi', 'av',
            'lbe', 'mdf', 'jbo', 'na', 'wo', 'bxr', 'ty', 'srn', 'ig', 'nso',
            'kaa', 'kg', 'tet', 'ab', 'ltg', 'zu', 'za', 'cdo', 'tyv', 'chy',
            'tw', 'rmy', 'roa-rup', 'cu', 'tn', 'om', 'chr', 'got', 'bi', 'pih',
            'rn', 'sm', 'bm', 'ss', 'iu', 'sd', 'pnt', 'ki', 'xh', 'ts', 'ee',
            'ak', 'ti', 'fj', 'lg', 'ks', 'ff', 'sg', 'ny', 've', 'cr', 'st',
            'dz', 'ik', 'tum', 'ch',
        ]

        langs = self.languages_by_size + ['test', 'test2']  # Sites we want to edit but not count as real languages

        self.langs = dict([(lang, '%s.wikipedia.org' % lang)
                           for lang in langs])

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

        self.obsolete = {
            'aa': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Afar_Wikipedia
            'cho': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Choctaw_Wikipedia
            'dk': 'da',
            'ho': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Hiri_Motu_Wikipedia
            'hz': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Herero_Wikipedia
            'ii': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Yi_Wikipedia
            'kj': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kwanyama_Wikipedia
            'kr': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kanuri_Wikipedia
            'mh': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Marshallese_Wikipedia
            'minnan': 'zh-min-nan',
            'mo': 'ro',  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Moldovan_Wikipedia
            'mus': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Muscogee_Wikipedia
            'nan': 'zh-min-nan',
            'nl_nds': 'nl-nds',  # miss-spelling
            'nb': 'no',
            'ng': None,  # (not reachable) https://meta.wikimedia.org/wiki/Inactive_wikis
            'jp': 'ja',
            'ru-sib': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Siberian_Wikipedia
            'tlh': None,
            'tokipona': None,
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        # Languages that used to be coded in iso-8859-1
        self.latin1old = [
            'de', 'en', 'et', 'es', 'ia', 'la', 'af', 'cs', 'fr', 'pt', 'sl',
            'bs', 'fy', 'vi', 'lt', 'fi', 'it', 'no', 'simple', 'gl', 'eu',
            'nds', 'co', 'mi', 'mr', 'id', 'lv', 'sw', 'tt', 'uk', 'vo', 'ga',
            'na', 'es', 'nl', 'da', 'dk', 'sv', 'test']

        self.crossnamespace[0] = {
            '_default': {
                'pt': [102],
                'als': [104],
                'ar': [104],
                'de': [4],
                'en': [12],
                'es': [104],
                'fi': [4],
                'fr': [104],
                'hr': [102],
                'lt': [104],
            },
            'km': {
                '_default': [0, 4, 12],
            },
            # wrong wikipedia namespace alias
            'mzn': {
                '_default': [0, 4],

            },
        }
        self.crossnamespace[1] = {
            '_default': {
                'pt': [103],
                'als': [105],
                'ar': [105],
                'en': [13],
                'es': [105],
                'fi': [5],
                'fr': [105],
                'hr': [103],
                'lt': [105],
            },
        }
        self.crossnamespace[4] = {
            '_default': {
                '_default': [12],
            },
            'de': {
                '_default': [0, 10, 12],
                'el': [100, 12],
                'es': [104, 12],
            },
            'fi': {
                '_default': [0, 12]
            },
            'mzn': {
                '_default': [0, 12]
            },
        }
        self.crossnamespace[5] = {
            'fi': {
                '_default': [1]}
        }
        self.crossnamespace[12] = {
            '_default': {
                '_default': [4],
            },
            'en': {
                '_default': [0, 4],
            },
        }
        self.crossnamespace[13] = {
            'en': {
                '_default': [0],
            },
        }
        self.crossnamespace[102] = {
            'pt': {
                '_default': [0],
                'als': [0, 104],
                'ar': [0, 104],
                'es': [0, 104],
                'fr': [0, 104],
                'lt': [0, 104]
            },
            'hr': {
                '_default': [0],
                'als': [0, 104],
                'ar': [0, 104],
                'es': [0, 104],
                'fr': [0, 104],
                'lt': [0, 104]
            },
        }
        self.crossnamespace[103] = {
            'pt': {
                '_default': [1],
                'als': [1, 105],
                'es': [1, 105],
                'fr': [1, 105],
                'lt': [1, 105]
            },
            'hr': {
                '_default': [1],
                'als': [1, 105],
                'es': [1, 105],
                'fr': [1, 105],
                'lt': [1, 105]
            },
        }
        self.crossnamespace[104] = {
            'als': {
                '_default': [0],
                'pt': [0, 102],
                'hr': [0, 102],
            },
            'ar': {
                '_default': [0, 100],
                'hr': [0, 102],
                'pt': [0, 102],
            },
            'es': {
                '_default': [0],
                'pt': [0, 102],
                'hr': [0, 102],
            },
            'fr': {
                '_default': [0],
                'pt': [0, 102],
                'hr': [0, 102],
            },
            'lt': {
                '_default': [0],
                'pt': [0, 102],
                'hr': [0, 102],
            },
        }
        self.crossnamespace[105] = {
            'als': {
                '_default': [1],
                'pt': [0, 103],
                'hr': [0, 103],
            },
            'ar': {
                '_default': [1, 101],
            },
            'es': {
                '_default': [1],
                'pt': [0, 103],
                'hr': [0, 103],
            },
            'fr': {
                '_default': [1],
                'pt': [0, 103],
                'hr': [0, 103],
            },
            'lt': {
                '_default': [1],
                'pt': [0, 103],
                'hr': [0, 103],
            },
        }

    def get_known_families(self, site):
        """Override the family interwiki prefixes for each site."""
        # In Swedish Wikipedia 's:' is part of page title not a family
        # prefix for 'wikisource'.
        if site.language() == 'sv':
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
