# -*- coding: utf-8  -*-
import family, config

__version__ = '$Id$'

# The wikimedia family that is known as Wikisource

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikisource'

        self.languages_by_size = [
            'en', 'fr', 'es', 'zh', 'de', 'it', 'pt', 'ru', 'th', 'pl',
            'ro', 'te', 'hr', 'tr', 'he', 'cs', 'fi', 'nl', 'sr', 'sv',
            'hu', 'ar', 'la', 'ml', 'is', 'ja', 'bs', 'uk', 'el', 'ca',
            'ko', 'sl', 'bn', 'hy', 'no', 'da', 'id', 'ta', 'az', 'mk',
            'kn', 'bg', 'fa', 'vi', 'sk', 'cy', 'et', 'lt', 'gl',
            'zh-min-nan','yi', 'ht', 'fo', 'ang',
        ]

        self.langs = {
            '-': 'wikisource.org',
        }
        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikisource.org' % lang

        # Override defaults
        self.namespaces[2]['pl'] = 'Wikiskryba'
        self.namespaces[3]['pl'] = 'Dyskusja Wikiskryby'

        # Most namespaces are inherited from family.Family.
        # Translation used on all wikis for the different namespaces.
        # (Please sort languages alphabetically)
        # You only need to enter translations that differ from _default.
        self.namespaces[4] = {
            '_default': [u'Wikisource', self.namespaces[4]['_default']],
            'ang': u'Wicifruma',
            'ar': u'ويكي مصدر',
            'az': u'VikiMənbə',
            'bg': u'Уикиизточник',
            'bn': u'উইকিসংকলন',
            'bs': u'Wikizvor',
            'ca': u'Viquitexts',
            'cy': u'Wicitestun',
            'el': u'Βικιθήκη',
            'et': u'Vikitekstid',
            'fa': u'ویکی‌نبشته',
            'fi': u'Wikiaineisto',
            'fo': u'Wikiheimild',
            'he': u'ויקיטקסט',
            'hr': u'Wikizvor',
            'ht': u'Wikisòrs',
            'hu': u'Wikiforrás',
            'is': u'Wikiheimild',
            'la': u'Vicifons',
            'lt': u'Vikišaltiniai',
            'ml': u'വിക്കിഗ്രന്ഥശാല',
            'nb': u'Wikikilden',
            'no': u'Wikikilden',
            'pl': u'Wikiźródła',
            'ru': u'Викитека',
            'sl': u'Wikivir',
            'sr': u'Викизворник',
            'th': u'วิกิซอร์ซ',
            'tr': u'VikiKaynak',
            'yi': [u'װיקיביבליאָטעק', u'וויקיביבליאטעק'],
        }
        self.namespaces[5] = {
            '_default': [u'Wikisource talk', self.namespaces[5]['_default']],
            'ang': u'Wicifruma talk',
            'ar': u'نقاش ويكي مصدر',
            'az': u'VikiMənbə müzakirəsi',
            'bg': u'Уикиизточник беседа',
            'bn': u'উইকিসংকলন আলাপ',
            'bs': u'Razgovor s Wikizvor',
            'ca': u'Viquitexts Discussió',
            'cs': u'Wikisource diskuse',
            'cy': u'Sgwrs Wicitestun',
            'da': u'Wikisource-diskussion',
            'de': u'Wikisource Diskussion',
            'el': u'Βικιθήκη συζήτηση',
            'es': u'Wikisource Discusión',
            'et': u'Vikitekstid arutelu',
            'fa': u'بحث ویکی‌نبشته',
            'fi': u'Keskustelu Wikiaineistosta',
            'fo': u'Wikiheimild kjak',
            'fr': u'Discussion Wikisource',
            'gl': u'Conversa Wikisource',
            'he': u'שיחת ויקיטקסט',
            'hr': u'Razgovor o Wikizvoru',
            'ht': u'Diskisyon Wikisòrs',
            'hu': u'Wikiforrás vita',
            'hy': u'Wikisource քննարկում',
            'id': u'Pembicaraan Wikisource',
            'is': u'Wikiheimildspjall',
            'it': u'Discussioni Wikisource',
            'ja': u'Wikisource‐ノート',
            'kn': u'Wikisource ಚರ್ಚೆ',
            'ko': u'Wikisource토론',
            'la': u'Disputatio Vicifontis',
            'lt': u'Vikišaltiniai aptarimas',
            'mk': u'Разговор за Wikisource',
            'ml': u'വിക്കിഗ്രന്ഥശാല സംവാദം',
            'nb': u'Wikikilden-diskusjon',
            'nl': u'Overleg Wikisource',
            'no': u'Wikikilden-diskusjon',
            'pl': u'Dyskusja Wikiźródeł',
            'pt': u'Wikisource Discussão',
            'ro': u'Discuţie Wikisource',
            'ru': u'Обсуждение Викитеки',
            'sk': u'Diskusia k Wikisource',
            'sl': u'Pogovor o Wikiviru',
            'sr': u'Разговор о Викизворнику',
            'sv': u'Wikisourcediskussion',
            'ta': u'Wikisource பேச்சு',
            'te': u'Wikisource చర్చ',
            'th': u'คุยเรื่องวิกิซอร์ซ',
            'tr': u'VikiKaynak tartışma',
            'uk': u'Обговорення Wikisource',
            'vi': u'Thảo luận Wikisource',
            'yi': [u'װיקיביבליאָטעק רעדן', u'וויקיביבליאטעק רעדן'],
        }
        self.namespaces[100] = {
            'bg': u'Автор',
            'bn': u'লেখক',
            'en': u'Portal',
            'fa': [u'درگاه', u'Portal'],
            'fr': u'Transwiki',
            'he': u'קטע',
            'hu': u'Szerző',
            'hy': u'Հեղինակ',
            'nl': u'Hoofdportaal',
            'pt': u'Portal',
            'sl': u'Stran',
        }
        self.namespaces[101] = {
            'bg': u'Автор беседа',
            'bn': u'লেখক আলাপ',
            'en': u'Portal talk',
            'fa': [u'بحث درگاه', u'Portal talk'],
            'fr': u'Discussion Transwiki',
            'he': u'שיחת קטע',
            'hu': u'Szerző vita',
            'hy': u'Հեղինակի քննարկում',
            'nl': u'Overleg hoofdportaal',
            'pt': u'Portal Discussão',
            'sl': u'Pogovor o strani',
        }
        self.namespaces[102] = {
            'ar': u'مؤلف',
            'da': [u'Forfatter', u'Author'],
            'de': u'Seite',
            'en': u'Author',
            'fa': [u'مؤلف', u'Author'],
            'hy': u'Պորտալ',
            'it': u'Autore',
            'la': u'Scriptor',
            'nb': u'Forfatter',
            'no': u'Forfatter',
            'pt': u'Autor',
        }
        self.namespaces[103] = {
            'ar': u'نقاش المؤلف',
            'da': [u'Forfatterdiskussion', u'Author talk'],
            'de': u'Seite Diskussion',
            'en': u'Author talk',
            'fa': [u'بحث مؤلف', u'Author talk'],
            'hy': u'Պորտալի քննարկում',
            'it': u'Discussioni autore',
            'la': u'Disputatio Scriptoris',
            'nb': u'Forfatterdiskusjon',
            'no': u'Forfatterdiskusjon',
            'pt': u'Autor Discussão',
        }

        self.namespaces[104] = {
            'ar': u'صفحة',
            'de': u'Index',
            'en': u'Page',
            'fa': [u'برگه', u'Page'],
            'fr': u'Page',
            'he': u'עמוד',
            'hy': u'Էջ',
            'it': u'Progetto',
            'la': u'Pagina',
            'pt': u'Galeria',
            'ru': u'Страница',
            'sv': u'Sida',
            'te': [u'పేజీ', u'Page'],
        }

        self.namespaces[105] = {
            'ar': u'نقاش الصفحة',
            'de': u'Index Diskussion',
            'en': u'Page talk',
            'fa': [u'بحث برگه', u'Page talk'],
            'fr': u'Discussion Page',
            'he': u'שיחת עמוד',
            'hy': u'Էջի քննարկում',
            'it': u'Discussioni progetto',
            'la': u'Disputatio Paginae',
            'pt': u'Galeria Discussão',
            'ru': u'Обсуждение страницы',
            'sv': u'Siddiskussion',
            'te': [u'పేజీ చర్చ', u'Page talk'],
        }

        self.namespaces[106] = {
            'he': u'ביאור',
            'hy': u'Ինդեքս',
            'it': u'Portale',
            'pt': u'Página',
            'sv': u'Författare',
        }

        self.namespaces[107] = {
            'he': u'שיחת ביאור',
            'hy': u'Ինդեքսի քննարկում',
            'it': u'Discussioni portale',
            'pt': u'Página Discussão',
            'sv': u'Författardiskussion',
        }

        self.namespaces[108] = {
            'it': u'Pagina',
            'pt': u'Em Tradução',
            'sv': u'Index',
        }

        self.namespaces[109] = {
            'it': u'Discussioni pagina',
            'pt': u'Discussão Em Tradução',
            'sv': u'Indexdiskussion',
        }

        self.namespaces[110] = {
            'it': u'Indice',
            'pt': u'Anexo',
        }

        self.namespaces[111] = {
            'it': u'Discussioni indice',
            'pt': u'Anexo Discussão',
        }

        self.namespaces[112] = {
            'fr': u'Livre',
        }

        self.namespaces[113] = {
            'fr': u'Discussion Livre',
        }

        self.alphabetic = ['ang','ar','az','bg','bs','ca','cs','cy',
                      'da','de','el','en','es','et','fa','fi',
                      'fo','fr','gl','he','hr','ht','hu','id',
                      'is','it','ja', 'ko','la','lt','ml','nl',
                      'no','pl','pt','ro','ru','sk','sl','sr',
                      'sv','te','th','tr','uk','vi','yi','zh']

        self.obsolete = {
            'dk': 'da',
            'jp': 'ja',
            'minnan':'zh-min-nan',
            'nb': 'no',
            'tokipona': None,
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        self.interwiki_putfirst = {
            'en': self.alphabetic,
            'fi': self.alphabetic,
            'fr': self.alphabetic,
            'he': ['en'],
            'hu': ['en'],
            'pl': self.alphabetic,
            'simple': self.alphabetic
        }

    def version(self, code):
        return "1.12alpha"

    def shared_image_repository(self, code):
        return ('commons', 'commons')

