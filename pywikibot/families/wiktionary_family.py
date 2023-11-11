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
        'en', 'fr', 'mg', 'zh', 'el', 'ru', 'de', 'ku', 'es', 'sh', 'sv', 'nl',
        'pl', 'lt', 'ca', 'it', 'hu', 'fi', 'pt', 'ta', 'tr', 'ja', 'io', 'hy',
        'ko', 'kn', 'vi', 'sr', 'th', 'hi', 'ro', 'id', 'no', 'et', 'skr',
        'cs', 'ml', 'my', 'uz', 'li', 'eo', 'or', 'te', 'fa', 'gl', 'sg', 'oc',
        'ar', 'jv', 'is', 'az', 'uk', 'ast', 'eu', 'br', 'bn', 'mnw', 'da',
        'simple', 'lo', 'la', 'shn', 'hr', 'sk', 'fj', 'wa', 'ky', 'lmo', 'bg',
        'ur', 'cy', 'ps', 'tg', 'kbd', 'he', 'vo', 'om', 'sl', 'af',
        'zh-min-nan', 'ms', 'scn', 'tl', 'pa', 'fy', 'sw', 'kk', 'ka', 'nn',
        'min', 'lv', 'nds', 'gor', 'sq', 'lb', 'bs', 'co', 'mn', 'pnb', 'nah',
        'yue', 'ckb', 'sa', 'diq', 'km', 'be', 'vec', 'nia', 'tk', 'mk', 'sm',
        'hsb', 'ks', 'shy', 'bcl', 'su', 'ga', 'btm', 'gd', 'an', 'gom', 'mr',
        'ha', 'wo', 'mni', 'ia', 'bjn', 'ang', 'mt', 'tt', 'sd', 'blk', 'fo',
        'so', 'si', 'gn', 'ie', 'mi', 'csb', 'ug', 'guw', 'st', 'hif', 'jbo',
        'roa-rup', 'kl', 'zu', 'ay', 'ln', 'yi', 'gu', 'kcg', 'na', 'gv', 'kw',
        'tpi', 'am', 'ne', 'rw', 'ts', 'ig', 'qu', 'ss', 'iu', 'chr', 'dv',
        'ti', 'tn',
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

    @classmethod
    def __post_init__(cls):
        """Add 'zh-yue' code alias due to :phab:`T341960`.

        .. versionadded:: 8.3
        """
        aliases = cls.code_aliases.copy()
        aliases['zh-yue'] = 'yue'
        cls.code_aliases = aliases
