# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wiktionary

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wiktionary'

        self.languages_by_size = [
            'fr', 'en', 'tr', 'lt', 'vi', 'ru', 'io', 'zh', 'el', 'pl',
            'fi', 'no', 'hu', 'it', 'ta', 'sv', 'de', 'ko', 'lo', 'pt',
            'nl', 'ku', 'ja', 'es', 'id', 'te', 'ro', 'et', 'gl', 'bg',
            'ca', 'ar', 'vo', 'uk', 'fa', 'is', 'sr', 'af', 'sw', 'scn',
            'fy', 'th', 'br', 'oc', 'simple', 'li', 'cs', 'he', 'sl', 'hy',
            'sq', 'tt', 'la', 'zh-min-nan', 'da', 'ast', 'tk', 'ur', 'wa', 'hsb',
            'kk', 'ml', 'ky', 'hr', 'wo', 'kn', 'ang', 'eo', 'hi', 'gn',
            'ga', 'ia', 'az', 'co', 'sk', 'csb', 'st', 'ms', 'nds', 'kl',
            'sd', 'ug', 'ti', 'tl', 'mk', 'ka', 'an', 'my', 'gu', 'km',
            'lv', 'cy', 'ts', 'qu', 'eu', 'fo', 'bs', 'am', 'rw', 'mr',
            'su', 'chr', 'mn', 'nah', 'om', 'ie', 'yi', 'be', 'iu', 'mg',
            'sh', 'gd', 'nn', 'bn', 'zu', 'si', 'pa', 'mt', 'dv', 'tpi',
            'mi', 'roa-rup', 'jv', 'tg', 'ps', 'ik', 'so', 'uz', 'ha', 'gv',
            'ss', 'kw', 'sa', 'ay', 'na', 'jbo', 'ne', 'tn', 'sm', 'sg',
            'lb', 'ks', 'fj', 'ln', 'za', 'dz', 'als',
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wiktionary.org' % lang

        # Other than most Wikipedias, page names must not start with a capital
        # letter on ALL Wiktionaries.
        self.nocapitalize = self.langs.keys()

        # Global bot allowed languages on http://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = [
            'ang', 'ast', 'az', 'bg', 'bn', 'da', 'eo', 'es', 'fa', 'fy', 'ga', 'gd', 'hu', 
            'ia', 'ie', 'ik', 'jv', 'ka', 'li', 'lt', 'mk', 'nl', 'no', 'pt', 'sk', 'tg', 'th', 'ti', 
            'ts', 'ug', 'uk', 'vo', 'za', 'zh-min-nan', 'zh', 'zu', 
        ]
        self.obsolete = {
            'aa': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Afar_Wiktionary
            'ab': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Abkhaz_Wiktionary
            'ak': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Akan_Wiktionary
            'as': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Assamese_Wiktionary
            'av': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Avar_Wiktionary
            'ba': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bashkir_Wiktionary
            'bh': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bihari_Wiktionary
            'bi': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bislama_Wiktionary
            'bm': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bambara_Wiktionary
            'bo': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tibetan_Wiktionary
            'ch': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Chamorro_Wiktionary
            'cr': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nehiyaw_Wiktionary
            'dk': 'da',
            'jp': 'ja',
            'mh': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Marshallese_Wiktionary
            'mo': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Moldovan_Wiktionary
            'minnan':'zh-min-nan',
            'nb': 'no',
            'or': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Oriya_Wiktionary
            'pi': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Pali_Bhasa_Wiktionary
            'rm': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Rhaetian_Wiktionary
            'rn': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kirundi_Wiktionary
            'sc': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Sardinian_Wiktionary
            'sn': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Shona_Wiktionary
            'to': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tongan_Wiktionary
            'tlh': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Klingon_Wiktionary
            'tw': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Twi_Wiktionary
            'tokipona': None,
            'xh': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Xhosa_Wiktionary
            'yo': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Yoruba_Wiktionary
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        # Order for fy: alphabetical by code, but y counts as i
        # TODO: This code is duplicated from wikipedia_family.py
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
            'et': self.alphabetic,
            'fi': self.alphabetic,
            'fy': self.fyinterwiki,
            'he': ['en'],
            'hu': ['en'],
            'pl': self.alphabetic,
            'simple': self.alphabetic
        }

        self.interwiki_on_one_line = ['pl']

        self.interwiki_attop = ['pl']

    def version(self, code):
        return '1.16alpha-wmf'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
