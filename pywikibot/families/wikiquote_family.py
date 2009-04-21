# -*- coding: utf-8  -*-
import urllib
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wikiquote

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikiquote'

        self.languages_by_size = [
            'en', 'it', 'de', 'pl', 'pt', 'sk', 'ru', 'bg', 'bs', 'es',
            'sl', 'tr', 'he', 'fr', 'cs', 'zh', 'lt', 'id', 'uk', 'fa',
            'hu', 'sv', 'el', 'nl', 'no', 'ja', 'fi', 'ca', 'nn', 'ka',
            'et', 'simple', 'ku', 'ar', 'hr', 'eo', 'hy', 'ro', 'gl', 'ko',
            'ml', 'li', 'is', 'af', 'sr', 'th', 'da', 'sq', 'te', 'vi',
            'eu', 'la', 'az', 'br', 'hi', 'be', 'ast', 'uz', 'ang', 'zh-min-nan',
            'lb', 'mr', 'su', 'ur', 'ta', 'wo', 'ky', 'kn', 'gu', 'cy',
            'am', 'co', 'kk',
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikiquote.org' % lang

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

        alphabetic = ['af','am','ang','ar','roa-rup','ast','az','bn',
                    'zh-min-nan','bg','be','bs','br','ca','chr','co','cs','cy',
                    'da','de','als','et','el','en','es','eo','eu','fa','fr',
                    'fy','ga','gv','gu','gd','gl','ko','hy','hi','hr','io',
                    'id','ia','is','it','he','jv','kn','ka','ks','csb','kk',
                    'ky','sw','ku','la','lb','lt','li','hu','mk','mg','ml',
                    'mi','mr','zh-cfr','mn','nah','na','nl','ja','no','nb',
                    'nn','oc','om','nds','uz','pl','pt','ro','ru','sa','st',
                    'sq','si','simple','sk','sl','sr','su','fi','sv','ta','tt',
                    'te','th','ur','vi','tpi','tr','uk','vo','yi','yo','wo',
                    'za','zh','zh-cn','zh-tw']

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
        return '1.15alpha'

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
