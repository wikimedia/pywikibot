"""Family module for Wikisource."""
#
# (C) Pywikibot team, 2004-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family
from pywikibot.tools import classproperty


# The Wikimedia family that is known as Wikisource
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikisource."""

    name = 'wikisource'

    closed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/closed.dblist
        'ang', 'ht',
    ]
    removed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=dblists/deleted.dblist
        'tokipona',
    ]

    codes = {
        'ar', 'as', 'az', 'ban', 'bcl', 'be', 'bg', 'bn', 'br', 'bs', 'ca',
        'cs', 'cy', 'da', 'de', 'el', 'en', 'eo', 'es', 'et', 'eu', 'fa', 'fi',
        'fo', 'fr', 'gl', 'gu', 'he', 'hi', 'hr', 'hu', 'hy', 'id', 'is', 'it',
        'ja', 'jv', 'ka', 'kn', 'ko', 'la', 'li', 'lij', 'lt', 'mk', 'ml',
        'mr', 'ms', 'mul', 'my', 'nap', 'nl', 'no', 'or', 'pa', 'pl', 'pms',
        'pt', 'ro', 'ru', 'sa', 'sah', 'sk', 'sl', 'sr', 'su', 'sv', 'ta',
        'tcy', 'te', 'th', 'tr', 'uk', 'vec', 'vi', 'wa', 'yi', 'zh',
        'zh-min-nan',
    }

    # Sites we want to edit but not count as real languages
    test_codes = ['beta']

    category_redirect_templates = {
        '_default': (),
        'ar': ('تحويل تصنيف',),
        'bn': ('বিষয়শ্রেণী পুনর্নির্দেশ',),
        'en': ('Category redirect',),
        'es': ('Categoría redirigida',),
        'ro': ('Redirect categorie',),
        'zh': ('分類重定向',),
    }

    # All requests to 'mul.wikisource.org/*' are redirected to
    # the main page, so using 'wikisource.org'
    @classproperty
    def langs(cls):
        cls.langs = super().langs
        cls.langs['mul'] = cls.domain
        cls.langs['beta'] = 'en.wikisource.beta.wmflabs.org'
        return cls.langs

    # Need to explicitly inject the beta domain
    @classproperty
    def domains(cls):
        cls.domains = super().domains
        cls.domains.append(cls.langs['beta'])
        return cls.domains

    # All requests to unknown languages are also redirected to
    # the main page, so using mul alias, see T114574 and T241413
    @classproperty
    def code_aliases(cls):
        cls.code_aliases = super().code_aliases.copy()
        aliases = cls.known_codes + ['-', 'www']
        for code in aliases:
            if (code not in cls.codes
                    and code not in cls.closed_wikis
                    and code not in cls.code_aliases):
                cls.code_aliases[code] = 'mul'
        return cls.code_aliases

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    # https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = [
        'ar', 'as', 'az', 'ban', 'be', 'bg', 'bn', 'br', 'bs', 'ca', 'cy',
        'da', 'el', 'eo', 'et', 'eu', 'fa', 'fi', 'fo', 'gl', 'gu', 'hi', 'hr',
        'hy', 'id', 'it', 'ja', 'jv', 'kn', 'ko', 'lij', 'lt', 'mk', 'ml',
        'nap', 'nl', 'no', 'or', 'pa', 'pl', 'pms', 'pt', 'ro', 'sa', 'sah',
        'sk', 'sr', 'ta', 'te', 'th', 'tr', 'uk', 'vi', 'wa', 'yi', 'zh',
        'zh-min-nan',
    ]

    authornamespaces = {
        '_default': [0],
        'ar': [102],
        'be': [102],
        'bn': [100],
        'bg': [100],
        'ca': [106],
        'cs': [100],
        'da': [102],
        'en': [102],
        'eo': [102],
        'es': [106],
        'et': [106],
        'fa': [102],
        'fr': [102],
        'he': [108],
        'hr': [100],
        'hu': [100],
        'hy': [100],
        'it': [102],
        'ko': [100],
        'la': [102],
        'nap': [102],
        'nl': [102],
        'no': [102],
        'pl': [104],
        'pt': [102],
        'ro': [102],
        'sr': [100],
        'sv': [106],
        'tr': [100],
        'vi': [102],
        'zh': [102],
        'beta': [102],
    }

    # Subpages for documentation.
    # TODO: List is incomplete, to be completed for missing languages.
    # TODO: Remove comments for appropriate pages
    doc_subpages = {
        '_default': (('/doc', ),
                     ['as', 'az', 'bn', 'en', 'es', 'et', 'gu', 'hu', 'it',
                      'ja', 'kn', 'ml', 'mk', 'mr', 'pt', 'ro', 'sa', 'sah',
                      'ta', 'te', 'th', 'vi']
                     ),
        'ar': ('/شرح', '/doc'),
        'be': ('/Дакументацыя', ),
        'bn': ('/নথি', ),
        'br': ('/diellerezh', ),
        'de': ('/Doku', '/Meta'),
        'el': ('/τεκμηρίωση', ),
        'eo': ('/dokumentado', ),
        # 'fa': ('/صفحه الگو', ),
        # 'fa': ('/فضای‌نام توضیحات', ),
        # 'fa': ('/آغاز جعبه', ),
        # 'fa': ('/پایان جعبه۲', ),
        # 'fa': ('/آغاز جعبه۲', ),
        # 'fa': ('/پایان جعبه', ),
        # 'fa': ('/توضیحات', ),
        'fr': ('/documentation', ),
        'id': ('/dok', ),
        'ko': ('/설명문서', ),
        'no': ('/dok', ),
        'ru': ('/Документация', ),
        'sl': ('/dok', ),
        'sr': ('/док', ),
        'sv': ('/dok', ),
        'uk': ('/документація', ),
    }
