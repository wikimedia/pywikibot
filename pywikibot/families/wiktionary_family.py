"""Family module for Wiktionary."""
#
# (C) Pywikibot team, 2005-2023
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The Wikimedia family that is known as Wiktionary
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wiktionary.

    .. versionchanged:: 8.0
       ``alphabetic_sv`` attribute was removed; ``interwiki_putfirst``
       attribute was removed and default setting from parent class is
       used.
    """

    name = 'wiktionary'

    closed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/closed.dblist
        'aa', 'ab', 'ak', 'as', 'av', 'bh', 'bi', 'bm', 'bo', 'ch', 'cr', 'dz',
        'ik', 'mh', 'pi', 'rm', 'rn', 'sc', 'sn', 'to', 'tw', 'xh', 'yo', 'za',
    ]

    removed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/deleted.dblist
        'als', 'ba', 'dk', 'mo', 'tlh', 'tokipona',
    ]

    languages_by_size = [
        'en', 'fr', 'mg', 'zh', 'ru', 'de', 'es', 'sh', 'sv', 'nl', 'el', 'pl',
        'ku', 'lt', 'ca', 'it', 'fi', 'ta', 'hu', 'tr', 'ja', 'io', 'hy', 'ko',
        'pt', 'kn', 'vi', 'sr', 'th', 'hi', 'ro', 'no', 'id', 'et', 'cs', 'ml',
        'my', 'skr', 'uz', 'li', 'or', 'eo', 'te', 'fa', 'gl', 'ar', 'oc',
        'jv', 'az', 'eu', 'uk', 'ast', 'br', 'is', 'sg', 'bn', 'da', 'lo',
        'simple', 'mnw', 'la', 'hr', 'shn', 'fj', 'sk', 'ky', 'bg', 'wa', 'tg',
        'ur', 'ps', 'cy', 'lmo', 'vo', 'he', 'om', 'sl', 'af', 'zh-min-nan',
        'scn', 'tl', 'pa', 'ms', 'fy', 'sw', 'nn', 'ka', 'lv', 'min', 'sq',
        'nds', 'lb', 'co', 'mn', 'pnb', 'bs', 'nah', 'yue', 'sa', 'kk', 'km',
        'vec', 'be', 'diq', 'tk', 'mk', 'nia', 'sm', 'hsb', 'ks', 'shy', 'su',
        'gd', 'ga', 'bcl', 'an', 'gom', 'mr', 'gor', 'wo', 'mni', 'ia', 'ang',
        'bjn', 'mt', 'fo', 'sd', 'tt', 'gn', 'so', 'ie', 'mi', 'csb', 'ug',
        'si', 'ha', 'st', 'hif', 'roa-rup', 'guw', 'jbo', 'kl', 'zu', 'ay',
        'tpi', 'yi', 'ln', 'gu', 'na', 'gv', 'kw', 'am', 'ne', 'rw', 'ts',
        'ig', 'qu', 'ss', 'iu', 'chr', 'dv', 'ti', 'tn',
    ]

    category_redirect_templates = {
        '_default': (),
        'ar': ('تحويل تصنيف',),
        'zh': ('分类重定向',),
    }

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = [
        'af', 'am', 'an', 'ang', 'ar', 'ast', 'ay', 'az', 'be', 'bg', 'bn',
        'br', 'bs', 'ca', 'chr', 'co', 'cs', 'csb', 'cy', 'da', 'dv', 'el',
        'eo', 'es', 'et', 'eu', 'fa', 'fi', 'fj', 'fo', 'fy', 'ga', 'gd', 'gl',
        'gn', 'gu', 'gv', 'ha', 'hsb', 'hu', 'hy', 'ia', 'id', 'ie', 'io',
        'iu', 'jbo', 'jv', 'ka', 'kk', 'kl', 'km', 'kn', 'ko', 'ks', 'ku',
        'kw', 'ky', 'la', 'lb', 'ln', 'lo', 'lt', 'lv', 'mg', 'mi', 'mk', 'ml',
        'mn', 'ms', 'mt', 'my', 'na', 'nah', 'nds', 'ne', 'nl', 'nn', 'no',
        'oc', 'om', 'or', 'pa', 'pnb', 'ps', 'pt', 'qu', 'roa-rup', 'rw', 'sa',
        'scn', 'sd', 'sg', 'sh', 'si', 'simple', 'sk', 'sl', 'sm', 'so', 'sq',
        'sr', 'ss', 'st', 'su', 'sv', 'sw', 'ta', 'te', 'tg', 'th', 'ti', 'tk',
        'tl', 'tn', 'tpi', 'tr', 'ts', 'tt', 'ug', 'uk', 'ur', 'uz', 'vec',
        'vi', 'vo', 'wa', 'wo', 'yi', 'zh', 'zh-min-nan', 'zu',
    ]

    interwiki_on_one_line = ['pl']

    interwiki_attop = ['pl']

    # Subpages for documentation.
    # TODO: List is incomplete, to be completed for missing languages.
    doc_subpages = {
        '_default': (('/doc', ),
                     ['en']
                     ),
        'ar': ('/شرح', '/doc'),
        'sr': ('/док', ),
    }
