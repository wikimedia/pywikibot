# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wikibooks

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikibooks'

        self.languages_by_size = [
            'en', 'de', 'fr', 'hu', 'pt', 'ja', 'es', 'nl', 'it', 'pl',
            'he', 'sq', 'fi', 'vi', 'ru', 'cs', 'hr', 'th', 'zh', 'da',
            'sv', 'mk', 'tr', 'sr', 'fa', 'tl', 'id', 'is', 'ca', 'ta',
            'ar', 'no', 'ko', 'eo', 'ka', 'simple', 'bg', 'gl', 'lt', 'ro',
            'sk', 'la', 'el', 'ia', 'ang', 'sl', 'et', 'mr', 'cv', 'ur',
            'oc', 'ml', 'uk', 'ms', 'eu', 'fy', 'lv', 'hi', 'ie', 'tg',
            'bn', 'hy', 'af', 'az', 'te', 'pa', 'bs', 'ky', 'be', 'sa',
            'zh-min-nan', 'ast', 'cy', 'tt', 'mg', 'km', 'si', 'ku', 'co', 'sw',
            'tk', 'ne', 'als', 'uz', 'vo', 'su', 'na', 'mn', 'lb', 'kn',
            'ps', 'xh', 'kk', 'za', 'nds', 'wa', 'zu', 'my',
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikibooks.org' % lang

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are put
        # after those, in code-alphabetical order.

        alphabetic = ['af', 'ar', 'roa-rup', 'om', 'bg', 'be', 'bn', 'bs',
                      'ca', 'chr', 'co', 'cs', 'cy', 'da', 'de', 'als', 'et',
                      'el', 'en', 'es', 'eo', 'eu', 'fa', 'fr', 'fy', 'gv',
                      'gd', 'gl', 'ko', 'hi', 'hr', 'io', 'id', 'ia', 'is', 'it',
                      'he', 'jv', 'ka', 'csb', 'sw', 'la', 'lv', 'lt', 'hu',
                      'mk', 'mg', 'ml', 'mi', 'mr', 'ms', 'zh-cfr', 'mn', 'nah', 'na',
                      'nl', 'ja', 'no', 'nb', 'oc', 'nds', 'pl', 'pt', 'ro', 'ru',
                      'sa', 'st', 'sq', 'si', 'simple', 'sk', 'sl', 'sr', 'su',
                      'fi', 'sv', 'ta', 'tt', 'th', 'ur', 'vi',
                      'tpi', 'tr', 'uk', 'vo', 'yi', 'za', 'zh', 'zh-cn',
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
            'km': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Khmer_Wikibooks
            'ks': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kashmiri_Wikibooks
            'lb': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_L%C3%ABtzebuergesch_Wikibooks
            'ln': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Lingala_Wikibooks
            'lv': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Latvian_Wikibooks
            'mi': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Maori_Wikibooks
            'minnan':'zh-min-nan',
            'nah': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nahuatl_Wikibooks
            'nb': 'no',
            'ps': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Pashto_Wikibooks
            'qu': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Quechua_Wikibooks
            'rm': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Rumantsch_Wikibooks
            'se': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Sami_Wikibooks
            'tokipona': None,
            'ug': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Uyghur_Wikibooks
            'wa': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Walon_Wikibooks
            'xh': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Xhosa_Wikibooks
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
        # Global bot allowed languages on http://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = ['fa', 'fy', 'it', 'ru', 'simple', 'zh']

    def version(self, code):
        return '1.16alpha'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
