# -*- coding: utf-8  -*-
"""Family module for Wiktionary."""

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wiktionary
class Family(family.WikimediaFamily):

    """Family class for Wiktionary."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'wiktionary'

        self.languages_by_size = [
            'en', 'mg', 'fr', 'sh', 'zh', 'es', 'lt', 'ru', 'el', 'pl', 'nl',
            'sv', 'ko', 'it', 'de', 'ku', 'tr', 'ta', 'hu', 'fi', 'kn', 'io',
            'vi', 'pt', 'chr', 'no', 'ml', 'id', 'my', 'ja', 'li', 'ro', 'et',
            'te', 'ca', 'jv', 'fa', 'cs', 'ar', 'eu', 'gl', 'lo', 'uk', 'hy',
            'br', 'fj', 'th', 'eo', 'bg', 'hr', 'ps', 'uz', 'az', 'oc', 'is',
            'cy', 'vo', 'simple', 'zh-min-nan', 'da', 'scn', 'sr', 'ast', 'af',
            'he', 'sw', 'or', 'hi', 'fy', 'tl', 'wa', 'nn', 'ur', 'la', 'sq',
            'pnb', 'ka', 'sm', 'sl', 'nah', 'lv', 'tt', 'lb', 'bs', 'kk', 'nds',
            'sk', 'tk', 'hsb', 'mk', 'ky', 'be', 'km', 'ms', 'ga', 'wo', 'sa',
            'ang', 'mn', 'co', 'tg', 'gn', 'mr', 'ug', 'csb', 'st', 'so', 'ia',
            'sd', 'si', 'vec', 'kl', 'an', 'jbo', 'ln', 'fo', 'bn', 'zu', 'gv',
            'kw', 'gu', 'rw', 'om', 'na', 'qu', 'ss', 'ie', 'mt', 'pa',
            'roa-rup', 'iu', 'su', 'am', 'mi', 'ne', 'gd', 'tpi', 'yi',
            'ti', 'sg', 'tn', 'dv', 'ts', 'ha', 'ks', 'ay',
        ]

        self.langs = dict([(lang, '%s.wiktionary.org' % lang)
                           for lang in self.languages_by_size])

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = [
            'am', 'an', 'ang', 'ast', 'ay', 'az', 'be', 'bg', 'bn', 'br', 'bs',
            'ca', 'chr', 'co', 'cy', 'da', 'dv', 'eo', 'es', 'et', 'eu', 'fa',
            'fi', 'fj', 'fo', 'fy', 'ga', 'gd', 'gl', 'gn', 'gv', 'hu', 'ia',
            'id', 'ie', 'io', 'jv', 'ka', 'kl', 'kn', 'ku', 'ky', 'lb', 'lo',
            'lt', 'lv', 'mg', 'mk', 'ml', 'mn', 'my', 'ne', 'nl', 'no', 'oc',
            'or', 'pt', 'sh', 'simple', 'sk', 'sl', 'sm', 'su', 'tg', 'th',
            'ti', 'tk', 'tn', 'tpi', 'ts', 'ug', 'uk', 'vo', 'wa', 'wo', 'zh',
            'zh-min-nan', 'zu',
        ]

        # Other than most Wikipedias, page names must not start with a capital
        # letter on ALL Wiktionaries.
        self.nocapitalize = list(self.langs.keys())

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are
        # put after those, in code-alphabetical order.

        self.alphabetic_sv = [
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
            'pa', 'pnb', 'gu', 'or', 'ta', 'te', 'kn', 'ml', 'si', 'th', 'lo',
            'dz', 'ka', 'ti', 'am', 'chr', 'iu', 'km', 'zh', 'ja', 'ko',
        ]

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
            'sv': self.alphabetic_sv,
            'simple': self.alphabetic,
        }

        self.obsolete = {
            'aa': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Afar_Wiktionary
            'ab': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Abkhaz_Wiktionary
            'ak': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Akan_Wiktionary
            'als': None,  # https://als.wikipedia.org/wiki/Wikipedia:Stammtisch/Archiv_2008-1#Afterwards.2C_closure_and_deletion_of_Wiktionary.2C_Wikibooks_and_Wikiquote_sites
            'as': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Assamese_Wiktionary
            'av': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Avar_Wiktionary
            'ba': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bashkir_Wiktionary
            'bh': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bihari_Wiktionary
            'bi': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bislama_Wiktionary
            'bm': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bambara_Wiktionary
            'bo': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tibetan_Wiktionary
            'ch': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Chamorro_Wiktionary
            'cr': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nehiyaw_Wiktionary
            'dk': 'da',
            'dz': None,
            'ik': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Inupiak_Wiktionary
            'jp': 'ja',
            'mh': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Marshallese_Wiktionary
            'mo': 'ro',  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Moldovan_Wiktionary
            'minnan': 'zh-min-nan',
            'nb': 'no',
            'pi': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Pali_Bhasa_Wiktionary
            'rm': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Rhaetian_Wiktionary
            'rn': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kirundi_Wiktionary
            'sc': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Sardinian_Wiktionary
            'sn': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Shona_Wiktionary
            'to': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tongan_Wiktionary
            'tlh': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Klingon_Wiktionary
            'tw': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Twi_Wiktionary
            'tokipona': None,
            'xh': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Xhosa_Wiktionary
            'yo': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Yoruba_Wiktionary
            'za': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Zhuang_Wiktionary
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        self.interwiki_on_one_line = ['pl']

        self.interwiki_attop = ['pl']
