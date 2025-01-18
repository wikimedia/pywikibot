"""Family module for Wikibooks."""
#
# (C) Pywikibot team, 2005-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family


# The Wikimedia family that is known as Wikibooks
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikibooks."""

    name = 'wikibooks'

    closed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/closed.dblist
        'aa', 'ak', 'ang', 'as', 'ast', 'ay', 'bi', 'bm', 'bo', 'ch', 'co',
        'ga', 'gn', 'got', 'gu', 'ie', 'kn', 'ks', 'lb', 'ln', 'lv', 'mi',
        'mn', 'my', 'na', 'nah', 'nds', 'ps', 'qu', 'rm', 'se', 'simple', 'su',
        'sw', 'tk', 'ug', 'uz', 'vo', 'wa', 'xh', 'yo', 'za', 'zh-min-nan',
        'zu',
    ]

    removed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/deleted.dblist
        'als', 'dk', 'tokipona',
    ]

    codes = {
        'af', 'ar', 'az', 'ba', 'be', 'bg', 'bn', 'bs', 'ca', 'cs', 'cv', 'cy',
        'da', 'de', 'el', 'en', 'eo', 'es', 'et', 'eu', 'fa', 'fi', 'fr', 'fy',
        'gl', 'he', 'hi', 'hr', 'hu', 'hy', 'ia', 'id', 'is', 'it', 'ja', 'ka',
        'kk', 'km', 'ko', 'ku', 'ky', 'la', 'li', 'lt', 'mg', 'mk', 'ml', 'mr',
        'ms', 'ne', 'nl', 'no', 'oc', 'pa', 'pl', 'pt', 'ro', 'ru', 'sa',
        'shn', 'si', 'sk', 'sl', 'sq', 'sr', 'sv', 'ta', 'te', 'tg', 'th',
        'tl', 'tr', 'tt', 'uk', 'ur', 'vi', 'zh',
    }

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
        'af', 'ar', 'az', 'ba', 'be', 'bg', 'bs', 'ca', 'cv', 'cy', 'da', 'de',
        'el', 'eo', 'et', 'eu', 'fa', 'fi', 'gl', 'hi', 'hy', 'ia', 'id', 'is',
        'it', 'ka', 'kk', 'km', 'ko', 'ku', 'ky', 'la', 'li', 'lt', 'mg', 'mk',
        'ml', 'mr', 'ms', 'ne', 'nl', 'no', 'oc', 'pa', 'pl', 'ro', 'ru', 'sa',
        'shn', 'si', 'sk', 'sl', 'sq', 'sv', 'ta', 'te', 'tg', 'th', 'tl',
        'tr', 'tt', 'uk', 'ur', 'vi', 'zh',
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
