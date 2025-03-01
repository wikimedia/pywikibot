"""Family module for Wikivoyage."""
#
# (C) Pywikibot team, 2012-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

# The new Wikivoyage family that is hosted at Wikimedia
from pywikibot import family


class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikivoyage."""

    name = 'wikivoyage'

    codes = {
        'bn', 'cs', 'de', 'el', 'en', 'eo', 'es', 'fa', 'fi', 'fr', 'he', 'hi',
        'id', 'it', 'ja', 'nl', 'pl', 'ps', 'pt', 'ro', 'ru', 'shn', 'sv',
        'tr', 'uk', 'vi', 'zh',
    }

    category_redirect_templates = {
        '_default': (),
        'bn': ('বিষয়শ্রেণী পুনর্নির্দেশ',),
        'zh': ('分类重定向',),
    }

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = [
        'bn', 'el', 'en', 'eo', 'es', 'fa', 'fi', 'hi', 'ja', 'pl', 'ps', 'pt',
        'ro', 'ru', 'shn', 'tr', 'uk', 'vi', 'zh',
    ]
