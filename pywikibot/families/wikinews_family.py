# -*- coding: utf-8  -*-
"""Family module for Wikinews."""
from __future__ import unicode_literals

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikinews
class Family(family.WikimediaFamily):

    """Family class for Wikinews."""

    closed_wikis = [
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Hungarian_Wikinews
        'hu',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Dutch_Wikinews
        'nl',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Sindhi_Wikinews
        'sd',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Thai_Wikinews
        'th',
    ]

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'wikinews'

        self.languages_by_size = [
            'sr', 'en', 'fr', 'de', 'pl', 'es', 'pt', 'ru', 'it', 'zh', 'ta',
            'el', 'ca', 'cs', 'sv', 'ar', 'fa', 'ro', 'uk', 'tr', 'ja', 'sq',
            'no', 'ko', 'eo', 'fi', 'bs', 'he', 'bg',
        ]

        self.langs = dict([(lang, '%s.wikinews.org' % lang)
                           for lang in self.languages_by_size])

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = ['ca', 'cs', 'en', 'fa', 'ko', ]

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
        }

    def shared_data_repository(self, code, transcluded=False):
        """Return the shared data repository for this site."""
        return ('wikidata', 'wikidata')
