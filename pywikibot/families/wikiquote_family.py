# -*- coding: utf-8  -*-
"""Family module for Wikiquote."""
from __future__ import unicode_literals

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikiquote
class Family(family.WikimediaFamily):

    """Family class for Wikiquote."""

    closed_wikis = [
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Alemannic_Wikiquote
        'als',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Old_English_Wikiquote
        'ang',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Asturianu_Wikiquote
        'ast',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Bambara_Wikiquote
        'bm',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Corsu_Wikiquote
        'co',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nehiyaw_Wikiquote
        'cr',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Gaeilge_Wikiquote
        'ga',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kazakh_Wikiquote
        'kk',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kanuri_Wikiquote
        'kr',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kashmiri_Wikiquote
        'ks',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Kernewek_Wikiquote
        'kw',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Luxembourgish_Wikiquote
        'lb',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Nauruan_Wikiquote
        'na',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Low_Saxon_Wikiquote
        'nds',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Quechua_Wikiquote
        'qu',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Simple_English_Wikiquote_(3)
        'simple',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Turkmen_Wikiquote
        'tk',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Tatar_Wikiquote
        'tt',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Oyghurque_Wikiquote
        'ug',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Volapuk_Wikiquote
        'vo',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Zhuang_Wikiquote
        'za',
    ]

    removed_wikis = [
        'tokipona',
    ]

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'wikiquote'

        self.languages_by_size = [
            'en', 'pl', 'it', 'ru', 'de', 'pt', 'cs', 'es', 'fr', 'sk', 'bs',
            'tr', 'fa', 'uk', 'lt', 'he', 'bg', 'eo', 'sl', 'ca', 'el', 'nn',
            'id', 'zh', 'hu', 'li', 'hr', 'hy', 'nl', 'ko', 'ja', 'su', 'sv',
            'ur', 'te', 'fi', 'cy', 'la', 'ar', 'no', 'ml', 'et', 'gl', 'az',
            'th', 'ku', 'sr', 'kn', 'ta', 'eu', 'ka', 'sa', 'ro', 'is', 'da',
            'vi', 'hi', 'sq', 'be', 'mr', 'br', 'uz', 'af', 'gu', 'zh-min-nan',
            'am', 'wo', 'ky',
        ]

        self.langs = dict([(lang, '%s.wikiquote.org' % lang)
                           for lang in self.languages_by_size])

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
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
