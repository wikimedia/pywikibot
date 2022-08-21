"""Family module for Wikibooks."""
#
# (C) Pywikibot team, 2005-2022
#
# Distributed under the terms of the MIT license.
#
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

    languages_by_size = [
        'en', 'hu', 'de', 'vi', 'fr', 'it', 'ja', 'pt', 'es', 'nl', 'pl', 'id',
        'he', 'fi', 'zh', 'sq', 'az', 'fa', 'ru', 'ca', 'eu', 'th', 'da', 'ko',
        'ba', 'sv', 'gl', 'cs', 'hi', 'sr', 'uk', 'hr', 'no', 'tr', 'sa', 'ar',
        'ta', 'eo', 'sk', 'is', 'bn', 'ro', 'si', 'bg', 'ms', 'ka', 'mk', 'tt',
        'lt', 'el', 'li', 'sl', 'tl', 'ur', 'km', 'la', 'mr', 'kk', 'te', 'et',
        'be', 'ia', 'ml', 'oc', 'hy', 'ne', 'pa', 'cv', 'tg', 'ku', 'fy', 'af',
        'bs', 'cy', 'mg', 'ky',
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
