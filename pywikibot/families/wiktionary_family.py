"""Family module for Wiktionary."""
#
# (C) Pywikibot team, 2005-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

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

    codes = {
        'af', 'am', 'an', 'ang', 'ar', 'ast', 'ay', 'az', 'bcl', 'be', 'bg',
        'bjn', 'blk', 'bn', 'br', 'bs', 'btm', 'ca', 'chr', 'ckb', 'co', 'cs',
        'csb', 'cy', 'da', 'de', 'diq', 'dv', 'el', 'en', 'eo', 'es', 'et',
        'eu', 'fa', 'fi', 'fj', 'fo', 'fr', 'fy', 'ga', 'gd', 'gl', 'gn',
        'gom', 'gor', 'gu', 'guw', 'gv', 'ha', 'he', 'hi', 'hif', 'hr', 'hsb',
        'hu', 'hy', 'ia', 'id', 'ie', 'ig', 'io', 'is', 'it', 'iu', 'ja',
        'jbo', 'jv', 'ka', 'kaa', 'kbd', 'kcg', 'kk', 'kl', 'km', 'kn', 'ko',
        'ks', 'ku', 'kw', 'ky', 'la', 'lb', 'li', 'lmo', 'ln', 'lo', 'lt',
        'lv', 'mad', 'mg', 'mi', 'min', 'mk', 'ml', 'mn', 'mni', 'mnw', 'mr',
        'ms', 'mt', 'my', 'na', 'nah', 'nds', 'ne', 'nia', 'nl', 'nn', 'no',
        'oc', 'om', 'or', 'pa', 'pl', 'pnb', 'ps', 'pt', 'qu', 'ro', 'roa-rup',
        'ru', 'rw', 'sa', 'sat', 'scn', 'sd', 'sg', 'sh', 'shn', 'shy', 'si',
        'simple', 'sk', 'skr', 'sl', 'sm', 'so', 'sq', 'sr', 'ss', 'st', 'su',
        'sv', 'sw', 'ta', 'tcy', 'te', 'tg', 'th', 'ti', 'tk', 'tl', 'tn',
        'tpi', 'tr', 'ts', 'tt', 'ug', 'uk', 'ur', 'uz', 'vec', 'vi', 'vo',
        'wa', 'wo', 'yi', 'yue', 'zh', 'zh-min-nan', 'zu',
    }

    category_redirect_templates = {
        '_default': (),
        'ar': ('تحويل تصنيف',),
        'zh': ('分类重定向',),
    }

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = [
        'af', 'am', 'an', 'ang', 'ar', 'ast', 'ay', 'az', 'bcl', 'be', 'bg',
        'bjn', 'bn', 'br', 'bs', 'ca', 'chr', 'co', 'cs', 'csb', 'cy', 'da',
        'diq', 'dv', 'el', 'eo', 'es', 'et', 'eu', 'fa', 'fi', 'fj', 'fo',
        'ga', 'gd', 'gl', 'gn', 'gom', 'gor', 'gu', 'guv', 'gv', 'ha', 'hiv',
        'hr', 'hsb', 'hu', 'hy', 'ia', 'id', 'ie', 'ig', 'io', 'iu', 'jbo',
        'jv', 'ka', 'kk', 'kl', 'km', 'kn', 'ko', 'ks', 'ku', 'kw', 'ky', 'la',
        'lb', 'lmo', 'ln', 'lo', 'lt', 'lv', 'mg', 'mi', 'min', 'mk', 'mn',
        'mni', 'mnw', 'mr', 'ms', 'mt', 'my', 'na', 'nah', 'nds', 'ne', 'nia',
        'nl', 'nn', 'no', 'oc', 'om', 'or', 'pa', 'pnb', 'ps', 'pt', 'qu',
        'roa-rup', 'rw', 'sa', 'sat', 'scn', 'sd', 'sg', 'sh', 'shn', 'shy',
        'si', 'simple', 'sk', 'skr', 'sl', 'sm', 'so', 'sq', 'sr', 'ss', 'st',
        'su', 'sv', 'sw', 'ta', 'te', 'tg', 'th', 'ti', 'tk', 'tl', 'tn',
        'tpi', 'tr', 'ts', 'tt', 'ug', 'uk', 'ur', 'uz', 'vec', 'vi', 'vo',
        'wa', 'wo', 'yi', 'zh', 'zh-min-nan', 'zu',
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
