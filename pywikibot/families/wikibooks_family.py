# -*- coding: utf-8  -*-
import urllib
from pywikibot import family

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
        return '1.14alpha'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
