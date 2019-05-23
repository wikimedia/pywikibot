# -*- coding: utf-8 -*-
"""Family module for Wikibooks."""
#
# (C) Pywikibot team, 2005-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family


# The Wikimedia family that is known as Wikibooks
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikibooks."""

    name = 'wikibooks'

    closed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=closed.dblist
        'aa', 'ak', 'als', 'ang', 'as', 'ast', 'ay',
        'bi', 'bm', 'bo', 'ch', 'co', 'ga', 'gn', 'got',
        'gu', 'ie', 'kn', 'ks', 'lb', 'ln', 'lv', 'mi',
        'mn', 'my', 'na', 'nah', 'nds', 'ps', 'qu', 'rm',
        'se', 'simple', 'su', 'sw', 'tk', 'ug', 'uz',
        'vo', 'wa', 'xh', 'yo', 'za', 'zh-min-nan', 'zu',
    ]

    removed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=closed.dblist
        'dk', 'tokipona',
    ]

    languages_by_size = [
        'en', 'hu', 'de', 'fr', 'pt', 'ja', 'it', 'nl', 'es', 'pl', 'th', 'he',
        'id', 'fi', 'sq', 'az', 'fa', 'zh', 'ca', 'ru', 'vi', 'da', 'ko', 'sv',
        'gl', 'sr', 'cs', 'hr', 'ba', 'no', 'ar', 'tr', 'ta', 'sa', 'uk', 'eo',
        'sk', 'is', 'ro', 'hi', 'si', 'bn', 'mk', 'bg', 'ka', 'lt', 'ms', 'tt',
        'el', 'li', 'ur', 'sl', 'km', 'tl', 'et', 'kk', 'ia', 'be', 'ml', 'oc',
        'ne', 'hy', 'eu', 'pa', 'tg', 'la', 'cv', 'fy', 'ku', 'bs', 'cy', 'af',
        'te', 'mr', 'mg', 'ky',
    ]

    category_redirect_templates = {
        '_default': (),
        'en': ('Category redirect',),
        'es': ('Categoría redirigida',),
        'ro': ('Redirect categorie',),
        'vi': ('Đổi hướng thể loại',),
    }

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    cross_allowed = [
        'af', 'ca', 'fa', 'fy', 'gl', 'it', 'nl', 'ru', 'th', 'zh',
    ]

    # Subpages for documentation.
    # TODO: List is incomplete, to be completed for missing languages.
    doc_subpages = {
        '_default': (('/doc', ),
                     ['en']
                     ),
        'es': ('/uso', '/doc'),
    }
