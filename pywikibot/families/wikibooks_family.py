# -*- coding: utf-8 -*-
"""Family module for Wikibooks."""
#
# (C) Pywikibot team, 2005-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

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
        'id', 'sq', 'fi', 'fa', 'zh', 'ca', 'ru', 'az', 'vi', 'da', 'ko', 'sv',
        'gl', 'sr', 'cs', 'hr', 'ba', 'no', 'tr', 'ar', 'ta', 'sa', 'sk', 'uk',
        'is', 'hi', 'ro', 'eo', 'si', 'mk', 'bn', 'bg', 'ka', 'ms', 'lt', 'tt',
        'li', 'el', 'ur', 'sl', 'km', 'tl', 'kk', 'et', 'ml', 'oc', 'be', 'ia',
        'eu', 'ne', 'pa', 'hy', 'la', 'cv', 'tg', 'fy', 'ku', 'bs', 'cy', 'te',
        'af', 'mr', 'mg', 'ky',
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
