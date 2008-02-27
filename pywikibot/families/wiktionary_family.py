# -*- coding: utf-8  -*-
import urllib
from pywikibot import family
import config

__version__ = '$Id$'

# The Wikimedia family that is known as Wiktionary

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wiktionary'

        self.languages_by_size = [
            'fr', 'en', 'vi', 'tr', 'ru', 'io', 'zh', 'el', 'ar', 'pl',
            'fi', 'it', 'de', 'hu', 'sv', 'pt', 'ku', 'ko', 'id', 'te',
            'es', 'nl', 'ja', 'lt', 'bg', 'vo', 'gl', 'li', 'et', 'sr',
            'fa', 'is', 'ro', 'af', 'scn', 'br', 'sl', 'ta', 'hy', 'zh-min-nan',
            'no', 'he', 'la', 'sq', 'ur', 'simple', 'da', 'ca', 'ast', 'tlh',
            'fy', 'uk', 'cs', 'hr', 'sw', 'oc', 'ang', 'kk', 'ml', 'hi',
            'ia', 'co', 'csb', 'st', 'eo', 'sk', 'kl', 'nds', 'ms', 'ky',
            'ug', 'sd', 'ga', 'az', 'th', 'tt', 'mk', 'ti', 'gu', 'tl',
            'ts', 'fo', 'qu', 'rw', 'cy', 'bs', 'mr', 'su', 'an', 'ie',
            'chr', 'am', 'yi', 'wo', 'kn', 'mn', 'nah', 'gd', 'be', 'pa',
            'lv', 'zu', 'nn', 'km', 'ps', 'mi', 'so', 'dv', 'tg', 'bn',
            'mg', 'ha', 'ka', 'na', 'sa', 'gv', 'tpi', 'ay', 'ss', 'eu',
            'ne', 'jbo', 'uz', 'gn', 'tn', 'ch', 'as', 'mt', 'jv', 'pi',
            'sh', 'lb', 'ks', 'tk', 'iu', 'sg', 'fj', 'als', 'xh', 'ik',
            'kw', 'ln', 'sm', 'si', 'za', 'roa-rup', 'mh', 'ba', 'or', 'sn',
            'ak', 'bh', 'lo', 'bm', 'yo', 'bi', 'to', 'aa', 'av', 'rn',
            'dz', 'tw', 'om', 'ab', 'my', 'wa', 'sc', 'cr', 'bo', 'rm',
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wiktionary.org' % lang

        # Override defaults
        self.namespaces[2]['pl'] = u'Wikipedysta'
        self.namespaces[3]['pl'] = u'Dyskusja Wikipedysty'

        # Most namespaces are inherited from family.Family.
        # Translation used on all wikis for the different namespaces.
        # (Please sort languages alphabetically)
        # You only need to enter translations that differ from _default.
        self.namespaces[4] = {
            '_default': [u'Wiktionary', self.namespaces[4]['_default']],
            'ar': u'ويكاموس',
            'ast': u'Uiccionariu',
            'bg': u'Уикиречник',
            'bs': u'Vikirječnik',
            'ca': u'Viccionari',
            'cs': u'Wikislovník',
            'cy': u'Wiciadur',
            'eo': u'Vikivortaro',
            'es': u'Wikcionario',
            'et': u'Vikisõnaraamat',
            'fa': u'ویکی‌واژه',
            'fi': u'Wikisanakirja',
            'fo': u'Wiktionary',
            'fr': u'Wiktionnaire',
            'ga': u'Vicífhoclóir',
            'gu': u'વિક્ષનરી',
            'he': u'ויקימילון',
            'hi': u'विक्षनरी',
            'hr': u'Wječnik',
            'hu': u'Wikiszótár',
            'io': u'Wikivortaro',
            'is': u'Wikiorðabók',
            'it': u'Wikizionario',
            'ka': u'ვიქსიკონი',
            'kk': u'Уикисөздік',
            'ko': u'위키낱말사전',
            'la': u'Victionarium',
            'lt': u'Vikižodynas',
            'ml': u'വിക്കിനിഘണ്ടു',
            'ms': u'Wiktionary',
            'nl': u'WikiWoordenboek',
            'oc': u'Wikiccionari',
            'pl': u'Wikisłownik',
            'pt': u'Wikcionário',
            'ro': u'Wikţionar',
            'ru': u'Викисловарь',
            'sk': u'Wikislovník',
            'sl': u'Wikislovar',
            'sr': u'Викиречник',
            'tr': u'Vikisözlük',
            'tt': u'Wiktionary',
            'ur': u'وکی لغت',
            'uz': u'Vikilug‘at',
            'vo': u'Vükivödabuk',
            'yi': [u'װיקיװערטערבוך', u'וויקיווערטערבוך'],
        }

        self.namespaces[5] = {
            '_default': [u'Wiktionary talk', self.namespaces[5]['_default']],
            'ab': u'Обсуждение Wiktionary',
            'af': u'Wiktionarybespreking',
            'als': u'Wiktionary Diskussion',
            'an': u'Descusión Wiktionary',
            'ar': u'نقاش ويكاموس',
            'ast': u'Uiccionariu alderique',
            'av': u'Обсуждение Wiktionary',
            'ay': u'Wiktionary Discusión',
            'az': u'Wiktionary müzakirəsi',
            'ba': u'Wiktionary б-са фекер алышыу',
            'be': u'Wiktionary размовы',
            'bg': u'Уикиречник беседа',
            'bm': u'Discussion Wiktionary',
            'bn': u'Wiktionary আলাপ',
            'br': u'Kaozeadenn Wiktionary',
            'bs': u'Razgovor s Vikirječnikom',
            'ca': u'Viccionari Discussió',
            'cs': u'Wikislovník diskuse',
            'csb': u'Diskùsëjô Wiktionary',
            'cy': u'Sgwrs Wiciadur',
            'da': u'Wiktionary-diskussion',
            'de': u'Wiktionary Diskussion',
            'el': u'Wiktionary συζήτηση',
            'eo': u'Vikivortaro diskuto',
            'es': u'Wikcionario Discusión',
            'et': u'Vikisõnaraamat arutelu',
            'eu': u'Wiktionary eztabaida',
            'fa': u'بحث ویکی‌واژه',
            'fi': u'Keskustelu Wikisanakirjasta',
            'fo': u'Wiktionary kjak',
            'fr': u'Discussion Wiktionnaire',
            'fy': u'Wiktionary oerlis',
            'ga': u'Plé Vicífhoclóra',
            'gl': u'Conversa Wiktionary',
            'gn': u'Wiktionary Discusión',
            'gu': u'વિક્ષનરી talk',
            'he': u'שיחת ויקימילון',
            'hi': u'विक्षनरी वार्ता',
            'hr': u'Razgovor Wječnik',
            'hsb': u'Wiktionary diskusija',
            'hu': u'Wikiszótár vita',
            'hy': u'Wiktionary քննարկում',
            'ia': u'Discussion Wiktionary',
            'id': u'Pembicaraan Wiktionary',
            'io': u'Wikivortaro Debato',
            'is': [u'Wikiorðabókarspjall', u'Wikiorðabókspjall'],
            'it': u'Discussioni Wikizionario',
            'ja': u'Wiktionary‐ノート',
            'jv': u'Dhiskusi Wiktionary',
            'ka': u'ვიქსიკონი განხილვა',
            'kk': u'Уикисөздік талқылауы',
            'kn': u'Wiktionary ಚರ್ಚೆ',
            'ko': u'위키낱말사전토론',
            'ku': u'Wiktionary nîqaş',
            'la': u'Disputatio Victionarii',
            'lb': u'Wiktionary Diskussioun',
            'li': u'Euverlèk Wiktionary',
            'ln': u'Discussion Wiktionary',
            'lt': u'Vikižodyno aptarimas',
            'lv': u'Wiktionary diskusija',
            'mg': u'Discussion Wiktionary',
            'mk': u'Разговор за Wiktionary',
            'ml': u'വിക്കിനിഘണ്ടു സംവാദം',
            'mr': u'Wiktionary चर्चा',
            'ms': u'Perbincangan Wiktionary',
            'nah': u'Wiktionary Discusión',
            'nds': u'Wiktionary Diskuschoon',
            'nl': u'Overleg WikiWoordenboek',
            'nn': u'Wiktionary-diskusjon',
            'no': u'Wiktionary-diskusjon',
            'oc': u'Discussion Wikiccionari',
            'pa': u'Wiktionary ਚਰਚਾ',
            'pl': u'Wikidyskusja',
            'pt': u'Wikcionário Discussão',
            'qu': u'Wiktionary rimanakuy',
            'ro': u'Discuţie Wikţionar',
            'ru': u'Обсуждение Викисловаря',
            'sa': u'Wiktionaryसंभाषणं',
            'sc': u'Wiktionary discussioni',
            'scn': u'Discussioni Wiktionary',
            'sk': u'Diskusia k Wikislovníku',
            'sl': u'Pogovor o Wikislovarju',
            'sq': u'Wiktionary diskutim',
            'sr': u'Разговор о викиречнику',
            'su': u'Obrolan Wiktionary',
            'sv': u'Wiktionarydiskussion',
            'ta': u'Wiktionary பேச்சு',
            'te': u'Wiktionary చర్చ',
            'tg': u'Баҳси Wiktionary',
            'th': u'คุยเรื่องWiktionary',
            'tlh': u"Wiktionary ja'chuq",
            'tr': u'Vikisözlük tartışma',
            'tt': u'Wiktionary bäxäse',
            'uk': u'Обговорення Wiktionary',
            'ur': u'تبادلۂ خیال وکی لغت',
            'uz': u'Vikilug‘at munozarasi',
            'vi': u'Thảo luận Wiktionary',
            'vo': u'Bespik dö Vükivödabuk',
            'wa': u'Wiktionary copene',
            'wo': u'Discussion Wiktionary',
            'yi': [u'װיקיװערטערבוך רעדן', u'וויקיווערטערבוך רעדן'],
        }

        self.namespaces[100] = {
            'bg': u'Словоформи',
            'bs': u'Portal',
            'cy': u'Atodiad',
            'en': u'Appendix',
            'fi': u'Liite',
            'fr': u'Annexe',
            'he': u'נספח',
            'it': u'Appendice',
            'ko': u'부록',
            'lt': u'Sąrašas',
            'oc': u'Annèxa',
            'pl': u'Aneks',
            'pt': u'Apêndice',
            'ro': u'Portal',
            'ru': [u'Приложение', u'Appendix'],
            'sr': u'Портал',
            'sv': u'WT',
        }
        self.namespaces[101] = {
            'bg': u'Словоформи беседа',
            'bs': u'Razgovor o Portalu',
            'cy': u'Sgwrs Atodiad',
            'en': u'Appendix talk',
            'fi': u'Keskustelu liitteestä',
            'fr': u'Discussion Annexe',
            'he': u'שיחת נספח',
            'it': u'Discussioni appendice',
            'ko': u'부록 토론',
            'lt': u'Sąrašo aptarimas',
            'oc': u'Discussion Annèxa',
            'pl': u'Dyskusja aneksu',
            'pt': u'Apêndice Discussão',
            'ro': u'Discuţie Portal',
            'ru': [u'Обсуждение приложения', u'Appendix talk'],
            'sr': u'Разговор о порталу',
            'sv': u'WT-diskussion',
        }

        self.namespaces[102] = {
            'bs': u'Indeks',
            'cy': u'Odliadur',
            'de': u'Verzeichnis',
            'en': u'Concordance',
            'fr': u'Transwiki',
            'pl': u'Indeks',
            'pt': u'Vocabulário',
            'ro': u'Apendice',
            'ru': [u'Конкорданс', u'Concordance'],
            'sv': u'Appendix',
        }

        self.namespaces[103] = {
            'bs': u'Razgovor o Indeksu',
            'cy': u'Sgwrs Odliadur',
            'de': u'Verzeichnis Diskussion',
            'en': u'Concordance talk',
            'fr': u'Discussion Transwiki',
            'pl': u'Dyskusja indeksu',
            'pt': u'Vocabulário Discussão',
            'ro': u'Discuţie Apendice',
            'ru': [u'Обсуждение конкорданса', u'Concordance talk'],
            'sv': u'Appendixdiskussion',
        }

        self.namespaces[104] = {
            'bs': u'Dodatak',
            'cy': u'WiciSawrws',
            'en': u'Index',
            'fr': u'Portail',
            'pl': u'Portal',
            'pt': u'Rimas',
            'ru': [u'Индекс', u'Index'],
            'sv': u'Rimord',
        }

        self.namespaces[105] = {
            'bs': u'Razgovor o Dodatku',
            'cy': u'Sgwrs WiciSawrws',
            'en': u'Index talk',
            'fr': u'Discussion Portail',
            'pl': u'Dyskusja portalu',
            'pt': u'Rimas Discussão',
            'ru': [u'Обсуждение индекса', u'Index talk'],
            'sv': u'Rimordsdiskussion',
        }

        self.namespaces[106] = {
            'en': u'Rhymes',
            'is': u'Viðauki',
            'pt': u'Portal',
            'ru': [u'Рифмы', u'Rhymes'],
            'sv': u'Transwiki',
        }

        self.namespaces[107] = {
            'en': u'Rhymes talk',
            'is': u'Viðaukaspjall',
            'pt': u'Portal Discussão',
            'ru': [u'Обсуждение рифм', u'Rhymes talk'],
            'sv': u'Transwikidiskussion',
        }

        self.namespaces[108] = {
            'en': u'Transwiki',
        }

        self.namespaces[109] = {
            'en': u'Transwiki talk',
        }

        self.namespaces[110] = {
            'en': u'Wikisaurus',
        }

        self.namespaces[111] = {
            'en': u'Wikisaurus talk',
        }

        self.namespaces[112] = {
            'en': u'WT',
        }

        self.namespaces[113] = {
            'en': u'WT talk',
        }

        self.namespaces[114] = {
            'en': u'Citations',
        }

        self.namespaces[115] = {
            'en': u'Citations talk',
        }

        # Other than most Wikipedias, page names must not start with a capital
        # letter on ALL Wiktionaries.
        self.nocapitalize = self.langs.keys()

        self.obsolete = {
            'dk': 'da',
            'jp': 'ja',
            'mo': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Moldovan_Wiktionary
            'minnan':'zh-min-nan',
            'nb': 'no',
            'tokipona': None,
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are put
        # after those, in code-alphabetical order.

        self.interwiki_putfirst = {
            'en': self.alphabetic,
            'et': self.alphabetic,
            'fi': self.alphabetic,
            'fr': self.alphabetic,
            'he': ['en'],
            'hu': ['en'],
            'pl': self.alphabetic,
            'simple': self.alphabetic
        }

        self.interwiki_on_one_line = ['pl']

        self.interwiki_attop = ['pl']

    def version(self, code):
        return "1.12alpha"

    def shared_image_repository(self, code):
        return ('commons', 'commons')
