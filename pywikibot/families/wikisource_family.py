# -*- coding: utf-8  -*-
"""Family module for Wikisource."""
from __future__ import unicode_literals

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikisource
class Family(family.WikimediaFamily):

    """Family class for Wikisource."""

    closed_wikis = [
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Old_English_Wikisource
        'ang',
        # https://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Haitian_Creole_Wikisource
        'ht',
    ]

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'wikisource'

        self.languages_by_size = [
            'fr', 'en', 'de', 'ru', 'he', 'zh', 'pl', 'it', 'es', 'ar', 'sv',
            'cs', 'pt', 'fa', 'ca', 'hu', 'ml', 'ko', 'sl', 'ro', 'te', 'sr',
            'fi', 'vi', 'hy', 'sa', 'el', 'hr', 'th', 'bn', 'no', 'is', 'gu',
            'ja', 'nl', 'la', 'az', 'br', 'vec', 'eo', 'uk', 'tr', 'mk', 'yi',
            'ta', 'be', 'id', 'da', 'li', 'et', 'as', 'mr', 'bg', 'bs', 'sah',
            'kn', 'gl', 'lt', 'cy', 'sk', 'zh-min-nan', 'fo', 'or',
        ]

        self.langs = dict([(lang, '%s.wikisource.org' % lang)
                           for lang in self.languages_by_size])
        # FIXME: '-' is invalid at the beginning of a hostname, and
        # '-' is not a valid subdomain.
        self.langs['-'] = 'wikisource.org'

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
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

        # Subpages for documentation.
        # TODO: List is incomplete, to be completed for missing languages.
        # TODO: Remove comments for appropriate pages
        self.doc_subpages = {
            '_default': ((u'/doc', ),
                         ['ar', 'as', 'az', 'bn', 'en', 'es',
                          'et', 'gu', 'hu', 'it', 'ja', 'kn', 'ml',
                          'mk', 'mr', 'pt', 'ro', 'sa', 'sah', 'ta',
                          'te', 'th', 'vi']
                         ),
            'be': (u'/Дакументацыя', ),
            'bn': (u'/নথি', ),
            'br': (u'/diellerezh', ),
            'de': (u'/Doku', u'/Meta'),
            'el': (u'/τεκμηρίωση', ),
            'eo': ('u/dokumentado', ),
            # 'fa': (u'/صفحه الگو', ),
            # 'fa': (u'/فضای‌نام توضیحات', ),
            # 'fa': (u'/آغاز جعبه', ),
            # 'fa': (u'/پایان جعبه۲', ),
            # 'fa': (u'/آغاز جعبه۲', ),
            # 'fa': (u'/پایان جعبه', ),
            # 'fa': (u'/توضیحات', ),
            'fr': (u'/documentation', ),
            'id': (u'/dok', ),
            'ko': (u'/설명문서', ),
            'no': (u'/dok', ),
            'ru': (u'/Документация', ),
            'sl': (u'/dok', ),
            'sv': (u'/dok', ),
            'uk': (u'/документація', ),
        }

    def shared_data_repository(self, code, transcluded=False):
        """Return the shared data repository for this site."""
        return ('wikidata', 'wikidata')
