# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wiktionary

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wiktionary'

        self.languages_by_size = [
            'en', 'fr', 'zh', 'mg', 'lt', 'ko', 'ru', 'tr', 'pl', 'ta', 'vi',
            'de', 'io', 'el', 'fi', 'pt', 'hu', 'kn', 'sv', 'nl', 'no', 'my',
            'it', 'hi', 'et', 'li', 'ja', 'ml', 'fa', 'es', 'lo', 'ku', 'ar',
            'ro', 'id', 'te', 'gl', 'ca', 'cs', 'uk', 'bg', 'eo', 'vo', 'oc',
            'eu', 'is', 'hr', 'br', 'simple', 'scn', 'th', 'sr', 'af', 'fy',
            'sw', 'tl', 'he', 'fj', 'cy', 'la', 'ast', 'sq', 'hy', 'da', 'sl',
            'tt', 'wa', 'zh-min-nan', 'ur', 'ka', 'az', 'lv', 'ne', 'tk', 'ps',
            'hsb', 'kk', 'nn', 'ky', 'wo', 'km', 'bs', 'ang', 'be', 'lb', 'ga',
            'co', 'mr', 'gn', 'ia', 'sk', 'csb', 'ms', 'st', 'nds', 'sd', 'kl',
            'sh', 'si', 'tg', 'ug', 'ti', 'mk', 'bn', 'nah', 'zu', 'an', 'gu',
            'chr', 'am', 'ss', 'qu', 'ts', 'fo', 'rw', 'kw', 'om', 'gv', 'iu',
            'su', 'mn', 'so', 'yi', 'ie', 'gd', 'za', 'pa', 'mt', 'mi', 'tpi',
            'dv', 'ik', 'jv', 'sg', 'roa-rup', 'uz', 'ln', 'sa', 'na', 'sm',
            'tn', 'ha', 'ay', 'ks', 'jbo', 'dz',
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wiktionary.org' % lang


        # CentralAuth cross avaliable projects.
        self.cross_projects = [
            'wikipedia', 'wikibooks', 'wikiquote', 'wikisource', 'wikinews', 'wikiversity',
            'meta', 'mediawiki', 'test', 'incubator', 'commons', 'species'
        ]
        # Global bot allowed languages on
        # http://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = [
            'ang', 'ast', 'az', 'bg', 'bn', 'da', 'eo', 'es', 'fa', 'fy', 'ga',
            'gd', 'hu', 'ia', 'ie', 'ik', 'jv', 'ka', 'li', 'lt', 'mk', 'nl',
            'no', 'oc', 'pt', 'sk', 'tg', 'th', 'ti', 'ts', 'ug', 'uk', 'vo',
            'za', 'zh-min-nan', 'zh', 'zu',
        ]

        # Other than most Wikipedias, page names must not start with a capital
        # letter on ALL Wiktionaries.
        self.nocapitalize = self.langs.keys()

        self.alphabetic_roman = [
            'aa', 'af', 'ak', 'als', 'an', 'roa-rup', 'ast', 'gn', 'ay', 'az',
            'id', 'ms', 'bm', 'zh-min-nan', 'jv', 'su', 'mt', 'bi', 'bo', 'bs',
            'br', 'ca', 'cs', 'ch', 'sn', 'co', 'za', 'cy', 'da', 'de', 'na',
            'mh', 'et', 'ang', 'en', 'es', 'eo', 'eu', 'to', 'fr', 'fy', 'fo',
            'ga', 'gv', 'sm', 'gd', 'gl', 'hr', 'io', 'ia', 'ie', 'ik', 'xh',
            'is', 'zu', 'it', 'kl', 'csb', 'kw', 'rw', 'rn', 'sw', 'ky', 'ku',
            'la', 'lv', 'lb', 'lt', 'li', 'ln', 'jbo', 'hu', 'mg', 'mi', 'mo',
            'my', 'fj', 'nah', 'nl', 'cr', 'no', 'nn', 'hsb', 'oc', 'om', 'ug',
            'uz', 'nds', 'pl', 'pt', 'ro', 'rm', 'qu', 'sg', 'sc', 'st', 'tn',
            'sq', 'scn', 'simple', 'ss', 'sk', 'sl', 'so', 'sh', 'fi', 'sv',
            'tl', 'tt', 'vi', 'tpi', 'tr', 'tw', 'vo', 'wa', 'wo', 'ts', 'yo',
            'el', 'av', 'ab', 'ba', 'be', 'bg', 'mk', 'mn', 'ru', 'sr', 'tg',
            'uk', 'kk', 'hy', 'yi', 'he', 'ur', 'ar', 'tk', 'sd', 'fa', 'ha',
            'ps', 'dv', 'ks', 'ne', 'pi', 'bh', 'mr', 'sa', 'hi', 'as', 'bn',
            'pa', 'gu', 'or', 'ta', 'te', 'kn', 'ml', 'si', 'th', 'lo', 'dz',
            'ka', 'ti', 'am', 'chr', 'iu', 'km', 'zh', 'ja', 'ko',
           ]


        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are put
        # after those, in code-alphabetical order.

        self.interwiki_putfirst = {
            'da': self.alphabetic,
            'en': self.alphabetic,
            'et': self.alphabetic,
            'fi': self.alphabetic,
            'fy': self.fyinterwiki,
            'he': ['en'],
            'hu': ['en'],
            'ms': self.alphabetic_revised,
            'pl': self.alphabetic_revised,
            'sv': self.alphabetic_roman,
            'simple': self.alphabetic,
        }

        self.obsolete = {
            'aa': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Afar_Wiktionary
            'ab': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Abkhaz_Wiktionary
            'ak': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Akan_Wiktionary
            'als': None, # http://als.wikipedia.org/wiki/Wikipedia:Stammtisch/Archiv_2008-1#Afterwards.2C_closure_and_deletion_of_Wiktionary.2C_Wikibooks_and_Wikiquote_sites
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
            'mo': 'ro', # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Moldovan_Wiktionary
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

        self.interwiki_on_one_line = ['pl']

        self.interwiki_attop = ['pl']

    def shared_image_repository(self, code):
        return ('commons', 'commons')
