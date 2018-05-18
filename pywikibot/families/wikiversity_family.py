# -*- coding: utf-8 -*-
"""Family module for Wikiversity."""
#
# (C) Pywikibot team, 2007-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family


# The Wikimedia family that is known as Wikiversity
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikiversity."""

    name = 'wikiversity'

    languages_by_size = [
        'de', 'en', 'fr', 'ru', 'it', 'cs', 'beta', 'pt', 'es', 'ar', 'sv',
        'fi', 'sl', 'el', 'hi', 'ja', 'ko',
    ]

    category_redirect_templates = {
        '_default': (),
        'ar': ('قالب:تحويل تصنيف',),
        'en': ('Category redirect',),
    }

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = ['ja', 'ko', ]
