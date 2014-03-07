# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikisource
class Family(family.WikimediaFamily):
    def __init__(self):
        super(Family, self).__init__()
        self.name = 'wikisource'

        self.languages_by_size = [
            'fr', 'en', 'de', 'ru', 'it', 'pl', 'zh', 'he', 'es', 'sv', 'pt',
            'ca', 'cs', 'fa', 'hu', 'ar', 'ml', 'ko', 'sl', 'ro', 'te', 'fi',
            'vi', 'sa', 'sr', 'el', 'bn', 'hr', 'no', 'th', 'hy', 'is', 'nl',
            'la', 'gu', 'ja', 'vec', 'uk', 'br', 'eo', 'tr', 'mk', 'yi', 'ta',
            'id', 'be', 'da', 'az', 'li', 'et', 'as', 'mr', 'bg', 'bs', 'sah',
            'gl', 'kn', 'lt', 'cy', 'sk', 'zh-min-nan', 'fo',
        ]

        self.langs = dict([(lang, '%s.wikisource.org' % lang)
                           for lang in self.languages_by_size])
        self.langs['-'] = 'wikisource.org'

        # Global bot allowed languages on http://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = [
            'ca', 'el', 'fa', 'it', 'ko', 'no', 'pl', 'vi', 'zh',
        ]

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are
        # put after those, in code-alphabetical order.
        self.interwiki_putfirst = {
            'en': self.alphabetic,
            'fi': self.alphabetic,
            'fr': self.alphabetic,
            'he': ['en'],
            'hu': ['en'],
            'pl': self.alphabetic,
            'simple': self.alphabetic
        }

        self.obsolete = {
            'ang': None,  # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Old_English_Wikisource
            'dk': 'da',
            'ht': None,   # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Haitian_Creole_Wikisource
            'jp': 'ja',
            'minnan': 'zh-min-nan',
            'nb': 'no',
            'tokipona': None,
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        self.authornamespaces = {
            '_default': [0],
            'ar': [102],
            'be': [102],
            'bg': [100],
            'ca': [106],
            'cs': [100],
            'da': [102],
            'en': [102],
            'eo': [102],
            'et': [106],
            'fa': [102],
            'fr': [102],
            'he': [108],
            'hr': [100],
            'hu': [100],
            'hy': [100],
            'it': [102],
            'ko': [100],
            'la': [102],
            'nl': [102],
            'no': [102],
            'pl': [104],
            'pt': [102],
            'ro': [102],
            'sv': [106],
            'tr': [100],
            'vi': [102],
            'zh': [102],
        }

        for key, values in self.authornamespaces.items():
            for item in values:
                self.crossnamespace[item].update({key: self.authornamespaces})

    def shared_data_repository(self, code, transcluded=False):
        return ('wikidata', 'wikidata')
