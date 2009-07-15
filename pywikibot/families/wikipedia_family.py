# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wikipedia, the Free Encyclopedia

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikipedia'

        self.languages_by_size = [
            'en', 'de', 'fr', 'pl', 'ja', 'it', 'nl', 'pt', 'es', 'ru',
            'sv', 'zh', 'no', 'fi', 'ca', 'uk', 'tr', 'cs', 'hu', 'ro',
            'vo', 'eo', 'da', 'sk', 'id', 'ko', 'ar', 'he', 'vi', 'lt',
            'sl', 'sr', 'bg', 'et', 'fa', 'hr', 'new', 'simple', 'ht', 'nn',
            'gl', 'th', 'te', 'el', 'ms', 'eu', 'ceb', 'hi', 'mk', 'ka',
            'la', 'lb', 'bs', 'br', 'is', 'az', 'sq', 'cy', 'mr', 'bpy',
            'sh', 'tl', 'lv', 'pms', 'be-x-old', 'bn', 'jv', 'oc', 'ta', 'io',
            'be', 'an', 'nds', 'su', 'scn', 'nap', 'ku', 'af', 'fy', 'ast',
            'sw', 'wa', 'zh-yue', 'bat-smg', 'qu', 'ur', 'cv', 'ml', 'ksh', 'war',
            'tg', 'ga', 'vec', 'roa-tara', 'uz', 'gd', 'gu', 'pam', 'kn', 'mi',
            'yi', 'yo', 'lmo', 'glk', 'nah', 'zh-min-nan', 'co', 'hsb', 'roa-rup', 'als',
            'kk', 'ia', 'li', 'hy', 'gan', 'sah', 'tt', 'tk', 'sa', 'wuu',
            'nds-nl', 'fo', 'os', 'vls', 'fiu-vro', 'arz', 'nrm', 'bcl', 'am', 'rm',
            'pag', 'map-bms', 'dv', 'mn', 'gv', 'se', 'diq', 'fur', 'ne', 'sco',
            'bar', 'lij', 'nov', 'bh', 'mt', 'ilo', 'pi', 'mzn', 'zh-classical', 'km',
            'ug', 'csb', 'frp', 'lad', 'si', 'pdc', 'kw', 'ang', 'haw', 'sc',
            'mg', 'to', 'kv', 'szl', 'pa', 'ps', 'ie', 'my', 'gn', 'ln',
            'hif', 'stq', 'wo', 'jbo', 'arc', 'crh', 'tpi', 'ty', 'ext', 'cbk-zam',
            'ky', 'eml', 'zea', 'srn', 'ay', 'myv', 'hak', 'pap', 'ig', 'kg',
            'so', 'or', 'kab', 'lo', 'rmy', 'ba', 'ce', 'sm', 'udm', 'av',
            'ks', 'nv', 'dsb', 'cu', 'got', 'kaa', 'tet', 'sd', 'bo', 'mdf',
            'iu', 'na', 'bm', 'as', 'cdo', 'chr', 'ee', 'om', 'pnt', 'pih',
            'kl', 'zu', 'ab', 'ti', 'ts', 'ss', 'za', 'bi', 'cr', 'dz',
            'xal', 've', 'ch', 'ha', 'xh', 'tn', 'bug', 'st', 'bxr', 'ik',
            'rw', 'chy', 'tw', 'ak', 'fj', 'ny', 'ff', 'sn', 'sg', 'lbe',
            'rn', 'ki', 'lg', 'tum', 'ng', 'mhr',
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
                   u'Catredirect',
                   u'Categoryredirect',),
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
            'af':  [u'Dubbelsinnig', u'Disambig'],
            'als': [u'Begriffsklärung', u'Disambig'],
            'an':  [u'Desambig', u'Disambig'],
            'ar':  [u'Disambig', u'توضيح'],
            'arc': [u'ܕ'],
            'ast': [u'Dixebra'],
            'av':  [u'Неоднозначность'],
            'az':  [u'Dəqiqləşdirmə'],
            'bar': [u'Begriffsklärung'],
            'be':  [u'Неадназначнасць', u'Disambig'],
            'be-x-old':  [u'Неадназначнасць', u'Неадназначнасьць', u'Disambig'],
            'bg':  [u'Пояснение', u'Disambig'],
            'bn':  [u'দ্ব্যর্থতা নিরসন', u'Disambig'],
            'br':  [u'Hvlstumm', u'Digejañ', u'Digejañ anvioù-badez'],
            'bs':  [u'Čvor'],
            'ca':  [u'Desambiguació', u'Disambig', u'Desambigua',
                    u'acrònim', u'onomàstica'],
            'ceb': [u'Giklaro'],
            'cdo': [u'Gì-ngiê'],
            'cs':  [u'Rozcestník', u'Rozcestník - 2 znaky', u'Rozcestník - Příjmení',
                    u'Rozcestník - místopisné jméno', u'Disambig', u'Rozcestník - příjmení',
                    u'Rozcestník - sakrální stavba', u'Rozcestník - kostel',
                    u'Rozcestník - 3 znaky'],
            'cu':  [u'Мъногосъмыслиѥ', u'Disambig'],
            'cy':  [u'Anamrwysedd', u'Disambig', u'Gwahaniaethu'],
            'da':  [u'Flertydig'],
            'de':  [u'Begriffsklärung', u'BKS', u'Disambig'],
            'el':  [u'Disambig', u'Αποσαφ', u'Αποσαφήνιση'],
            'en':  None,
            'eo':  [u'Apartigilo', u'Disambig'],
            'es':  [u'Desambiguacion', u'Desambiguación', u'Desambig', u'Disambig',u'Des'],
            'et':  [u'Täpsustuslehekülg', u'Täpsustus', u'Disambig'],
            'eu':  [u'Argipen', u'Disambig'],
            'ext': [u'Desambiguáncia'],
            'fa':  [u'ابهام‌زدایی',u'ابهام زدایی'],
            'fi':  [u'Täsmennyssivu', u'Disambig'],
            'fo':  [u'Fleiri týdningar'],
            'fr':  None,
            'frp': [u'Homonimos'],
            'fy':  [u'Tfs', u'Neibetsjuttings'],
            'ga':  [u'Idirdhealú', u'Disambig'],
            'gl':  [u'Homónimos', u'Disambig'],
            'gv':  [u'Reddaghey'],
            'haw': [u'Huaʻōlelo puana like'],
            'he':  [u'פירושונים', u'Disambig'],
            'hi':  [u'बहुविकल्पी शब्द', u'Disambig',],
            'hr':  [u'Disambig', u'Razdvojba', u'razdvojba1'],
            'hsb': [u'Wjacezmyslnosć', u'Disambig'],
            'ht':  [u'Menm non', u'Disambig'],
            'hu':  [u'Egyert', u'Disambig', u'Egyért', u'Egyért-redir'],
            'hy':  [u'Երկիմաստ', u'Disambig'],
            'ia':  [u'Disambiguation', u'Disambig'],
            'id':  [u'Disingkat',u'Disambig', u'Disambig nama', u'Disambig tempat', u'Disambig-bandara', u'Disambiguasi', u'Disambig suku'],
            'io':  [u'Homonimo', u'Disambig'],
            'is':  None,
            'it':  [u'Disambigua', u'Sigla2', u'Sigla3', u'Sigla4', u'Cogni'],
            'ja':  [u'Aimai', u'Dab', u'曖昧さ回避', u'Disambig'],
            'ka':  [u'მრავალმნიშვნელოვანი', u'მრავმნიშ'],
            'kab': [u'Asefham'],
            'kg':  [u'Bisongidila'],
            'kn':  [u'ದ್ವಂದ್ವ ನಿವಾರಣೆ'],
            'ko':  [u'Disambig', u'동음이의', u'동음이의어'],
            'ku':  [u'Cudakirin'],
            'kw':  [u'Klerheans'],
            'ksh': [u'Disambig'],
            'la':  [u'Discretiva', u'Disnomen'],
            'lb':  [u'Homonymie', u'Disambig'],
            'li':  [u'Verdudeliking', u'Verdudelikingpazjena', u'Vp'],
            'lmo': [u'Desambiguació'],
            'ln':  [u'Bokokani'],
            'lt':  None,
            'mk':  [u'Појаснување', u'Disambig', u'Geodis'],
            'mo':  [u'Дезамбигуйзаре', u'Disambig'],
            'ms':  [u'Nyahkekaburan', u'Disambig'],
            'mt':  [u'Diżambigwazzjoni'],
            'mzn': [u'گجگجی بایری'],
            'nap': [u'Disambigua'],
            'nds': [u'Mehrdüdig Begreep', 'Disambig'],
            'nds-nl': [u'Dv'],
            'nl':  [u'Dp', u'DP', u'Dp2', u'Dpintro', u'Cognomen'],
            'nn':  [u'Fleirtyding'],
            'no':  [u'Peker', u'Etternavn', u'Disambig', u'Tobokstavsforkortelse',
                    u'Trebokstavsforkortelse', u'Flertydig', u'Pekerside'],
            'nov': [u'Desambig'],
            'nrm': [u'Page dé frouque'],
            'oc':  [u'Omonimia', u'Disambig'],
            'pl':  [u'Disambig', u'DisambRulers', u'DisambigC', u'Strona ujednoznaczniająca'],
            'pms': [u'Gestion dij sinònim'],
            'pt':  [u'Desambiguação', u'Disambig', u'Desambig'],
            'qu':  [u"Sut'ichana qillqa", u'Disambig', u'SJM'],
            'rmy': [u'Dudalipen'],
            'ro':  [u'Dezambiguizare', u'Disambig', u'Hndis', u'Dez'],
            'ru':  [u'Disambig', u'Неоднозначность', u'неоднозначность',
                    u'Многозначность', u'Фамилия'],
            'scn': [u'Disambigua', u'Disambig', u'Sigla2', u'Sigla3'],
            'simple': None,
            'sh': [u'Višeznačna odrednica', u'Disambig', u'Razdvojba',
                  u'Razvrstavanje', u'VZO', u'Višeznačnost',
                  u'Homograf',
                  u'Radzvojba', u'Čvor'],
            'sk':  [u'Disambig', u'Rozlišovacia stránka', u'Disambiguation'],
            'sl':  None,
            'sq':  [u'Kthjellim', u'Disambig'],
            'sr':  [u'Вишезначна одредница', u'Disambig', u'Вишезначна',
                    u'Višeznačna odrednica'],
            'srn': [u'Dp'],
            'su':  [u'Disambig'],
            'sv':  None,
            'sw':  [u'Maana'],
            'ta':  [u'பக்கவழி நெறிப்படுத்தல்'],
            'te':  [u'అయోమయ నివృత్తి', u'వివరమైన అయోమయ నివృత్తి'],
            'tg':  [u'Ибҳомзудоӣ', u'Disambig', u'Рафъи ибҳом', u'Disambiguation'],
            'th':  [u'แก้กำกวม', u'Disambig', u'คำกำกวม'],
            'tl':  [u'Paglilinaw', u'Disambig'],
            'tr':  [u'Anlam ayrım', u'Disambig', u'Anlam ayrımı',
                    u'Kişi adları (anlam ayrımı)', u'Yerleşim yerleri (anlam ayrımı)',
                    u'kısaltmalar (anlam ayrımı)'],
            'uk':  [u'Неоднозначність',u'DisambigG', u'Disambig', u'DisambigN',
                    u'Багатозначність'],
            'vec': [u'Disambigua'],
            'vi':  [u'Trang định hướng', u'Định hướng', u'Disambig', u'Hndis'],
            'vls': [u'Db', u'Dp', u'Dpintro'],
            'vo':  [u'Telplänov'],
            'wa':  [u'Omonimeye', u'Disambig'],
            'yi':  [u'באדייטען'],
            'zea': [u'dp', u'Deurverwiespagina'],
            'zh':  [u'Disambig', u'消歧义', u'消歧义页', u'消歧義'],
            'zh-classical':  [u'Disambig', u'釋義', u'消歧義'],
            'zh-min-nan': [u'Khu-pia̍t-ia̍h', 'KhPI', u'Disambig'],
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
            'fa':  u'صفحات ابهام‌زدایی',
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

        # Global bot allowed languages on http://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = [
            'ab', 'af', 'ak', 'am', 'ang', 'arc', 'arz', 'as', 'ast,', 'av', 'ay', 'az',
            'ba', 'bar', 'bcl', 'be-x-old', 'be', 'bg', 'bh', 'bi', 'bm', 'bo', 'bpy', 'bug', 'bxr',
            'cbk-zam', 'cdo', 'ce', 'ch', 'chr', 'chy', 'co', 'crh', 'cr', 'csb', 'cu', 'cv', 'cy',
            'diq', 'dsb', 'dz', 'ee', 'eml', 'eu', 'ext', 'fa', 'ff', 'fj', 'fo', 'frp', 'fur',
            'gan', 'ga', 'glk', 'gn', 'got', 'gu', 'gv', 'ha', 'hak', 'haw', 'hif', 'hi', 'hsb', 'ht', 'hu', 'hy',
            'ia', 'id', 'ie', 'ig', 'ik', 'ilo', 'iow', 'is', 'iu', 'jbo', 'jv',
            'kaa', 'kab', 'ka', 'kg', 'ki', 'kl', 'km', 'kn', 'ko', 'ks', 'ku', 'kv', 'kw', 'ky',
            'lad', 'lbe', 'lg', 'li', 'lij', 'lmo', 'ln', 'lo', 'lv', 'map-bms', 'mdf', 'mg', 'mk', 'mn', 'mt', 'myv', 'my', 'mzn',
            'nah', 'na', 'nap', 'nds-nl', 'ne', 'new', 'ng', 'nl', 'nov', 'nrm', 'nv', 'ny', 'om', 'or', 'os',
            'pam', 'pap', 'pa', 'pdc', 'pnt', 'ps', 'qu', 'rm', 'rmy', 'rn', 'roa-rup', 'roa-tara', 'rw',
            'sah', 'sa', 'sc', 'sco', 'sd', 'se', 'sg', 'sh', 'simple', 'si', 'sk', 'sm', 'sn', 'so', 'srn', 'stq', 'st', 'su', 'sw', 'szl',
            'ta', 'te', 'tet', 'tg', 'ti', 'tk', 'tn', 'to', 'tpi', 'ts', 'tt', 'tum', 'tw', 'ty',
            'udm', 'ug', 'uz', 've', 'vls', 'wa', 'war', 'wo', 'wuu',
            'xal', 'xh', 'yi', 'yo', 'za', 'zh', 'zh-classic', 'zh-min-nan', 'zu',
        ]
        # On most Wikipedias page names must start with a capital letter, but some
        # languages don't use this.

        self.nocapitalize = ['jbo',]


        # A revised sorting order worked out on http://meta.wikimedia.org/wiki/Interwiki_sorting_order
        self.alphabetic_revised = [
            'af', 'ak', 'als', 'am', 'ang', 'ab', 'ar', 'an', 'arc', 'roa-rup',
            'frp', 'as', 'ast', 'gn', 'av', 'ay', 'az', 'id', 'ms', 'bm', 'bn',
            'zh-min-nan', 'nan', 'map-bms', 'jv', 'su', 'ba', 'be', 'be-x-old',
            'bh', 'bcl', 'bi', 'bar', 'bo', 'bs', 'br', 'bug', 'bg', 'bxr',
            'ca', 'ceb', 'cv', 'cs', 'ch', 'cbk-zam', 'ny', 'sn', 'tum', 'cho',
            'co', 'cy', 'da', 'dk', 'pdc', 'de', 'dv', 'nv', 'dsb', 'na', 'dz',
            'mh', 'mhr', 'et', 'el', 'eml', 'en', 'myv', 'es', 'eo', 'ext', 'eu',
            'ee','fa', 'hif', 'fo', 'fr', 'fy', 'ff', 'fur', 'ga', 'gv', 'sm',
            'gd','gl', 'gan', 'ki', 'glk', 'gu', 'got', 'hak', 'xal', 'ko', 'ha',
            'haw', 'hy', 'hi', 'ho', 'hsb', 'hr', 'io', 'ig', 'ilo', 'bpy',
            'ia', 'ie', 'iu', 'ik', 'os', 'xh', 'zu', 'is', 'it', 'he', 'kl',
            'kn', 'kr', 'pam', 'ka', 'ks', 'csb', 'kk', 'kw', 'rw', 'ky', 'rn',
            'sw', 'kv', 'kg', 'ht', 'ku', 'kj', 'lad', 'lbe', 'lo', 'la', 'lv',
            'to', 'lb', 'lt', 'lij', 'li', 'ln', 'jbo', 'lg', 'lmo', 'hu',
            'mk', 'mg', 'ml', 'mt', 'mi', 'mr', 'arz', 'mzn', 'cdo', 'mdf',
            'mo', 'mn', 'mus', 'my', 'nah', 'fj', 'nl', 'nds-nl', 'cr', 'ne',
            'new', 'ja', 'nap', 'ce', 'pih', 'no', 'nb', 'nn', 'nrm', 'nov',
            'ii', 'oc', 'or', 'om', 'ng', 'hz', 'uz', 'pa', 'pi', 'pag', 'pap',
            'ps', 'km', 'pms', 'nds', 'pl', 'pnt', 'pt', 'aa', 'kaa', 'crh',
            'ty', 'ksh', 'ro', 'rmy', 'rm', 'qu', 'ru', 'sah', 'se', 'sa', 'sg',
            'sc', 'za', 'sco', 'stq', 'st', 'tn', 'sq', 'scn', 'si', 'simple',
            'sd', 'ss', 'sk', 'sl', 'cu', 'szl', 'so', 'srn', 'sr', 'sh', 'fi',
            'sv', 'tl', 'ta', 'kab', 'roa-tara', 'tt', 'te', 'tet', 'th', 'vi',
            'ti', 'tg', 'tpi', 'tokipona', 'tp', 'chr', 'chy', 've', 'tr',
            'tk', 'tw', 'udm', 'uk', 'ur', 'ug', 'vec', 'vo', 'fiu-vro', 'wa',
            'zh-classical', 'vls', 'war', 'wo', 'wuu', 'ts', 'yi', 'yo',
            'zh-yue', 'diq', 'zea', 'bat-smg', 'zh', 'zh-tw', 'zh-cn'
        ]

        # Order for fy: alphabetical by code, but y counts as i

        def fycomp(x,y):
            x = x.replace("y","i")+x.count("y")*"!"
            y = y.replace("y","i")+y.count("y")*"!"
            return cmp(x,y)
        self.fyinterwiki = self.alphabetic[:]
        self.fyinterwiki.sort(fycomp)

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are put
        # after those, in code-alphabetical order.

        self.interwiki_putfirst = {
            'en': self.alphabetic,
            'et': self.alphabetic_revised,
            'fi': self.alphabetic_revised,
            'fiu-vro': self.alphabetic_revised,
            'fy': self.fyinterwiki,
            'he': ['en'],
            'hu': ['en'],
            'lb': self.alphabetic,
            'ms': self.alphabetic_revised,
            'nds': ['nds-nl', 'pdt'] + self.alphabetic, # Note: as of 2008-02-24, pdt: (Plautdietsch) is still in the Incubator.
            'nn': ['no', 'nb', 'sv', 'da'] + self.alphabetic,
            'no': self.alphabetic,
            'pl': self.alphabetic,
            'simple': self.alphabetic,
            'te': ['en', 'hi', 'kn', 'ta', 'ml'],
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
                'en': [12],
                'es': [104],
                'fi': [4],
                'fr': [104],
                'hr': [102],
                'lt': [104],
            },
        }
        self.crossnamespace[1] = {
            '_default': {
                'pt': [103],
                'als': [105],
                'en': [13],
                'es': [105],
                'fi': [5],
                'fr': [105],
                'hr': [103],
                'lt': [105],
            },
        }
        self.crossnamespace[4] = {
            'fi': {'_default': [0]}
        }
        self.crossnamespace[5] = {
            'fi': {'_default': [1]}
        }
        self.crossnamespace[102] = {
            'pt': {
                '_default': [0],
                'als': [0, 104],
                'es': [0, 104],
                'fr': [0, 104],
                'lt': [0, 104]
            },
            'hr': {
                '_default': [0],
                'als': [0, 104],
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
        self.crossnamespace[12] = {
            'en': {
                '_default': [0],
            },
        }
        self.crossnamespace[13] = {
            'en': {
                '_default': [0],
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
        return '1.16alpha'

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
