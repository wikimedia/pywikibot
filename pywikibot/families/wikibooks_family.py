# -*- coding: utf-8 -*-
"""Family module for Wikibooks."""
#
# (C) Pywikibot team, 2005-2020
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The Wikimedia family that is known as Wikibooks
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikibooks."""

    name = 'wikibooks'

    closed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=dblists/closed.dblist  # noqa
        'aa', 'ak', 'als', 'ang', 'as', 'ast', 'ay', 'bi', 'bm', 'bo', 'ch',
        'co', 'ga', 'gn', 'got', 'gu', 'ie', 'kn', 'ks', 'lb', 'ln', 'lv',
        'mi', 'mn', 'my', 'na', 'nah', 'nds', 'ps', 'qu', 'rm', 'se', 'simple',
        'su', 'sw', 'tk', 'ug', 'uz', 'vo', 'wa', 'xh', 'yo', 'za',
        'zh-min-nan', 'zu',
    ]

    removed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=dblists/deleted.dblist  # noqa
        'dk', 'tokipona',
    ]

    languages_by_size = [
        'en', 'hu', 'de', 'fr', 'it', 'pt', 'ja', 'es', 'nl', 'pl', 'id', 'he',
        'fi', 'zh', 'sq', 'az', 'fa', 'ru', 'vi', 'ca', 'eu', 'da', 'ko', 'ba',
        'th', 'sv', 'gl', 'sr', 'cs', 'hi', 'hr', 'no', 'tr', 'sa', 'ar', 'ta',
        'uk', 'eo', 'sk', 'is', 'ro', 'bn', 'si', 'mk', 'ka', 'bg', 'ms', 'tt',
        'lt', 'el', 'li', 'sl', 'ur', 'km', 'tl', 'la', 'et', 'be', 'kk', 'ia',
        'ml', 'oc', 'ne', 'hy', 'cv', 'pa', 'tg', 'te', 'ku', 'fy', 'bs', 'cy',
        'af', 'mg', 'mr', 'ky',
    ]

    category_redirect_templates = {
        '_default': (),
        'ar': ('تحويل تصنيف',),
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
        'ar': ('/شرح', '/doc'),
        'es': ('/uso', '/doc'),
        'sr': ('/док', ),
    }
