# -*- coding: utf-8 -*-
"""Family module for Wikivoyage."""
#
# (C) Pywikibot team, 2012-2018
#
# Distributed under the terms of the MIT license.
#
# The new wikivoyage family that is hosted at wikimedia
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family


class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikivoyage."""

    name = 'wikivoyage'

    languages_by_size = [
        'en', 'de', 'pl', 'it', 'fa', 'fr', 'ru', 'zh', 'nl', 'pt', 'es', 'he',
        'fi', 'sv', 'el', 'vi', 'ro', 'uk', 'bn', 'ps', 'hi',
    ]

    category_redirect_templates = {
        '_default': (),
        'bn': ('বিষয়শ্রেণী পুনর্নির্দেশ',),
        'zh': ('分类重定向',),
    }

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = [
        'bn', 'el', 'en', 'es', 'fa', 'fi', 'hi', 'ps', 'ru',
    ]
