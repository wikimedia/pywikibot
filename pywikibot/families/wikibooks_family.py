# -*- coding: utf-8 -*-
"""Family module for Wikibooks."""
#
# (C) Pywikibot team, 2005-2020
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
        # See https://noc.wikimedia.org/conf/highlight.php?file=dblists/closed.dblist  # noqa
        'aa', 'ak', 'als', 'ang', 'as', 'ast', 'ay',
        'bi', 'bm', 'bo', 'ch', 'co', 'ga', 'gn', 'got',
        'gu', 'ie', 'kn', 'ks', 'lb', 'ln', 'lv', 'mi',
        'mn', 'my', 'na', 'nah', 'nds', 'ps', 'qu', 'rm',
        'se', 'simple', 'su', 'sw', 'tk', 'ug', 'uz',
        'vo', 'wa', 'xh', 'yo', 'za', 'zh-min-nan', 'zu',
    ]

    removed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=dblists/deleted.dblist  # noqa
        'dk', 'tokipona',
    ]

    languages_by_size = [
        'en', 'hu', 'de', 'fr', 'pt', 'ja', 'it', 'es', 'nl', 'pl', 'id', 'he',
        'fi', 'sq', 'zh', 'az', 'fa', 'vi', 'ru', 'ca', 'da', 'ko', 'sv', 'gl',
        'th', 'sr', 'cs', 'ba', 'hr', 'ar', 'no', 'tr', 'hi', 'sa', 'ta', 'uk',
        'eo', 'sk', 'is', 'ro', 'bn', 'si', 'mk', 'ka', 'bg', 'ms', 'tt', 'lt',
        'el', 'li', 'ur', 'sl', 'km', 'tl', 'la', 'et', 'be', 'kk', 'ia', 'ml',
        'oc', 'eu', 'ne', 'hy', 'pa', 'tg', 'cv', 'ku', 'fy', 'bs', 'cy', 'af',
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
    # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = [
        'af', 'ar', 'ba', 'ca', 'eu', 'fa', 'fy', 'gl', 'it', 'ko', 'ky', 'nl',
        'ru', 'sk', 'th', 'zh',
    ]

    # Subpages for documentation.
    # TODO: List is incomplete, to be completed for missing languages.
    doc_subpages = {
        '_default': (('/doc', ),
                     ['en']
                     ),
        'es': ('/uso', '/doc'),
        'sr': ('/док', ),
    }
