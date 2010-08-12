# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wikipedia, the Free Encyclopedia

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikipedia'

        self.languages_by_size = [
            'en', 'de', 'fr', 'pl', 'it', 'ja', 'es', 'nl', 'pt', 'ru', 'sv',
            'zh', 'ca', 'no', 'fi', 'uk', 'hu', 'cs', 'ro', 'tr', 'ko', 'da',
            'eo', 'ar', 'id', 'vi', 'vo', 'sr', 'sk', 'lt', 'he', 'bg', 'fa',
            'sl', 'war', 'hr', 'et', 'new', 'ms', 'simple', 'th', 'gl',
            'roa-rup', 'nn', 'eu', 'hi', 'el', 'ht', 'te', 'la', 'ka', 'mk',
            'ceb', 'az', 'br', 'sh', 'tl', 'mr', 'jv', 'lb', 'bs', 'lv', 'is',
            'cy', 'pms', 'sq', 'be-x-old', 'bpy', 'ta', 'be', 'oc', 'an', 'bn',
            'io', 'sw', 'fy', 'nds', 'lmo', 'scn', 'gu', 'af', 'qu', 'su', 'ku',
            'zh-yue', 'ur', 'ml', 'ast', 'nap', 'bat-smg', 'wa', 'cv', 'ga',
            'ksh', 'hy', 'yo', 'tg', 'kn', 'roa-tara', 'vec', 'gd', 'yi', 'uz',
            'pam', 'zh-min-nan', 'os', 'tt', 'sah', 'ne', 'als', 'mi', 'arz',
            'kk', 'nah', 'li', 'hsb', 'glk', 'co', 'gan', 'pnb', 'ia', 'bcl',
            'mn', 'fiu-vro', 'am', 'nds-nl', 'fo', 'vls', 'tk', 'sa', 'si',
            'bar', 'dv', 'gv', 'nrm', 'pag', 'rm', 'map-bms', 'my', 'sco',
            'diq', 'se', 'ckb', 'wuu', 'fur', 'lij', 'ug', 'bh', 'mt', 'nov',
            'mzn', 'csb', 'mg', 'ilo', 'km', 'zh-classical', 'sc', 'lad', 'pi',
            'ang', 'cbk-zam', 'frp', 'bo', 'hak', 'hif', 'pa', 'kw', 'xal',
            'szl', 'haw', 'pdc', 'ps', 'ie', 'stq', 'fj', 'crh', 'kv', 'to',
            'ace', 'myv', 'nv', 'so', 'gn', 'ky', 'krc', 'ln', 'ext', 'mhr',
            'arc', 'jbo', 'wo', 'eml', 'ty', 'pcd', 'kab', 'tpi', 'pap', 'ay',
            'ee', 'zea', 'ba', 'srn', 'kl', 'udm', 'ig', 'ce', 'or', 'dsb',
            'kg', 'lo', 'ab', 'rmy', 'cu', 'mwl', 'mdf', 'kaa', 'sm', 'av',
            'ks', 'tet', 'got', 'sd', 'na', 'bm', 'pih', 'pnt', 'iu', 'ik',
            'as', 'cdo', 'bi', 'chr', 'bug', 'om', 'za', 'ss', 'ti', 'ts', 've',
            'zu', 'ha', 'dz', 'sg', 'ch', 'cr', 'xh', 'lbe', 'ak', 'rw', 'ki',
            'tn', 'bxr', 'ny', 'st', 'tw', 'rn', 'sn', 'chy', 'ff', 'tum', 'lg',
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
            # set value to None, instead of a list, to retrieve names from
            # the live wiki ([[MediaWiki:Disambiguationspage]]
            '_default': [u'Disambig'],
            'af':  None,
            'als': None,
            'an':  None,
            'ang': [u'Disambig', u'Geodis'],
            'ar':  None,
            'arc': [u'ܕ'],
            'arz': None,
            'ast': [u'Dixebra'],
            'av':  [u'Неоднозначность'],
            'ay':  [u'Desambiguación'],
            'az':  [u'Dəqiqləşdirmə'],
            'ba':  [u'Күп мәғәнәлелек'],
            'bar': None,
            'bcl': [u'Clarip'],
            'be':  [u'Неадназначнасць', u'Disambig'],
            'be-x-old':  [u'Неадназначнасьць', u'Disambig'],
            'bg':  None,
            'bn':  [u'দ্ব্যর্থতা নিরসন', u'Disambig'],
            'br':  None,
            'bs':  [u'Čvor'],
            'ca':  None,
            'ceb': None,
            'cdo': [u'Gì-ngiê'],
            'crh': [u'Çoq manalı', u'Disambig'],
            'cs':  None,
            'cu':  None,
            'cy':  None,
            'da':  None,
            'de':  None,
            'dsb': [u'Wěcejwóznamowosć'],
            'el':  None,
            'en':  None,
            'eo':  None,
            'es':  None,
            'et':  None,
            'eu':  None,
            'ext': [u'Desambiguáncia'],
            'fa':  None,
            'fi':  None,
            'fiu-vro': [u'Täpsüstüslehekülg'],
            'fo':  [u'Fleiri týdningar'],
            'fr':  None,
            'frp': [u'Homonimos'],
            'fur': [u'Disambiguazion', u'Disambig'],
            'fy':  [u'Tfs', u'Neibetsjuttings'],
            'ga':  [u'Idirdhealú', u'Disambig'],
            'gan': [u'扤清楚', u'Disambig'],
            'gd':  [u'Soilleireachadh'],
            'gl':  None,
            'gv':  [u'Reddaghey'],
            'haw': [u'Huaʻōlelo puana like'],
            'he':  None,
            'hi':  [u'बहुविकल्पी शब्द', u'Disambig',],
            'hr':  [u'Preusmjerenje u razdvojbu', u'Razdvojba', u'razdvojba1', u'Nova razdvojba'],
            'hsb': [u'Wjacezmyslnosć', u'Disambig'],
            'ht':  [u'Menm non', u'Disambig'],
            'hu':  [u'Egyert', u'Disambig', u'Egyért', u'Egyért-redir'],
            'hy':  None,
            'ia':  [u'Disambiguation', u'Disambig'],
            'id':  None,
            'io':  [u'Homonimo', u'Disambig'],
            'is':  None,
            'it':  None,
            'ja':  None,
            'ka':  None,
            'kab': [u'Asefham'],
            'kg':  [u'Bisongidila'],
            'kn':  [u'ದ್ವಂದ್ವ ನಿವಾರಣೆ'],
            'ko':  None,
            'krc': [u'Кёб магъаналы', u'Disambig'],
            'ksh': None,
            'ku':  None,
            'kw':  None,
            'la':  None,
            'lb':  [u'Homonymie', u'Disambig', u'Homonymie Ofkierzungen'],
            'li':  [u'Verdudeliking', u'Verdudelikingpazjena', u'Vp'],
            'lmo': [u'Desambiguació', u'Dezambiguasiú', u'Desambiguazion',
                    u'Desambiguassiú', u'Desambiguació'],
            'ln':  None,
            'lt':  None,
            'lv':  [u'Nozīmju atdalīšana', u'Disambig'],
            'mk':  [u'Појаснување', u'Disambig', u'Geodis'],
            'mn':  [u'Салаа утгатай', u'Disambig'],
            'ms':  [u'Nyahkekaburan', u'Disambig'],
            'mt':  None,
            'mzn': [u'گجگجی بایری'],
            'nap': [u'Disambigua'],
            'nds': [u'Mehrdüdig Begreep', 'Disambig'],
            'nds-nl': None,
            'nl':  [u'Dp', u'DP', u'Dp2', u'Dpintro', u'Cognomen', u'Dp cognomen'],
            'nn':  [u'Fleirtyding', u'Tobokstavforkorting', u'Pekerside', u'Peikar', u'Disambig'],
            'no':  [u'Peker', u'Etternavn', u'Disambig', u'Tobokstavsforkortelse',
                    u'Trebokstavsforkortelse', u'Flertydig', u'Pekerside'],
            'nov': [u'Desambig'],
            'nv':  None,
            'nrm': [u'Page dé frouque'],
            'oc':  [u'Omonimia', u'Disambig'],
            'pl':  None,
            'pms': [u'Gestion dij sinònim'],
            'pt':  None,
            'qu':  [u"Sut'ichana qillqa", u'Disambig', u'SJM'],
            'rmy': [u'Dudalipen'],
            'ro':  [u'Dezambiguizare', u'Disambig', u'Hndis', u'Dez', u'Dezamb'],
            'ru':  None,
            'sc':  [u'Disambigua'],
            'scn': [u'Disambigua', u'Disambig', u'Sigla2', u'Sigla3'],
            'simple': None,
            'sh':  None,
            'sk':  [u'Disambig', u'Rozlišovacia stránka', u'Disambiguation'],
            'sl':  None,
            'sq':  [u'Kthjellim', u'Disambig'],
            'sr':  None,
            'srn': [u'Dp'],
            'stq': [u'Begriepskläärenge'],
            'su':  None,
            'sv':  None,
            'sw':  [u'Maana'],
            'szl': [u'Disambig'], 
            'ta':  None,
            'te':  None,
            'tg':  [u'Ибҳомзудоӣ', u'Disambig', u'Рафъи ибҳом', u'Disambiguation'],
            'th':  [u'แก้กำกวม', u'Disambig', u'คำกำกวม'],
            'tl':  None,
            'to':  [u'Fakaʻuhingakehe'],
            'tr':  [u'Anlam ayrım', u'Disambig', u'Anlam ayrımı',
                    u'Kişi adları (anlam ayrımı)', u'Yerleşim yerleri (anlam ayrımı)',
                    u'kısaltmalar (anlam ayrımı)'],
            'uk':  None,
            'vec': [u'Disanbigua', u'Disambigua'],
            'vi':  None,
            'vls': [u'Db', u'Dp', u'Dpintro'],
            'vo':  None,
            'wa':  None,
            'war': None,
            'wo':  [u'Bokktekki'],
            'yi':  [u'באדייטען'],
            'zea': [u'dp', u'Deurverwiespagina'],
            'zh':  [u'Disambig', u'消歧义', u'消歧义页', u'消歧義', u'消歧義頁', u'Letter disambig'],
            'zh-classical':  [u'Disambig', u'釋義', u'消歧義'],
            'zh-min-nan': None,
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
            'nds-nl': u'Deurverwiespagina',
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
            'ab', 'ace', 'af', 'ak', 'als', 'am', 'an', 'ang', 'arc', 'arz', 'as', 'ast', 'av', 'ay', 'az',
            'ba', 'bat-smg', 'bar', 'bcl', 'be-x-old', 'be', 'bg', 'bh', 'bi', 'bm', 'bo', 'bpy', 'bug', 'bxr',
            'cbk-zam', 'cdo', 'ce', 'ceb', 'ch', 'chr', 'chy', 'ckb', 'co', 'crh', 'cr', 'csb', 'cu', 'cv', 'cy',
            'diq', 'dsb', 'dz', 'ee', 'el', 'eml', 'eo', 'et', 'eu', 'ext', 'fa', 'ff', 'fj', 'fo', 'frp', 'fur',
            'ga', 'gan', 'gd', 'glk', 'gn', 'got', 'gu', 'gv', 'ha', 'hak', 'haw', 'hif', 'hi', 'hr', 'hsb', 'ht', 'hu', 'hy',
            'ia', 'id', 'ie', 'ig', 'ik', 'ilo', 'iow', 'is', 'iu', 'ja', 'jbo', 'jv',
            'kaa', 'kab', 'ka', 'kg', 'ki', 'kk', 'kl', 'km', 'kn', 'ko', 'ks', 'ku', 'kv', 'kw', 'ky',
            'lad', 'lb', 'lbe', 'lg', 'li', 'lij', 'lmo', 'ln', 'lo', 'lv',
            'map-bms', 'mdf', 'mg', 'mhr', 'mi', 'mk', 'mn', 'ms', 'mt', 'mwl', 'myv', 'my', 'mzn',
            'nah', 'na', 'nap', 'nds-nl', 'ne', 'new', 'ng', 'nl', 'nov', 'nrm', 'nv', 'ny', 'oc', 'om', 'or', 'os',
            'pam', 'pap', 'pa', 'pag', 'pdc', 'pi', 'pih', 'pms', 'pnb', 'pnt', 'ps', 'qu', 'rm', 'rmy', 'rn', 'roa-rup', 'roa-tara', 'rw',
            'sah', 'sa', 'sc', 'scn', 'sco', 'sd', 'se', 'sg', 'sh', 'simple', 'si', 'sk', 'sm', 'sn', 'so', 'srn', 'stq', 'st', 'su', 'sw', 'szl',
            'ta', 'te', 'tet', 'tg', 'th', 'ti', 'tk', 'tl', 'tn', 'to', 'tpi', 'ts', 'tt', 'tum', 'tw', 'ty',
            'udm', 'ug', 'uz', 've', 'vls', 'wa', 'war', 'wo', 'wuu',
            'xal', 'xh', 'yi', 'yo', 'za', 'zea', 'zh', 'zh-classical', 'zh-min-nan', 'zu',
        ]

        # On most Wikipedias page names must start with a capital letter,
        # but some languages don't use this.
        self.nocapitalize = ['jbo',]

        # A revised sorting order worked out on
        # http://meta.wikimedia.org/wiki/Interwiki_sorting_order
        self.alphabetic_revised = [
            'ace', 'af', 'ak', 'als', 'am', 'ang', 'ab', 'ar', 'an', 'arc',
            'roa-rup', 'frp', 'as', 'ast', 'gn', 'av', 'ay', 'az', 'id', 'ms',
            'bm', 'bn', 'zh-min-nan', 'nan', 'map-bms', 'jv', 'su', 'ba', 'be',
            'be-x-old', 'bh', 'bcl', 'bi', 'bar', 'bo', 'bs', 'br', 'bug', 'bg',
            'bxr', 'ca', 'ceb', 'cv', 'cs', 'ch', 'cbk-zam', 'ny', 'sn', 'tum',
            'cho', 'co', 'cy', 'da', 'dk', 'pdc', 'de', 'dv', 'nv', 'dsb', 'na',
            'dz', 'mh', 'et', 'el', 'eml', 'en', 'myv', 'es', 'eo', 'ext', 'eu',
            'ee', 'fa', 'hif', 'fo', 'fr', 'fy', 'ff', 'fur', 'ga', 'gv', 'sm',
            'gd', 'gl', 'gan', 'ki', 'glk', 'gu', 'got', 'hak', 'xal', 'ko',
            'ha', 'haw', 'hy', 'hi', 'ho', 'hsb', 'hr', 'io', 'ig', 'ilo',
            'bpy', 'ia', 'ie', 'iu', 'ik', 'os', 'xh', 'zu', 'is', 'it', 'he',
            'kl', 'kn', 'kr', 'pam', 'ka', 'ks', 'csb', 'kk', 'kw', 'rw', 'ky',
            'rn', 'sw', 'kv', 'kg', 'ht', 'ku', 'kj', 'lad', 'lbe', 'lo', 'la',
            'lv', 'to', 'lb', 'lt', 'lij', 'li', 'ln', 'jbo', 'lg', 'lmo', 'hu',
            'mk', 'mg', 'ml', 'krc', 'mt', 'mi', 'mr', 'arz', 'mzn', 'cdo',
            'mwl', 'mdf', 'mo', 'mn', 'mus', 'my', 'nah', 'fj', 'nl', 'nds-nl',
            'cr', 'ne', 'new', 'ja', 'nap', 'ce', 'pih', 'no', 'nb', 'nn',
            'nrm', 'nov', 'ii', 'oc', 'mhr', 'or', 'om', 'ng', 'hz', 'uz', 'pa',
            'pi', 'pag', 'pnb', 'pap', 'ps', 'km', 'pcd', 'pms', 'nds', 'pl',
            'pnt', 'pt', 'aa', 'kaa', 'crh', 'ty', 'ksh', 'ro', 'rmy', 'rm',
            'qu', 'ru', 'sah', 'se', 'sa', 'sg', 'sc', 'sco', 'stq', 'st', 'tn',
            'sq', 'scn', 'si', 'simple', 'sd', 'ss', 'sk', 'sl', 'cu', 'szl',
            'so', 'ckb', 'srn', 'sr', 'sh', 'fi', 'sv', 'tl', 'ta', 'kab',
            'roa-tara', 'tt', 'te', 'tet', 'th', 'vi', 'ti', 'tg', 'tpi',
            'tokipona', 'tp', 'chr', 'chy', 've', 'tr', 'tk', 'tw', 'udm', 'uk',
            'ur', 'ug', 'za', 'vec', 'vo', 'fiu-vro', 'wa', 'zh-classical',
            'vls', 'war', 'wo', 'wuu', 'ts', 'yi', 'yo', 'zh-yue', 'diq', 'zea',
            'bat-smg', 'zh', 'zh-tw', 'zh-cn',
        ]
        
        self.alphabetic_latin = [
            'ace', 'af', 'ak', 'als', 'am', 'ang', 'ab', 'ar', 'an', 'arc',
            'roa-rup', 'frp', 'arz', 'as', 'ast', 'gn', 'av', 'ay', 'az', 'id',
            'ms', 'bg', 'bm', 'zh-min-nan', 'nan', 'map-bms', 'jv', 'su', 'ba',
            'be', 'be-x-old', 'bh', 'bcl', 'bi', 'bn', 'bo', 'bar', 'bs', 'bpy',
            'br', 'bug', 'bxr', 'ca', 'ceb', 'ch', 'cbk-zam', 'sn', 'tum', 'ny',
            'cho', 'chr', 'co', 'cy', 'cv', 'cs', 'da', 'dk', 'pdc', 'de', 'nv',
            'dsb', 'na', 'dv', 'dz', 'mh', 'et', 'el', 'eml', 'en', 'myv', 'es',
            'eo', 'ext', 'eu', 'ee', 'fa', 'hif', 'fo', 'fr', 'fy', 'ff', 'fur',
            'ga', 'gv', 'sm', 'gd', 'gl', 'gan', 'ki', 'glk', 'got', 'gu', 'ha',
            'hak', 'xal', 'haw', 'he', 'hi', 'ho', 'hsb', 'hr', 'hy', 'io',
            'ig', 'ii', 'ilo', 'ia', 'ie', 'iu', 'ik', 'os', 'xh', 'zu', 'is',
            'it', 'ja', 'ka', 'kl', 'kr', 'pam', 'krc', 'csb', 'kk', 'kw', 'rw',
            'ky', 'rn', 'sw', 'km', 'kn', 'ko', 'kv', 'kg', 'ht', 'ks', 'ku',
            'kj', 'lad', 'lbe', 'la', 'lv', 'to', 'lb', 'lt', 'lij', 'li', 'ln',
            'lo', 'jbo', 'lg', 'lmo', 'hu', 'mk', 'mg', 'mt', 'mi', 'cdo',
            'mwl', 'ml', 'mdf', 'mo', 'mn', 'mr', 'mus', 'my', 'mzn', 'nah',
            'fj', 'ne', 'nl', 'nds-nl', 'cr', 'new', 'nap', 'ce', 'pih', 'no',
            'nb', 'nn', 'nrm', 'nov', 'oc', 'mhr', 'or', 'om', 'ng', 'hz', 'uz',
            'pa', 'pag', 'pap', 'pi', 'pcd', 'pms', 'nds', 'pnb', 'pl', 'pt',
            'pnt', 'ps', 'aa', 'kaa', 'crh', 'ty', 'ksh', 'ro', 'rmy', 'rm',
            'qu', 'ru', 'sa', 'sah', 'se', 'sg', 'sc', 'sco', 'sd', 'stq', 'st',
            'tn', 'sq', 'si', 'scn', 'simple', 'ss', 'sk', 'sl', 'cu', 'szl',
            'so', 'ckb', 'srn', 'sr', 'sh', 'fi', 'sv', 'ta', 'tl', 'kab',
            'roa-tara', 'tt', 'te', 'tet', 'th', 'ti', 'vi', 'tg', 'tokipona',
            'tp', 'tpi', 'chy', 've', 'tr', 'tk', 'tw', 'udm', 'uk', 'ur', 'ug',
            'za', 'vec', 'vo', 'fiu-vro', 'wa', 'vls', 'war', 'wo', 'wuu', 'ts',
            'yi', 'yo', 'diq', 'zea', 'zh', 'zh-tw', 'zh-cn', 'zh-classical',
            'zh-yue', 'bat-smg',
        ]

        # Order for fy: alphabetical by code, but y counts as i

        def fycomp(x,y):
            x = x.replace("y","i")+x.count("y")*"!"
            y = y.replace("y","i")+y.count("y")*"!"
            return cmp(x,y)
        self.fyinterwiki = self.alphabetic[:]
        self.fyinterwiki.remove('nb')
        self.fyinterwiki.sort(fycomp)

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
            'nds': ['nds-nl', 'pdt'] + self.alphabetic, # Note: as of 2008-02-24, pdt: (Plautdietsch) is still in the Incubator.
            'nn': ['no', 'nb', 'sv', 'da'] + self.alphabetic,
            'no': self.alphabetic,
            'pl': self.alphabetic,
            'simple': self.alphabetic,
            'sr': self.alphabetic_latin,
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
            'mo': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Moldovan_Wikipedia
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
                '_default': [0, 12]
            },
            'fi': {
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

    def version(self, code):
        return '1.16wmf4'

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
