# -*- coding: utf-8 -*-
"""Family module for Wikibooks."""
#
# (C) Pywikibot team, 2005-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikibooks
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikibooks."""

    name = 'wikibooks'

    closed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=closed.dblist
        'aa', 'ak', 'als', 'ang', 'as', 'ast', 'ay', 'ba',
        'bi', 'bm', 'bo', 'ch', 'co', 'ga', 'got', 'gn',
        'gu', 'kn', 'ie', 'ks', 'lb', 'ln', 'lv', 'mi',
        'mn', 'my', 'na', 'nah', 'nds', 'ps', 'qu', 'rm',
        'se', 'simple', 'su', 'sw', 'tk', 'ug', 'uz',
        'vo', 'wa', 'xh', 'yo', 'za', 'zh-min-nan', 'zu',
    ]

    removed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=closed.dblist
        'dk', 'tokipona',
    ]

    def __init__(self):
        """Constructor."""
        self.languages_by_size = [
            'en', 'hu', 'de', 'fr', 'ja', 'it', 'es', 'pt', 'nl', 'pl', 'he',
            'vi', 'ca', 'th', 'fi', 'id', 'sq', 'fa', 'ru', 'zh', 'cs', 'az',
            'sv', 'da', 'hr', 'sr', 'tr', 'ko', 'ar', 'no', 'gl', 'ro', 'ta',
            'tl', 'mk', 'is', 'sa', 'uk', 'ka', 'lt', 'tt', 'eo', 'sk', 'el',
            'hi', 'bg', 'bn', 'hy', 'si', 'li', 'ms', 'sl', 'ur', 'la', 'ml',
            'km', 'ia', 'et', 'cv', 'mr', 'eu', 'oc', 'kk', 'be', 'pa', 'ne',
            'fy', 'tg', 'te', 'af', 'ku', 'ky', 'bs', 'mg', 'cy',
        ]

        super(Family, self).__init__()

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/BPI#Current_implementation
        self.cross_allowed = [
            'af', 'ca', 'fa', 'fy', 'gl', 'it', 'nl', 'ru', 'th', 'zh',
        ]

        # Subpages for documentation.
        # TODO: List is incomplete, to be completed for missing languages.
        self.doc_subpages = {
            '_default': ((u'/doc', ),
                         ['en']
                         ),
            'es': ('/uso', '/doc'),
        }
