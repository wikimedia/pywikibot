# -*- coding: utf-8  -*-
import urllib
from pywikibot import family
import config

__version__ = '$Id$'

# The Wikimedia family that is known as Wikibooks

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikibooks'

        self.languages_by_size = [
            'en', 'de', 'fr', 'pt', 'hu', 'es', 'it', 'ja', 'pl', 'nl',
            'he', 'sq', 'fi', 'sv', 'hr', 'da', 'vi', 'mk', 'cs', 'ru',
            'zh', 'fa', 'is', 'id', 'ta', 'tr', 'no', 'ar', 'ka', 'eo',
            'ko', 'th', 'bg', 'ca', 'lt', 'gl', 'simple', 'ro', 'sk', 'ia',
            'sr', 'ang', 'mr', 'uk', 'sl', 'als', 'et', 'oc', 'el', 'ur',
            'la', 'ml', 'cv', 'ie', 'hi', 'fy', 'lv', 'tl', 'hy', 'eu',
            'ky', 'bn', 'pa', 'bs', 'ms', 'be', 'tg', 'te', 'af', 'cy',
            'ast', 'sa', 'tt', 'az', 'ku', 'mg', 'si', 'co', 'sw', 'tk',
            'ne', 'qu', 'bm', 'ak', 'vo', 'uz', 'bo', 'su',
            'na', 'se', 'ps', 'kn', 'kk', 'zh-min-nan', 'ay', 'lb', 'got', 'nah',
            'aa', 'mn', 'ch', 'gn', 'ln', 'km', 'nds',
            'xh', 'rm', 'ba', 'za', 'bi', 'my', 'wa', 'zu', 'mi',
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikibooks.org' % lang

        # Override defaults
        self.namespaces[2]['pl'] = u'Wikipedysta'
        self.namespaces[3]['pl'] = u'Dyskusja Wikipedysty'

        # Most namespaces are inherited from family.Family.
        # Translation used on all wikis for the different namespaces.
        # (Please sort languages alphabetically)
        # You only need to enter translations that differ from _default.
        self.namespaces[4] = {
            '_default': [u'Wikibooks', self.namespaces[4]['_default']],
            'ar': u'ويكي الكتب',
            'bg': u'Уикикниги',
            'bs': u'Wikiknjige',
            'ca': u'Viquillibres',
            'cs': u'Wikiknihy',
            'cy': u'Wicillyfrau',
            'el': u'Βικιβιβλία',
            'eo': u'Vikilibroj',
            'es': u'Wikilibros',
            'fa': u'ویکی‌نسک',
            'fi': u'Wikikirjasto',
            'fr': u'Wikilivres',
            'ga': u'Vicíleabhair',
            'he': u'ויקיספר',
            'hr': u'Wikiknjige',
            'hu': u'Wikikönyvek',
            'hy': u'Վիքիգրքեր',
            'is': u'Wikibækur',
            'ka': u'ვიკიწიგნები',
            'kk': u'Уикикітап',
            'ko': u'위키책',
            'la': u'Vicilibri',
            'ml': u'വിക്കിപാഠശാല',
            'no': u'Wikibøker',
            'oc': u'Wikilibres',
            'ro': u'Wikimanuale',
            'ru': u'Викиучебник',
            'sl': u'Wikiknjige',
            'sr': u'Викикњиге',
            'tr': u'Vikikitap',
            'uk': u'Вікіпідручник',
            'ur': u'وکی کتب',
            'uz': u'Vikikitob',
            'vo': u'Vükibuks',
        }

        self.namespaces[5] = {
            '_default': [u'Wikibooks talk', self.namespaces[5]['_default']],
            'af': u'Wikibooksbespreking',
            'als': u'Wikibooks Diskussion',
            'ar': u'نقاش ويكي الكتب',
            'ast': u'Wikibooks alderique',
            'ay': u'Wikibooks Discusión',
            'az': u'Wikibooks müzakirəsi',
            'ba': u'Wikibooks б-са фекер алышыу',
            'be': u'Wikibooks размовы',
            'bg': u'Уикикниги беседа',
            'bm': u'Discussion Wikibooks',
            'bn': u'Wikibooks আলাপ',
            'bs': u'Razgovor s Wikiknjigama',
            'ca': u'Viquillibres Discussió',
            'cs': u'Wikiknihy diskuse',
            'cv': u'Wikibooks сӳтсе явмалли',
            'cy': u'Sgwrs Wicillyfrau',
            'da': u'Wikibooks-diskussion',
            'de': u'Wikibooks Diskussion',
            'el': u'Βικιβιβλία συζήτηση',
            'eo': u'Vikilibroj diskuto',
            'es': u'Wikilibros Discusión',
            'et': u'Wikibooks arutelu',
            'eu': u'Wikibooks eztabaida',
            'fa': u'بحث ویکی‌نسک',
            'fi': u'Keskustelu Wikikirjastosta',
            'fr': u'Discussion Wikilivres',
            'fy': u'Wikibooks oerlis',
            'ga': u'Plé Vicíleabhar',
            'gl': u'Conversa Wikibooks',
            'gn': u'Wikibooks myangekõi',
            'he': u'שיחת ויקיספר',
            'hi': u'Wikibooks वार्ता',
            'hr': u'Razgovor Wikiknjige',
            'hu': u'Wikikönyvek vita',
            'hy': u'Վիքիգրքերի քննարկում',
            'ia': u'Discussion Wikibooks',
            'id': u'Pembicaraan Wikibooks',
            'is': u'Wikibækurspjall',
            'it': u'Discussioni Wikibooks',
            'ja': u'Wikibooks‐ノート',
            'ka': u'ვიკიწიგნები განხილვა',
            'kk': u'Уикикітап талқылауы',
            'km': u'ការពិភាក្សាអំពីWikibooks',
            'kn': u'Wikibooks ಚರ್ಚೆ',
            'ko': u'위키책토론',
            'ku': u'Wikibooks nîqaş',
            'la': u'Disputatio Vicilibrorum',
            'lb': u'Wikibooks Diskussioun',
            'ln': u'Discussion Wikibooks',
            'lt': u'Wikibooks aptarimas',
            'lv': u'Wikibooks diskusija',
            'mg': u'Discussion Wikibooks',
            'mk': u'Разговор за Wikibooks',
            'ml': u'വിക്കിപാഠശാല സംവാദം',
            'mr': u'Wikibooks चर्चा',
            'ms': u'Perbincangan Wikibooks',
            'nah': u'Wikibooks Discusión',
            'nds': u'Wikibooks Diskuschoon',
            'nl': u'Overleg Wikibooks',
            'no': u'Wikibøker-diskusjon',
            'oc': u'Discussion Wikilibres',
            'pa': u'Wikibooks ਚਰਚਾ',
            'pl': u'Dyskusja Wikibooks',
            'ps': u'د Wikibooks خبرې اترې',
            'pt': u'Wikibooks Discussão',
            'qu': u'Wikibooks rimanakuy',
            'ro': u'Discuţie Wikimanuale',
            'ru': u'Обсуждение Викиучебника',
            'sa': u'Wikibooksसंभाषणं',
            'si': u'Wikibooks සාකච්ඡාව',
            'sk': u'Diskusia k Wikibooks',
            'sl': u'Pogovor o Wikiknjigah',
            'sq': u'Wikibooks diskutim',
            'sr': u'Разговор о викикњигама',
            'su': u'Obrolan Wikibooks',
            'sv': u'Wikibooksdiskussion',
            'ta': u'Wikibooks பேச்சு',
            'te': u'Wikibooks చర్చ',
            'tg': u'Баҳси Wikibooks',
            'th': u'คุยเรื่องWikibooks',
            'tr': u'Vikikitap tartışma',
            'tt': u'Wikibooks bäxäse',
            'uk': u'Обговорення Вікіпідручника',
            'ur': u'تبادلۂ خیال وکی کتب',
            'uz': u'Vikikitob munozarasi',
            'vi': u'Thảo luận Wikibooks',
            'vo': u'Bespik dö Vükibuks',
            'wa': u'Wikibooks copene',
        }

        self.namespaces[100] = {
            'fr': u'Transwiki',
            'he': u'שער',
            'id': u'Resep',
            'it': u'Progetto',
            'ja': u'Transwiki',
            'ms': u'Resipi',
            'ro': u'Raft',
            'ru': u'Полка',
            'tr': u'Yemek',
            'uk': u'Полиця',
        }

        self.namespaces[101] = {
            'fr': u'Discussion Transwiki',
            'he': u'שיחת שער',
            'id': u'Pembicaraan Resep',
            'it': u'Discussioni progetto',
            'ja': u'Transwiki‐ノート',
            'ms': u'Perbualan Resipi',
            'ro': u'Discuţie Raft',
            'ru': u'Обсуждение полки',
            'tr': u'Yemek tartışma',
            'uk': u'Обговорення полиці',
        }

        self.namespaces[102] = {
            'cy': u'Silff lyfrau',
            'de': u'Regal',
            'en': u'Cookbook',
            'es': u'Wikiversidad',
            'id': u'Wisata',
            'it': u'Ripiano',
            'nl': u'Transwiki',
            'ro': u'Wikijunior',
            'ru': u'Импортировано',
            'sr': u'Кувар',
            'uk': u'Рецепт',
        }

        self.namespaces[103] = {
            'cy': u'Sgwrs Silff lyfrau',
            'de': u'Regal Diskussion',
            'en': u'Cookbook talk',
            'es': u'Wikiversidad Discusión',
            'id': u'Pembicaraan Wisata',
            'it': u'Discussioni ripiano',
            'nl': u'Overleg transwiki',
            'ro': u'Discuţie Wikijunior',
            'ru': u'Обсуждение импортированного',
            'sr': u'Разговор о кувару',
            'uk': u'Обговорення рецепта',
        }

        self.namespaces[104] = {
            'he': u'מדף',
            'ka': u'თარო',
            'nl': u'Wikijunior',
            'ro': u'Carte de bucate',
            'ru': u'Рецепт',
        }

        self.namespaces[105] = {
            'he': u'שיחת מדף',
            'ka': u'თარო განხილვა',
            'nl': u'Overleg Wikijunior',
            'ro': u'Discuţie Carte de bucate',
            'ru': u'Обсуждение рецепта',
        }

        self.namespaces[106] = {
            'ru': u'Задача',
        }

        self.namespaces[107] = {
            'ru': u'Обсуждение задачи',
        }

        self.namespaces[108] = {
            'en': u'Transwiki',
        }

        self.namespaces[109] = {
            'en': u'Transwiki talk',
        }

        self.namespaces[110] = {
            'en': u'Wikijunior',
        }

        self.namespaces[111] = {
            'en': u'Wikijunior talk',
        }

        self.namespaces[112] = {
            'en': u'Subject',
        }

        self.namespaces[113] = {
            'en': u'Subject talk',
        }

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are put
        # after those, in code-alphabetical order.

        alphabetic = ['af','ar','roa-rup','om','bg','be','bn','bs',
                      'ca','chr','co','cs','cy','da','de','als','et',
                      'el','en','es','eo','eu','fa','fr','fy','gv',
                      'gd','gl','ko','hi','hr','io','id','ia','is','it',
                      'he','jv','ka','csb','sw','la','lv','lt','hu',
                      'mk','mg','ml','mi','mr','ms','zh-cfr','mn','nah','na',
                      'nl','ja','no','nb','oc','nds','pl','pt','ro','ru',
                      'sa','st','sq','si','simple','sk','sl','sr','su',
                      'fi','sv','ta','tt','th','ur','vi',
                      'tpi','tr','uk','vo','yi','za','zh','zh-cn',
                      'zh-tw']

        self.obsolete = {
            'aa': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Afar_Wikibooks
            'ak': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Akan_Wikibooks
            'as': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Assamese_Wikibooks
            'ay': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Aymar_Wikibooks
            'ba': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bashkir_Wikibooks
            'bi': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bislama_Wikibooks
            'bm': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bambara_Wikibooks
            'bo': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tibetan_Wikibooks
            'ch': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Chamorro_Wikibooks
            'dk': 'da',
            'ga':None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Gaeilge_Wikibooks
            'got': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Gothic_Wikibooks
            'gn': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Guarani_Wikibooks
            'gu': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Gujarati_Wikibooks
            'jp': 'ja',
            'ks': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kashmiri_Wikibooks
            'ln': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Lingala_Wikibooks
            'mi': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Maori_Wikibooks
            'minnan':'zh-min-nan',
            'nah': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nahuatl_Wikibooks
            'nb': 'no',
            'qu': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Quechua_Wikibooks
            'rm': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Rumantsch_Wikibooks
            'se': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Sami_Wikibooks
            'tokipona': None,
            'ug': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Uyghur_Wikibooks
            'yo': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Yoruba_Wikibooks
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        self.interwiki_putfirst = {
            'en': alphabetic,
            'fi': alphabetic,
            'fr': alphabetic,
            'he': ['en'],
            'hu': ['en'],
            'pl': alphabetic,
            'simple': alphabetic
        }

    def version(self, code):
        return '1.13alpha'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
