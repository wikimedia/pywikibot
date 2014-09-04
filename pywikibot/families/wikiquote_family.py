# -*- coding: utf-8  -*-
"""Family module for Wikiquote."""

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikiquote
class Family(family.WikimediaFamily):

    """Family class for Wikiquote."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'wikiquote'

        self.languages_by_size = [
            'pl', 'en', 'it', 'ru', 'de', 'pt', 'es', 'fr', 'cs', 'sk', 'bg',
            'bs', 'tr', 'uk', 'he', 'sl', 'fa', 'lt', 'eo', 'el', 'ca', 'zh',
            'id', 'hu', 'fi', 'sv', 'li', 'nl', 'hr', 'nn', 'ja', 'no', 'az',
            'sa', 'hy', 'ar', 'et', 'ko', 'gl', 'ml', 'cy', 'ka', 'sr', 'ro',
            'ku', 'te', 'th', 'da', 'eu', 'ta', 'is', 'vi', 'af', 'sq', 'hi',
            'kn', 'la', 'be', 'br', 'mr', 'ur', 'uz', 'zh-min-nan', 'gu', 'su',
            'wo', 'ky', 'am',
        ]

        self.langs = dict([(lang, '%s.wikiquote.org' % lang)
                           for lang in self.languages_by_size])

        # Global bot allowed languages on https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = [
            'af', 'am', 'ar', 'az', 'be', 'bg', 'br', 'bs', 'ca', 'cs', 'da',
            'el', 'eo', 'es', 'et', 'eu', 'fa', 'fi', 'fr', 'gl', 'he', 'hi',
            'hu', 'hy', 'id', 'is', 'it', 'ja', 'ka', 'kn', 'ku', 'ky', 'la',
            'li', 'lt', 'ml', 'mr', 'nl', 'nn', 'no', 'pt', 'ro', 'ru', 'sk',
            'sl', 'sq', 'sr', 'su', 'sv', 'ta', 'te', 'tr', 'uk', 'uz', 'vi',
            'wo', 'zh',
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
            'simple': self.alphabetic,
            'pt': self.alphabetic,
        }

        self.obsolete = {
            'als': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Alemannic_Wikiquote
            'ang': None,  # https://bugzilla.wikimedia.org/show_bug.cgi?id=29150
            'ast': None,  # https://bugzilla.wikimedia.org/show_bug.cgi?id=28964
            'bm': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bambara_Wikiquote
            'co': None,
            'cr': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nehiyaw_Wikiquote
            'dk': 'da',
            'ga': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Gaeilge_Wikiquote
            'jp': 'ja',
            'kk': None,   # https://bugzilla.wikimedia.org/show_bug.cgi?id=20325
            'kr': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kanuri_Wikiquote
            'ks': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kashmiri_Wikiquote
            'kw': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kernewek_Wikiquote
            'lb': None,
            'minnan': 'zh-min-nan',
            'na': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nauruan_Wikiquote
            'nb': 'no',
            'nds': None,  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Low_Saxon_Wikiquote
            'qu': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Quechua_Wikiquote
            'simple': 'en',  # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Simple_English_(3)_Wikiquote
            'tk': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Turkmen_Wikiquote
            'tokipona': None,
            'tt': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tatar_Wikiquote
            'ug': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Oyghurque_Wikiquote
            'vo': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Volapuk_Wikiquote
            'za': None,   # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Zhuang_Wikiquote
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

    def code2encodings(self, code):
        """
        Return a list of historical encodings for a specific language.

        @param code: site code
        """
        # Historic compatibility
        if code == 'pl':
            return 'utf-8', 'iso8859-2'
        if code == 'ru':
            return 'utf-8', 'iso8859-5'
        return self.code2encoding(code),

    def shared_data_repository(self, code, transcluded=False):
        """Return the shared data repository for this family."""
        return ('wikidata', 'wikidata')
