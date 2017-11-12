# -*- coding: utf-8 -*-
"""Family module for Wikiquote."""
#
# (C) Pywikibot team, 2005-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikiquote
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikiquote."""

    name = 'wikiquote'

    closed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=closed.dblist
        'als', 'am', 'ang', 'ast', 'bm', 'co', 'cr', 'ga', 'kk',
        'kr', 'ks', 'kw', 'lb', 'na', 'nds', 'qu', 'simple',
        'tk', 'tt', 'ug', 'vo', 'za', 'zh_min_nan',
    ]

    removed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=deleted.dblist
        'tokipona',
    ]

    def __init__(self):
        """Constructor."""
        self.languages_by_size = [
            'en', 'it', 'pl', 'ru', 'cs', 'fa', 'de', 'pt', 'es', 'uk', 'sk',
            'fr', 'bs', 'tr', 'he', 'ca', 'fi', 'lt', 'th', 'bg', 'sl', 'eo',
            'hy', 'el', 'nn', 'hr', 'id', 'zh', 'hu', 'su', 'li', 'az', 'ko',
            'nl', 'ja', 'ar', 'gu', 'sv', 'sr', 'gl', 'ur', 'te', 'ta', 'cy',
            'la', 'no', 'ml', 'et', 'vi', 'kn', 'ku', 'be', 'ro', 'eu', 'hi',
            'ka', 'da', 'sa', 'is', 'sq', 'mr', 'br', 'af', 'uz', 'zh-min-nan',
            'wo', 'ky',
        ]

        super(Family, self).__init__()

        self.category_redirect_templates = {
            '_default': (),
            'ar': ('قالب:تحويل تصنيف',),
            'en': ('Category redirect',),
            'ro': ('Redirect categorie',),
            'sq': ('Kategori e zhvendosur',),
            'uk': ('Categoryredirect',),
        }

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/BPI#Current_implementation
        # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
        self.cross_allowed = [
            'af', 'ar', 'az', 'be', 'bg', 'br', 'bs', 'ca', 'cs',
            'cy', 'da', 'el', 'eo', 'es', 'et', 'eu', 'fa', 'fi',
            'fr', 'gl', 'gu', 'he', 'hi', 'hu', 'hy', 'id', 'is',
            'it', 'ja', 'ka', 'kn', 'ko', 'ku', 'ky', 'la', 'li',
            'lt', 'ml', 'mr', 'nl', 'nn', 'no', 'pt', 'ro', 'ru',
            'sk', 'sl', 'sq', 'sr', 'su', 'sv', 'ta', 'te', 'tr',
            'uk', 'ur', 'uz', 'vi', 'wo', 'zh',
        ]

        # Subpages for documentation.
        # TODO: List is incomplete, to be completed for missing languages.
        self.doc_subpages = {
            '_default': ((u'/doc', ),
                         ['en']
                         ),
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
