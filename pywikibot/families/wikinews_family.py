# -*- coding: utf-8 -*-
"""Family module for Wikinews."""
#
# (C) Pywikibot team, 2005-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family


# The Wikimedia family that is known as Wikinews
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikinews."""

    name = 'wikinews'

    closed_wikis = [
        # https://noc.wikimedia.org/conf/highlight.php?file=closed.dblist
        'hu', 'sd', 'th',
    ]

    languages_by_size = [
        'sr', 'en', 'fr', 'ru', 'de', 'pt', 'pl', 'es', 'it', 'ar', 'zh',
        'cs', 'ca', 'nl', 'el', 'ta', 'sv', 'uk', 'fa', 'ro', 'tr', 'ja',
        'sq', 'no', 'eo', 'fi', 'bs', 'ko', 'he', 'bg',
    ]

    category_redirect_templates = {
        '_default': (),
        'ar': ('قالب:تحويل تصنيف',),
        'fa': ('الگو:رده بهتر',),
        'no': ('Kategoriomdirigering',),
        'ro': ('Redirect categorie',),
        'ru': ('Category redirect',),
        'tr': ('Kategori yönlendirme',),
        'zh': ('分类重定向',),
    }

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = [
        'ar', 'bg', 'bs', 'ca', 'cs', 'el', 'en', 'eo', 'fa', 'fi', 'he',
        'ja', 'ko', 'nl', 'no', 'pt', 'ro', 'sq', 'sr', 'sv', 'ta', 'tr',
        'uk', 'zh',
    ]

    # TODO:
    # Change site_tests.py when wikinews will have doc_subpage.
