# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wikipedia, the Free Encyclopedia

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikipedia'

        self.languages_by_size = [
            'en', 'de', 'fr', 'it', 'pl', 'es', 'nl', 'ru', 'ja', 'pt', 'sv',
            'zh', 'ca', 'uk', 'no', 'fi', 'vi', 'cs', 'hu', 'ko', 'tr', 'id',
            'ro', 'fa', 'ar', 'da', 'eo', 'sr', 'lt', 'sk', 'he', 'bg', 'ms',
            'sl', 'vo', 'eu', 'war', 'hr', 'hi', 'kk', 'et', 'az', 'gl',
            'simple', 'nn', 'new', 'th', 'el', 'roa-rup', 'la', 'tl', 'ht',
            'ka', 'mk', 'sh', 'te', 'pms', 'ceb', 'be-x-old', 'ta', 'br', 'lv',
            'jv', 'be', 'mr', 'sq', 'cy', 'lb', 'is', 'bs', 'oc', 'yo', 'an',
            'mg', 'bpy', 'bn', 'io', 'fy', 'lmo', 'sw', 'gu', 'ml', 'pnb', 'af',
            'nds', 'scn', 'ur', 'ku', 'zh-yue', 'qu', 'ne', 'hy', 'diq', 'su',
            'ast', 'nap', 'ga', 'cv', 'bat-smg', 'tt', 'wa', 'am', 'kn', 'als',
            'ia', 'zh-min-nan', 'tg', 'bug', 'vec', 'roa-tara', 'yi', 'gd',
            'arz', 'os', 'sah', 'uz', 'my', 'pam', 'nah', 'sco', 'hsb', 'mi',
            'mn', 'li', 'sa', 'co', 'gan', 'glk', 'ba', 'si', 'hif', 'bcl',
            'fo', 'mrj', 'ckb', 'bar', 'fiu-vro', 'nds-nl', 'tk', 'vls', 'gv',
            'ilo', 'se', 'map-bms', 'dv', 'nrm', 'pag', 'pa', 'rm', 'mzn', 'bo',
            'ps', 'udm', 'km', 'fur', 'csb', 'wuu', 'mt', 'ug', 'lij', 'rue',
            'koi', 'pi', 'kv', 'ang', 'bh', 'mhr', 'sc', 'lad', 'nov',
            'zh-classical', 'ksh', 'ky', 'cbk-zam', 'hak', 'so', 'kw', 'nv',
            'frp', 'szl', 'ext', 'stq', 'ie', 'xal', 'rw', 'haw', 'ln', 'pdc',
            'or', 'pcd', 'pfl', 'krc', 'to', 'frr', 'crh', 'ace', 'eml', 'gn',
            'myv', 'ay', 'arc', 'kl', 'ce', 'pap', 'bjn', 'lbe', 'gag', 'tpi',
            'jbo', 'wo', 'mdf', 'zea', 'av', 'kab', 'ty', 'srn', 'dsb', 'xmf',
            'lo', 'ab', 'as', 'ig', 'na', 'tet', 'mwl', 'kg', 'kaa', 'rmy',
            'ltg', 'sn', 'cu', 'kbd', 'sm', 'sd', 'bi', 'bm', 'ks', 'ik', 'iu',
            'ss', 'pih', 'pnt', 'za', 'chr', 'cdo', 'got', 'ee', 'ha', 'ti',
            'bxr', 'zu', 'om', 've', 'ts', 'sg', 'rn', 'cr', 'dz', 'tum', 'fj',
            'lg', 'ch', 'tn', 'ny', 'ff', 'st', 'ak', 'chy', 'xh', 'ki', 'tw',
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikipedia.org' % lang

        self.category_redirect_templates = {
            '_default': (),
            'ar': (u"تحويل تصنيف",
                   u"تحويلة تصنيف",
                   u"Category redirect",
                   u"تحويلة تصنيف",),
            'arz': (u'تحويل تصنيف',),
            'cs': (u'Zastaralá kategorie',),
            'da': (u'Kategoriomdirigering',),
            'de': (u'Kategorieweiterleitung',),
            'en': (u"Category redirect",
                   u"Category redirect3",
                   u"Categoryredirect",
                   u"CR",
                   u"Catredirect",
                   u"Cat redirect",
                   u"Catredir",
                   u"Seecat",),
            'es': (u'Categoría redirigida',),
            'eu': (u'Kategoria redirect',),
            'fa': (u'رده بهتر',
                   u'انتقال رده',
                   u'فیلم‌های امریکایی',),
            'fr': (u'Redirection de catégorie',),
            'hi': (u'श्रेणीअनुप्रेषित',
                   u'Categoryredirect',),
            'hu': (u'Kat-redir',
                   u'Katredir',
                   u'Kat-redirekt',),
            'id': (u'Alih kategori',
                   u'Alihkategori',),
            # 'it' has removed its template
            # 'ja' is discussing to remove this template
            'ja': (u"Category redirect",),
            'ko': (u'분류 넘겨주기',),
            'mk': (u'Премести категорија',),
            'ms': (u'Pengalihan kategori',
                   u'Categoryredirect',
                   u'Category redirect',),
            'mt': (u'Redirect kategorija',),
            # 'nl' has removed its template
            'no': (u"Category redirect",
                   u"Kategoriomdirigering",
                   u"Kategori-omdirigering",),
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
            'simple': (u"Category redirect",
                       u"Categoryredirect",
                       u"Catredirect",),
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

        self.disambiguationTemplates = {
            # If no templates are given, retrieve names from  the live wiki
            # ([[MediaWiki:Disambiguationspage]])
            '_default': [u'Disambig'],
            'ang': [u'Disambig', u'Geodis'],
            'arc': [u'ܕ'],
            'ast': [u'Dixebra'],
            'az':  [u'Dəqiqləşdirmə'],
            'ba':  [u'Күп мәғәнәлелек'],
            'bcl': [u'Clarip'],
            'bn':  [u'দ্ব্যর্থতা নিরসন', u'Disambig'],
            'cdo': [u'Gì-ngiê'],
            'ext': [u'Desambiguáncia'],
            'fo':  [u'Fleiri týdningar'],
            'frp': [u'Homonimos'],
            'fur': [u'Disambiguazion', u'Disambig'],
            'fy':  [u'Tfs', u'Neibetsjuttings'],
            'gan': [u'扤清楚', u'Disambig'],
            'gd':  [u'Soilleireachadh'],
            'haw': [u'Huaʻōlelo puana like'],
            'hr':  [u'Preusmjerenje u razdvojbu', u'Razdvojba', u'razdvojba1',
                    u'Nova razdvojba'],
            'hy':  [u'Երկիմաստ', u'Բազմիմաստություն', u'Բազմանշանակ', u'Disambig'],
            'kg':  [u'Bisongidila'],
            'krc': [u'Кёб магъаналы', u'Disambig'],
            'la':  [u'Discretiva', u'Disnomen'], #{{Disambig}} is not a disambig
            'lb':  [u'Homonymie', u'Disambig', u'Homonymie Ofkierzungen'],
            'li':  [u'Verdudeliking', u'Verdudelikingpazjena', u'Vp'],
            'lmo': [u'Desambiguació', u'Dezambiguasiú', u'Desambiguazion',
                    u'Desambiguassiú', u'Desambiguació'],
            'mn':  [u'Салаа утгатай', u'Disambig'],
            'nl':  [u'Dp', u'DP', u'Dp2', u'Dpintro', u'Cognomen',
                    u'Dp cognomen'],
            'nn':  [u'Fleirtyding', u'Tobokstavforkorting', u'Pekerside',
                    u'Peikar', u'Disambig'],
            'no':  [u'Peker', u'Etternavn', u'Disambig',
                    u'Tobokstavsforkortelse', u'Trebokstavsforkortelse',
                    u'Flertydig', u'Pekerside'],
            'nov': [u'Desambig'],
            'nrm': [u'Page dé frouque'],
            'qu':  [u"Sut'ichana qillqa", u'Disambig', u'SJM'],
            'rmy': [u'Dudalipen'],
            'ro':  [u'Dezambiguizare', u'Disambig', u'Hndis', u'Dez',
                    u'Dezamb'],
            'sc':  [u'Disambigua'],
            'sk':  [u'Disambig', u'Rozlišovacia stránka', u'Disambiguation'],
            'srn': [u'Dp'],
            'tg':  [u'Ибҳомзудоӣ', u'Disambig', u'Рафъи ибҳом',
                    u'Disambiguation'],
            'tr':  [u'Anlam ayrım', u'Disambig', u'Anlam ayrımı',
                    u'Kişi adları (anlam ayrımı)',
                    u'Yerleşim yerleri (anlam ayrımı)',
                    u'kısaltmalar (anlam ayrımı)', u'Coğrafya (anlam ayrımı)',
                    u'Yerleşim yerleri (anlam ayrımı)', u'Sayılar (anlam ayrımı)',
                    u"ABD'deki iller (anlam ayrımı)"],
            'vls': [u'Db', u'Dp', u'Dpintro'],
            'wo':  [u'Bokktekki'],
            'yi':  [u'באדייטען'],
            'zea': [u'dp', u'Deurverwiespagina'],
            'zh':  [u'Disambig', u'消歧义', u'消歧义页', u'消歧義', u'消歧義頁',
                    u'Letter disambig', u'Isomerdab'],
            'zh-classical':  [u'Disambig', u'釋義', u'消歧義'],
            'zh-yue': [u'搞清楚', u'Disambig'],
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
            'ca':  u'Viquipèdia:Registre de pàgines de desambiguació',
            'cbk-zam': u'Desambiguo',
            'cs':  u'Rozcestníky',
            'cy':  u'Gwahaniaethu',
            'da':  u'Flertdig',
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

        # CentralAuth cross avaliable projects.
        self.cross_projects = [
            'wiktionary', 'wikibooks', 'wikiquote', 'wikisource', 'wikinews', 'wikiversity',
            'meta', 'mediawiki', 'test', 'incubator', 'commons', 'species',
        ]
        # Global bot allowed languages on
        # http://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = [
            'ab', 'ace', 'af', 'ak', 'als', 'am', 'an', 'ang', 'arc', 'arz',
            'as', 'ast', 'av', 'ay', 'az', 'ba', 'bat-smg', 'bar', 'bcl',
            'be-x-old', 'be', 'bg', 'bh', 'bi', 'bm', 'bo', 'bpy', 'bug', 'bxr',
            'cbk-zam', 'cdo', 'ce', 'ceb', 'ch', 'chr', 'chy', 'ckb', 'co',
            'crh', 'cr', 'csb', 'cu', 'cv', 'cy', 'diq', 'dsb', 'dz', 'ee',
            'el', 'eml', 'eo', 'et', 'eu', 'ext', 'fa', 'ff', 'fj', 'fo', 'frp',
            'frr', 'fur', 'ga', 'gan', 'gd', 'glk', 'gn', 'got', 'gu', 'gv',
            'ha', 'hak', 'haw', 'hif', 'hi', 'hr', 'hsb', 'ht', 'hu', 'hy',
            'ia', 'id', 'ie', 'ig', 'ik', 'ilo', 'iow', 'is', 'iu', 'ja', 'jbo',
            'jv', 'kaa', 'kab', 'ka', 'kg', 'ki', 'kk', 'kl', 'km', 'kn', 'ko',
            'koi', 'ks', 'ku', 'kv', 'kw', 'ky', 'lad', 'lb', 'lbe', 'lg', 'li',
            'lij', 'lmo', 'ln', 'lo', 'lv', 'map-bms', 'mdf', 'mg', 'mhr', 'mi',
            'mk', 'mn', 'mrj', 'ms', 'mt', 'mwl', 'myv', 'my', 'mzn', 'nah',
            'na', 'nap', 'nds-nl', 'ne', 'new', 'ng', 'nl', 'nov', 'nrm', 'nv',
            'ny', 'oc', 'om', 'or', 'os', 'pam', 'pap', 'pa', 'pag', 'pdc',
            'pfl', 'pi', 'pih', 'pms', 'pnb', 'pnt', 'ps', 'qu', 'rm', 'rmy',
            'rn', 'roa-rup', 'roa-tara', 'rw', 'sah', 'sa', 'sc', 'scn', 'sco',
            'sd', 'se', 'sg', 'sh', 'simple', 'si', 'sk', 'sm', 'sn', 'so',
            'srn', 'stq', 'st', 'su', 'sw', 'szl', 'ta', 'te', 'tet', 'tg',
            'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tpi', 'ts', 'tt', 'tum', 'tw',
            'ty', 'udm', 'ug', 'uz', 've', 'vls', 'wa', 'war', 'wo', 'wuu',
            'xal', 'xh', 'yi', 'yo', 'za', 'zea', 'zh', 'zh-classical',
            'zh-min-nan', 'zu',
        ]

        # On most Wikipedias page names must start with a capital letter,
        # but some languages don't use this.
        self.nocapitalize = ['jbo',]

        self.alphabetic_latin = [
            'ace', 'af', 'ak', 'als', 'am', 'ang', 'ab', 'ar', 'an', 'arc',
            'roa-rup', 'frp', 'arz', 'as', 'ast', 'gn', 'av', 'ay', 'az', 'bjn',
            'id', 'ms', 'bg', 'bm', 'zh-min-nan', 'nan', 'map-bms', 'jv', 'su',
            'ba', 'be', 'be-x-old', 'bh', 'bcl', 'bi', 'bn', 'bo', 'bar', 'bs',
            'bpy', 'br', 'bug', 'bxr', 'ca', 'ceb', 'ch', 'cbk-zam', 'sn',
            'tum', 'ny', 'cho', 'chr', 'co', 'cy', 'cv', 'cs', 'da', 'dk',
            'pdc', 'de', 'nv', 'dsb', 'na', 'dv', 'dz', 'mh', 'et', 'el', 'eml',
            'en', 'myv', 'es', 'eo', 'ext', 'eu', 'ee', 'fa', 'hif', 'fo', 'fr',
            'fy', 'ff', 'fur', 'ga', 'gv', 'sm', 'gag', 'gd', 'gl', 'gan', 'ki',
            'glk', 'got', 'gu', 'ha', 'hak', 'xal', 'haw', 'he', 'hi', 'ho',
            'hsb', 'hr', 'hy', 'io', 'ig', 'ii', 'ilo', 'ia', 'ie', 'iu', 'ik',
            'os', 'xh', 'zu', 'is', 'it', 'ja', 'ka', 'kl', 'kr', 'pam', 'kbd',
            'krc', 'csb', 'kk', 'kw', 'rw', 'ky', 'mrj', 'rn', 'sw', 'km', 'kn',
            'ko', 'kv', 'kg', 'ht', 'ks', 'ku', 'kj', 'lad', 'lbe', 'la', 'ltg',
            'lv', 'to', 'lb', 'lt', 'lij', 'li', 'ln', 'lo', 'jbo', 'lg', 'lmo',
            'hu', 'mk', 'mg', 'mt', 'mi', 'cdo', 'mwl', 'ml', 'mdf', 'mo', 'mn',
            'mr', 'mus', 'my', 'mzn', 'nah', 'fj', 'ne', 'nl', 'nds-nl', 'cr',
            'new', 'nap', 'ce', 'frr', 'pih', 'no', 'nb', 'nn', 'nrm', 'nov',
            'oc', 'mhr', 'or', 'om', 'ng', 'hz', 'uz', 'pa', 'pfl', 'pag',
            'pap', 'koi', 'pi', 'pcd', 'pms', 'nds', 'pnb', 'pl', 'pt', 'pnt',
            'ps', 'aa', 'kaa', 'crh', 'ty', 'ksh', 'ro', 'rmy', 'rm', 'qu',
            'ru', 'rue', 'sa', 'sah', 'se', 'sg', 'sc', 'sco', 'sd', 'stq',
            'st', 'tn', 'sq', 'si', 'scn', 'simple', 'ss', 'sk', 'sl', 'cu',
            'szl', 'so', 'ckb', 'srn', 'sr', 'sh', 'fi', 'sv', 'ta', 'tl',
            'kab', 'roa-tara', 'tt', 'te', 'tet', 'th', 'ti', 'vi', 'tg',
            'tokipona', 'tp', 'tpi', 'chy', 've', 'tr', 'tk', 'tw', 'udm', 'uk',
            'ur', 'ug', 'za', 'vec', 'vo', 'fiu-vro', 'wa', 'vls', 'war', 'wo',
            'wuu', 'ts', 'xmf', 'yi', 'yo', 'diq', 'zea', 'zh', 'zh-tw',
            'zh-cn', 'zh-classical', 'zh-yue', 'bat-smg',
        ]

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are
        # put after those, in code-alphabetical order.

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
            'nds': ['nds-nl', 'pdt'], # Note: as of 2008-02-24, pdt:
            'nds-nl': ['nds', 'pdt'], # (Plautdietsch) is still in the Incubator.
            'nn': ['no', 'nb', 'sv', 'da'] + self.alphabetic,
            'no': self.alphabetic,
            'pdc': ['de', 'en'],
            'pl': self.alphabetic,
            'simple': self.alphabetic,
            'sr': self.alphabetic_latin,
            'sv': self.alphabetic,
            'te': ['en', 'hi', 'kn', 'ta', 'ml'],
            'ur': ['ar', 'fa', 'en'] + self.alphabetic,
            'vi': self.alphabetic_revised,
            'yi': ['en', 'he', 'de']
        }

        self.obsolete = {
            'aa': None,  # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Afar_Wikipedia
            'cho': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Choctaw_Wikipedia
            'dk': 'da',
            'ho': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Hiri_Motu_Wikipedia
            'hz': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Herero_Wikipedia
            'ii': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Yi_Wikipedia
            'kj': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kwanyama_Wikipedia
            'kr': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kanuri_Wikipedia
            'mh': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Marshallese_Wikipedia
            'minnan': 'zh-min-nan',
            'mo': 'ro', # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Moldovan_Wikipedia
            'mus': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Muscogee_Wikipedia
            'nb': 'no',
            'ng': None, #(not reachable) http://meta.wikimedia.org/wiki/Inactive_wikis
            'jp': 'ja',
            'ru-sib': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Siberian_Wikipedia
            'tlh': None,
            'tokipona': None,
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        # Languages that used to be coded in iso-8859-1
        self.latin1old = ['de', 'en', 'et', 'es', 'ia', 'la', 'af', 'cs',
                    'fr', 'pt', 'sl', 'bs', 'fy', 'vi', 'lt', 'fi', 'it',
                    'no', 'simple', 'gl', 'eu', 'nds', 'co', 'mi', 'mr',
                    'id', 'lv', 'sw', 'tt', 'uk', 'vo', 'ga', 'na', 'es',
                    'nl', 'da', 'dk', 'sv', 'test']

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
            #wrong wikipedia namespace alias
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
        # In Swedish Wikipedia 's:' is part of page title not a family
        # prefix for 'wikisource'.
        if site.language() == 'sv':
            d = self.known_families.copy()
            d.pop('s') ; d['src'] = 'wikisource'
            return d
        else:
            return self.known_families

    def dbName(self, code):
        # returns the name of the MySQL database
        # for historic reasons, the databases are called xxwiki instead of
        # xxwikipedia for Wikipedias.
        return '%swiki_p' % code

    def code2encodings(self, code):
        """Return a list of historical encodings for a specific language
           wikipedia"""
        # Historic compatibility
        if code == 'pl':
            return 'utf-8', 'iso8859-2'
        if code == 'ru':
            return 'utf-8', 'iso8859-5'
        if code in self.latin1old:
            return 'utf-8', 'iso-8859-1'
        return self.code2encoding(code),

    def shared_image_repository(self, code):
        return ('commons', 'commons')
