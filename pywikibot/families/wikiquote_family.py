# -*- coding: utf-8  -*-
import urllib
from pywikibot import family
import config

__version__ = '$Id$'

# The Wikimedia family that is known as Wikiquote

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikiquote'

        self.languages_by_size = [
            'en', 'de', 'it', 'pl', 'sk', 'pt', 'ru', 'bg', 'bs', 'es',
            'sl', 'tr', 'he', 'zh', 'fr', 'lt', 'cs', 'id', 'el', 'uk',
            'sv', 'hu', 'ja', 'no', 'nl', 'fa', 'fi', 'ca', 'ku', 'ar',
            'eo', 'ro', 'hr', 'gl', 'ko', 'li', 'is', 'et', 'af', 'nn',
            'ka', 'sr', 'ml', 'da', 'th', 'simple', 'vi', 'sq', 'te', 'la',
            'az', 'br', 'eu', 'hi', 'ast', 'uz', 'be', 'ang', 'zh-min-nan', 'lb',
            'mr', 'su', 'ur', 'kn', 'ta', 'wo', 'ky', 'gu', 'cy', 'hy',
            'am', 'tt', 'qu', 'co', 'bm', 'ug', 'kw', 'na', 'tk', 'vo',
            'ga', 'cr', 'nds', 'kk', 'kr', 'als', 'za', 'ks',
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikiquote.org' % lang

        # Most namespaces are inherited from family.Family.
        # Translation used on all wikis for the different namespaces.
        # (Please sort languages alphabetically)
        # You only need to enter translations that differ from _default.
        self.namespaces[4] = {
            '_default': [u'Wikiquote', self.namespaces[4]['_default']],
            'ar': u'ويكي الاقتباس',
            'bg': u'Уикицитат',
            'br': u'Wikiarroud',
            'bs': u'Wikicitati',
            'ca': u'Viquidites',
            'cs': u'Wikicitáty',
            'el': u'Βικιφθέγματα',
            'eo': u'Vikicitaro',
            'fa': u'ویکی‌گفتاورد',
            'fi': u'Wikisitaatit',
            'ga': u'Vicísliocht',
            'he': u'ויקיציטוט',
            'hr': u'Wikicitat',
            'hu': u'Wikidézet',
            'hy': u'Վիքիքաղվածք',
            'is': u'Wikivitnun',
            'ka': [u'ვიკიციტატა', u'Wikiquote'],
            'kk': u'Уикидәйек',
            'ko': u'위키인용집',
            'la': u'Vicicitatio',
            'ml': u'വിക്കി ചൊല്ലുകള്‍',
            'pl': u'Wikicytaty',
            'ro': u'Wikicitat',
            'ru': u'Викицитатник',
            'sk': u'Wikicitáty',
            'sl': u'Wikinavedek',
            'tr': u'Vikisöz',
            'ur': u'وکی اقتباسات',
            'uz': u'Vikiiqtibos',
        }

        self.namespaces[5] = {
            '_default': [u'Wikiquote talk', self.namespaces[5]['_default']],
            'af': u'Wikiquotebespreking',
            'als': u'Wikiquote Diskussion',
            'ar': u'نقاش ويكي الاقتباس',
            'ast': u'Wikiquote alderique',
            'az': u'Wikiquote müzakirəsi',
            'be': u'Wikiquote размовы',
            'bg': u'Уикицитат беседа',
            'bm': u'Discussion Wikiquote',
            'br': u'Kaozeadenn Wikiarroud',
            'bs': u'Razgovor s Wikicitatima',
            'ca': u'Viquidites Discussió',
            'cs': u'Wikicitáty diskuse',
            'cy': u'Sgwrs Wikiquote',
            'da': u'Wikiquote-diskussion',
            'de': u'Wikiquote Diskussion',
            'el': u'Βικιφθέγματα συζήτηση',
            'eo': u'Vikicitaro diskuto',
            'es': u'Wikiquote Discusión',
            'et': u'Wikiquote arutelu',
            'eu': u'Wikiquote eztabaida',
            'fa': u'بحث ویکی‌گفتاورد',
            'fi': u'Keskustelu Wikisitaatitista',
            'fr': u'Discussion Wikiquote',
            'ga': u'Plé Vicísliocht',
            'gl': u'Conversa Wikiquote',
            'he': u'שיחת ויקיציטוט',
            'hi': u'Wikiquote वार्ता',
            'hr': u'Razgovor Wikicitat',
            'hu': u'Wikidézet-vita',
            'hy': u'Վիքիքաղվածքի քննարկում',
            'id': u'Pembicaraan Wikiquote',
            'is': u'Wikivitnunspjall',
            'it': u'Discussioni Wikiquote',
            'ja': u'Wikiquote‐ノート',
            'ka': [u'ვიკიციტატა განხილვა', u'Wikiquote განხილვა'],
            'kk': u'Уикидәйек талқылауы',
            'kn': u'Wikiquote ಚರ್ಚೆ',
            'ko': u'위키인용집토론',
            'ku': u'Wikiquote nîqaş',
            'la': u'Disputatio Vicicitationis',
            'lb': u'Wikiquote Diskussioun',
            'li': u'Euverlèk Wikiquote',
            'lt': u'Wikiquote aptarimas',
            'ml': u'വിക്കി ചൊല്ലുകള്‍ സംവാദം',
            'mr': u'Wikiquote चर्चा',
            'nds': u'Wikiquote Diskuschoon',
            'nl': u'Overleg Wikiquote',
            'nn': u'Wikiquote-diskusjon',
            'no': u'Wikiquote-diskusjon',
            'pl': u'Dyskusja Wikicytatów',
            'pt': u'Wikiquote Discussão',
            'qu': u'Wikiquote rimanakuy',
            'ro': u'Discuţie Wikicitat',
            'ru': u'Обсуждение Викицитатника',
            'sk': u'Diskusia k Wikicitátom',
            'sl': u'Pogovor o Wikinavedku',
            'sq': u'Wikiquote diskutim',
            'sr': u'Разговор о Wikiquote',
            'su': u'Obrolan Wikiquote',
            'sv': u'Wikiquotediskussion',
            'ta': u'Wikiquote பேச்சு',
            'te': u'Wikiquote చర్చ',
            'th': u'คุยเรื่องWikiquote',
            'tr': u'Vikisöz tartışma',
            'tt': u'Wikiquote bäxäse',
            'uk': u'Обговорення Wikiquote',
            'ur': u'تبادلۂ خیال وکی اقتباسات',
            'uz': u'Vikiiqtibos munozarasi',
            'vi': u'Thảo luận Wikiquote',
            'vo': u'Bespik dö Wikiquote',
            'wo': u'Discussion Wikiquote',
        }

        self.namespaces[100] = {
            'de': u'Portal',
            'fr': u'Portail',
            'he': u'פורטל',
            'li': u'Portaol',
        }

        self.namespaces[101] = {
            'de': u'Portal Diskussion',
            'fr': u'Discussion Portail',
            'he': u'שיחת פורטל',
            'li': u'Euverlèk portaol',
        }

        self.namespaces[102] = {
            'fr': u'Projet',
            }

        self.namespaces[103] = {
            'fr': u'Discussion Projet',
            }

        self.namespaces[104] = {
            'fr': u'Référence',
            }

        self.namespaces[105] = {
            'fr': u'Discussion Référence',
            }

        self.namespaces[108] = {
            'fr': u'Transwiki',
            }

        self.namespaces[109] = {
            'fr': u'Discussion Transwiki',
            }

        self.disambiguationTemplates = {
            '_default': [u''],
            'ka':       [u'მრავალმნიშვნელოვანი', u'მრავმნიშ'],
            'pt':       [u'Desambiguação'],
            }

        # attop is a list of languages that prefer to have the interwiki
        # links at the top of the page.
        self.interwiki_attop = []

        # on_one_line is a list of languages that want the interwiki links
        # one-after-another on a single line
        self.interwiki_on_one_line = []

        # Similar for category
        self.category_attop = []

        # List of languages that want the category on_one_line.
        self.category_on_one_line = []

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are put
        # after those, in code-alphabetical order.

        alphabetic = ['af','ar','roa-rup','om','bg','be','bn','bs',
                    'ca','chr','co','cs','cy','da','de','als','et',
                    'el','en','es','eo','eu','fa','fr','fy','ga','gv',
                    'gd','gl','ko','hi','hr','io','id','ia','is','it',
                    'he','jv','ka','csb','ks','sw','la','lt','hu',
                    'mk','mg','ml','mi','mr','zh-cfr','mn','nah','na',
                    'nl','ja','no','nb','oc','nds','pl','pt','ro','ru',
                    'sa','st','sq','si','simple','sk','sl','sr','su',
                    'fi','sv','ta','tt','th','ur','vi',
                    'tpi','tr','uk','vo','yi','yo','za','zh','zh-cn',
                    'zh-tw']

        self.interwiki_putfirst = {
            'en': alphabetic,
            'fi': alphabetic,
            'fr': alphabetic,
            'he': ['en'],
            'hu': ['en'],
            'pl': alphabetic,
            'simple': alphabetic,
            'pt': alphabetic,
        }

        self.obsolete = {
            'als': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Alemannic_Wikiquote
            'bm': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bambara_Wikiquote
            'cr': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nehiyaw_Wikiquote
            'dk': 'da',
            'ga': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Gaeilge_Wikiquote
            'jp': 'ja',
            'kr': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kanuri_Wikiquote
            'ks': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kashmiri_Wikiquote
            'kw': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kernewek_Wikiquote
            'minnan':'zh-min-nan',
            'na': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nauruan_Wikiquote
            'nb': 'no',
            'nds': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Low_Saxon_Wikiquote
            'qu': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Quechua_Wikiquote
            'tk': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Turkmen_Wikiquote
            'tokipona': None,
            'tt': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tatar_Wikiquote
            'ug': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Oyghurque_Wikiquote
            'vo': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Volapuk_Wikiquote
            'za':None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Zhuang_Wikiquote
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

    def version(self, code):
        return '1.14alpha'

    def code2encodings(self, code):
        """
        Return a list of historical encodings for a specific language wikipedia
        """
        # Historic compatibility
        if code == 'pl':
            return 'utf-8', 'iso8859-2'
        if code == 'ru':
            return 'utf-8', 'iso8859-5'
        return self.code2encoding(code),

    def shared_image_repository(self, code):
        return ('commons', 'commons')
