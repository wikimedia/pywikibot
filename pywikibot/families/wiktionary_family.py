"""Family module for Wiktionary."""
#
# (C) Pywikibot team, 2005-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family
from pywikibot.tools import classproperty


# The Wikimedia family that is known as Wiktionary
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wiktionary."""

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
        'ku', 'lt', 'ca', 'it', 'fi', 'ta', 'hu', 'tr', 'io', 'ja', 'hy', 'ko',
        'pt', 'kn', 'vi', 'sr', 'th', 'hi', 'ro', 'no', 'id', 'et', 'cs', 'ml',
        'my', 'uz', 'li', 'or', 'eo', 'te', 'fa', 'skr', 'gl', 'ar', 'oc',
        'jv', 'az', 'eu', 'uk', 'br', 'ast', 'is', 'da', 'lo', 'simple', 'bn',
        'sg', 'la', 'hr', 'fj', 'tg', 'sk', 'ky', 'mnw', 'bg', 'wa', 'shn',
        'ur', 'ps', 'cy', 'vo', 'he', 'om', 'sl', 'af', 'zh-min-nan', 'scn',
        'lmo', 'tl', 'pa', 'sw', 'fy', 'ms', 'nn', 'ka', 'lv', 'min', 'sq',
        'nds', 'lb', 'co', 'mn', 'pnb', 'bs', 'nah', 'yue', 'sa', 'kk', 'km',
        'diq', 'vec', 'be', 'tk', 'mk', 'nia', 'sm', 'hsb', 'ks', 'shy', 'su',
        'gd', 'ga', 'bcl', 'an', 'gom', 'mr', 'wo', 'mni', 'ia', 'ang', 'mt',
        'sd', 'fo', 'tt', 'gn', 'so', 'ie', 'mi', 'csb', 'ug', 'si', 'st',
        'roa-rup', 'tpi', 'hif', 'kl', 'bjn', 'ha', 'zu', 'guw', 'ay', 'jbo',
        'yi', 'ln', 'gu', 'na', 'gv', 'kw', 'am', 'ne', 'rw', 'ts', 'qu', 'ss',
        'iu', 'chr', 'dv', 'ti', 'tn', 'ig',
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

    # Which languages have a special order for putting interlanguage links,
    # and what order is it? If a language is not in interwiki_putfirst,
    # alphabetical order on language code is used. For languages that are in
    # interwiki_putfirst, interwiki_putfirst is checked first, and
    # languages are put in the order given there. All other languages are
    # put after those, in code-alphabetical order.

    alphabetic_sv = [
        'aa', 'af', 'ak', 'als', 'an', 'roa-rup', 'ast', 'gn', 'ay', 'az',
        'id', 'ms', 'bm', 'zh-min-nan', 'jv', 'su', 'mt', 'bi', 'bo', 'bs',
        'br', 'ca', 'cs', 'ch', 'sn', 'co', 'za', 'cy', 'da', 'de', 'na', 'mh',
        'et', 'ang', 'en', 'es', 'eo', 'eu', 'to', 'fr', 'fy', 'fo', 'ga',
        'gv', 'sm', 'gd', 'gl', 'hr', 'io', 'ia', 'ie', 'ik', 'xh', 'is', 'zu',
        'it', 'kl', 'csb', 'kw', 'rw', 'rn', 'sw', 'ky', 'ku', 'la', 'lv',
        'lb', 'lt', 'li', 'ln', 'jbo', 'hu', 'mg', 'mi', 'mo', 'my', 'fj',
        'nah', 'nl', 'cr', 'no', 'nn', 'hsb', 'oc', 'om', 'ug', 'uz', 'nds',
        'pl', 'pt', 'ro', 'rm', 'qu', 'sg', 'sc', 'st', 'tn', 'sq', 'scn',
        'simple', 'ss', 'sk', 'sl', 'so', 'sh', 'fi', 'sv', 'tl', 'tt', 'vi',
        'tpi', 'tr', 'tw', 'vo', 'wa', 'wo', 'ts', 'yo', 'el', 'av', 'ab',
        'ba', 'be', 'bg', 'mk', 'mn', 'ru', 'sr', 'tg', 'uk', 'kk', 'hy', 'yi',
        'he', 'ur', 'ar', 'tk', 'sd', 'fa', 'ha', 'ps', 'dv', 'ks', 'ne', 'pi',
        'bh', 'mr', 'sa', 'hi', 'as', 'bn', 'pa', 'pnb', 'gu', 'or', 'ta',
        'te', 'kn', 'ml', 'si', 'th', 'lo', 'dz', 'ka', 'ti', 'am', 'chr',
        'iu', 'km', 'zh', 'ja', 'ko', 'shn',
    ]

    @classproperty
    def interwiki_putfirst(cls):
        cls.interwiki_putfirst = {
            'da': cls.alphabetic,
            'en': cls.alphabetic,
            'et': cls.alphabetic,
            'fi': cls.alphabetic,
            'fy': cls.fyinterwiki,
            'he': ['en'],
            'hu': ['en'],
            'ms': cls.alphabetic_revised,
            'pl': cls.alphabetic_revised,
            'sv': cls.alphabetic_sv,
            'simple': cls.alphabetic,
        }
        return cls.interwiki_putfirst

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
