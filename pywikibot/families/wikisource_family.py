# -*- coding: utf-8 -*-
"""Family module for Wikisource."""
#
# (C) Pywikibot team, 2004-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family
from pywikibot.tools import classproperty


# The Wikimedia family that is known as Wikisource
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikisource."""

    name = 'wikisource'

    closed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=closed.dblist
        'ang', 'ht',
    ]
    removed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=deleted.dblist
        'tokipona',
    ]

    languages_by_size = [
        'en', 'pl', 'ru', 'de', 'fr', 'zh', 'he', 'it', 'es', 'ar', 'cs', 'pt',
        'www', 'fa', 'hu', 'ml', 'ko', 'sv', 'gu', 'sr', 'bn', 'sl', 'te',
        'sa', 'el', 'ro', 'uk', 'fi', 'hy', 'ja', 'vi', 'az', 'th', 'ca', 'ta',
        'kn', 'br', 'nl', 'hr', 'is', 'la', 'no', 'vec', 'eo', 'tr', 'et',
        'be', 'mk', 'da', 'yi', 'id', 'bg', 'li', 'mr', 'as', 'or', 'bs',
        'sah', 'lt', 'gl', 'sk', 'eu', 'cy', 'pa', 'zh-min-nan', 'fo',
    ]

    category_redirect_templates = {
        '_default': (),
        'ar': ('قالب:تحويل تصنيف',),
        'bn': ('বিষয়শ্রেণী পুনর্নির্দেশ',),
        'en': ('Category redirect',),
        'ro': ('Redirect categorie',),
        'zh': ('分類重定向',),
    }

    # All requests to 'mul.wikisource.org/*' are redirected to
    # the main page, so using 'wikisource.org'
    @classproperty
    def langs(cls):
        cls.langs = super(Family, cls).langs
        cls.langs['mul'] = cls.domain
        return cls.langs

    languages_by_size.append('mul')

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    cross_allowed = [
        'ca', 'el', 'fa', 'it', 'ko', 'no', 'pl', 'vi', 'zh',
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
        'nl': [102],
        'no': [102],
        'pl': [104],
        'pt': [102],
        'ro': [102],
        'sv': [106],
        'tr': [100],
        'vi': [102],
        'zh': [102],
    }

    # Subpages for documentation.
    # TODO: List is incomplete, to be completed for missing languages.
    # TODO: Remove comments for appropriate pages
    doc_subpages = {
        '_default': (('/doc', ),
                     ['ar', 'as', 'az', 'bn', 'en', 'es',
                      'et', 'gu', 'hu', 'it', 'ja', 'kn', 'ml',
                      'mk', 'mr', 'pt', 'ro', 'sa', 'sah', 'ta',
                      'te', 'th', 'vi']
                     ),
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
        'sv': ('/dok', ),
        'uk': ('/документація', ),
    }
