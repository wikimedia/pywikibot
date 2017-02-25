# -*- coding: utf-8 -*-
"""Family module for Wikibooks."""
#
# (C) Pywikibot team, 2005-2016
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
            'en', 'hu', 'de', 'fr', 'ja', 'it', 'es', 'pt', 'nl', 'vi', 'pl',
            'he', 'ca', 'id', 'fi', 'sq', 'fa', 'ru', 'th', 'cs', 'zh', 'az',
            'sv', 'hr', 'tr', 'sr', 'ar', 'ko', 'no', 'da', 'gl', 'ta', 'ro',
            'tl', 'mk', 'is', 'uk', 'ka', 'lt', 'tt', 'sa', 'eo', 'sk', 'bg',
            'el', 'bn', 'hi', 'hy', 'si', 'ms', 'sl', 'ur', 'li', 'la', 'ml',
            'km', 'ang', 'ia', 'cv', 'et', 'mr', 'eu', 'oc', 'kk', 'ne', 'pa',
            'fy', 'ie', 'te', 'af', 'tg', 'ku', 'ky', 'bs', 'be', 'mg', 'cy',
            'zh-min-nan', 'uz',
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
