# -*- coding: utf-8 -*-
"""Family module for Wikivoyage."""
#
# (C) Pywikibot team, 2012-2017
#
# Distributed under the terms of the MIT license.
#
# The new wikivoyage family that is hosted at wikimedia
from __future__ import absolute_import, unicode_literals

from pywikibot import family


class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikivoyage."""

    name = 'wikivoyage'

    languages_by_size = [
        'en', 'de', 'fa', 'it', 'fr', 'pl', 'ru', 'nl', 'pt', 'zh', 'es',
        'he', 'fi', 'vi', 'sv', 'el', 'ro', 'uk', 'hi',
    ]

    category_redirect_templates = {
        '_default': (),
        'zh': ('分类重定向',),
    }

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = [
        'el', 'en', 'es', 'fa', 'ru',
    ]
