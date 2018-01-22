# -*- coding: utf-8 -*-
"""Family module for Wiktionary."""
#
# (C) Pywikibot team, 2005-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family


# The Wikimedia family that is known as Wiktionary
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wiktionary."""

    name = 'wiktionary'

    closed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=closed.dblist
        'aa', 'ab', 'ak', 'als', 'as', 'av', 'ba', 'bh', 'bi', 'bm', 'bo',
        'ch', 'cr', 'dz', 'ik', 'mh', 'mo', 'pi', 'rm', 'rn', 'sc', 'sn',
        'to', 'tw', 'xh', 'yo', 'za',
    ]

    removed_wikis = [
        # See https://noc.wikimedia.org/conf/highlight.php?file=deleted.dblist
        'dk', 'ba', 'tlh', 'tokipona',
    ]

    def __init__(self):
        """Initializer."""
        self.languages_by_size = [
            'en', 'mg', 'fr', 'sh', 'ru', 'es', 'zh', 'de', 'nl', 'lt', 'sv',
            'ku', 'pl', 'el', 'it', 'ta', 'hu', 'fi', 'tr', 'ca', 'ko', 'io',
            'kn', 'pt', 'hy', 'vi', 'sr', 'ja', 'chr', 'hi', 'th', 'ro', 'no',
            'ml', 'id', 'et', 'uz', 'li', 'my', 'or', 'te', 'fa', 'cs', 'eo',
            'ar', 'jv', 'az', 'eu', 'gl', 'oc', 'da', 'lo', 'br', 'uk', 'hr',
            'fj', 'tg', 'bg', 'simple', 'ps', 'cy', 'sk', 'vo', 'wa', 'is',
            'zh-min-nan', 'la', 'scn', 'af', 'he', 'ast', 'tl', 'ky', 'sw',
            'fy', 'nn', 'lv', 'co', 'pnb', 'mn', 'pa', 'ka', 'nds', 'sl', 'sq',
            'lb', 'bs', 'nah', 'sa', 'kk', 'bn', 'tk', 'km', 'sm', 'mk', 'hsb',
            'be', 'ms', 'ga', 'ur', 'an', 'wo', 'vec', 'ang', 'tt', 'sd', 'gn',
            'mr', 'so', 'csb', 'ug', 'gd', 'mt', 'st', 'roa-rup', 'si', 'hif',
            'ia', 'ie', 'mi', 'ay', 'kl', 'fo', 'jbo', 'ln', 'zu', 'na', 'gu',
            'gv', 'kw', 'rw', 'ts', 'ne', 'om', 'qu', 'su', 'ss', 'ha', 'iu',
            'am', 'dv', 'tpi', 'yi', 'ti', 'sg', 'tn', 'ks',
        ]

        super(Family, self).__init__()

        self.category_redirect_templates = {
            '_default': (),
            'zh': ('分类重定向',),
        }

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/BPI#Current_implementation
        # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
        self.cross_allowed = [
            'am', 'af', 'am', 'ang', 'an', 'ar', 'ast', 'ay', 'az', 'be',
            'bg', 'bn', 'br', 'bs', 'ca', 'chr', 'co', 'csb', 'cs', 'cy',
            'da', 'dv', 'el', 'eo', 'es', 'et', 'eu', 'fa', 'fi', 'fj', 'fo',
            'fy', 'ga', 'gd', 'gl', 'gn', 'gu', 'gv', 'ha', 'hsb', 'hu', 'hy',
            'ia', 'id', 'ie', 'io', 'iu', 'jbo', 'jv', 'ka', 'kk', 'kl', 'km',
            'kn', 'ko', 'ks', 'ku', 'kw', 'ky', 'la', 'lb', 'ln', 'lo', 'lt',
            'lv', 'mg', 'mi', 'mk', 'ml', 'mn', 'ms', 'mt', 'my', 'nah', 'na',
            'nds', 'ne', 'nl', 'nn', 'no', 'oc', 'om', 'or', 'pa', 'pnb',
            'ps', 'pt', 'qu', 'roa_rup', 'rw', 'sa', 'scn', 'sd', 'sg', 'sh',
            'simple', 'si', 'sk', 'sl', 'sm', 'so', 'sq', 'sr', 'ss', 'st',
            'su', 'sv', 'sw', 'ta', 'te', 'tg', 'th', 'ti', 'tk', 'tl', 'tn',
            'tpi', 'tr', 'ts', 'tt', 'ug', 'uk', 'ur', 'uz', 'vec', 'vi', 'vo',
            'wa', 'wo', 'yi', 'zh_min_nan', 'zh', 'zu',
        ]

        # Other than most Wikipedias, page names must not start with a capital
        # letter on ALL Wiktionaries.
        self.nocapitalize = list(self.langs.keys())

        # Which languages have a special order for putting interlanguage links,
        # and what order is it? If a language is not in interwiki_putfirst,
        # alphabetical order on language code is used. For languages that are in
        # interwiki_putfirst, interwiki_putfirst is checked first, and
        # languages are put in the order given there. All other languages are
        # put after those, in code-alphabetical order.

        self.alphabetic_sv = [
            'aa', 'af', 'ak', 'als', 'an', 'roa-rup', 'ast', 'gn', 'ay', 'az',
            'id', 'ms', 'bm', 'zh-min-nan', 'jv', 'su', 'mt', 'bi', 'bo', 'bs',
            'br', 'ca', 'cs', 'ch', 'sn', 'co', 'za', 'cy', 'da', 'de', 'na',
            'mh', 'et', 'ang', 'en', 'es', 'eo', 'eu', 'to', 'fr', 'fy', 'fo',
            'ga', 'gv', 'sm', 'gd', 'gl', 'hr', 'io', 'ia', 'ie', 'ik', 'xh',
            'is', 'zu', 'it', 'kl', 'csb', 'kw', 'rw', 'rn', 'sw', 'ky', 'ku',
            'la', 'lv', 'lb', 'lt', 'li', 'ln', 'jbo', 'hu', 'mg', 'mi', 'mo',
            'my', 'fj', 'nah', 'nl', 'cr', 'no', 'nn', 'hsb', 'oc', 'om', 'ug',
            'uz', 'nds', 'pl', 'pt', 'ro', 'rm', 'qu', 'sg', 'sc', 'st', 'tn',
            'sq', 'scn', 'simple', 'ss', 'sk', 'sl', 'so', 'sh', 'fi', 'sv',
            'tl', 'tt', 'vi', 'tpi', 'tr', 'tw', 'vo', 'wa', 'wo', 'ts', 'yo',
            'el', 'av', 'ab', 'ba', 'be', 'bg', 'mk', 'mn', 'ru', 'sr', 'tg',
            'uk', 'kk', 'hy', 'yi', 'he', 'ur', 'ar', 'tk', 'sd', 'fa', 'ha',
            'ps', 'dv', 'ks', 'ne', 'pi', 'bh', 'mr', 'sa', 'hi', 'as', 'bn',
            'pa', 'pnb', 'gu', 'or', 'ta', 'te', 'kn', 'ml', 'si', 'th', 'lo',
            'dz', 'ka', 'ti', 'am', 'chr', 'iu', 'km', 'zh', 'ja', 'ko',
        ]

        self.interwiki_putfirst = {
            'da': self.alphabetic,
            'en': self.alphabetic,
            'et': self.alphabetic,
            'fi': self.alphabetic,
            'fy': self.fyinterwiki,
            'he': ['en'],
            'hu': ['en'],
            'ms': self.alphabetic_revised,
            'pl': self.alphabetic_revised,
            'sv': self.alphabetic_sv,
            'simple': self.alphabetic,
        }

        self.interwiki_on_one_line = ['pl']

        self.interwiki_attop = ['pl']

        # Subpages for documentation.
        # TODO: List is incomplete, to be completed for missing languages.
        self.doc_subpages = {
            '_default': ((u'/doc', ),
                         ['en']
                         ),
        }
