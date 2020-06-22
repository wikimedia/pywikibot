# -*- coding: utf-8 -*-
"""Family module for Wikiversity."""
#
# (C) Pywikibot team, 2007-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family
from pywikibot.tools import classproperty


# The Wikimedia family that is known as Wikiversity
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikiversity."""

    name = 'wikiversity'

    languages_by_size = [
        'de', 'en', 'fr', 'ru', 'zh', 'it', 'cs', 'pt', 'es', 'sv', 'sl', 'fi',
        'ar', 'el', 'hi', 'ko', 'ja',
    ]

    test_codes = ['beta']

    @classproperty
    def code_aliases(cls):
        cls.code_aliases = super(Family, cls).code_aliases.copy()
        cls.code_aliases['mul'] = 'beta'
        return cls.code_aliases

    category_redirect_templates = {
        '_default': (),
        'ar': ('قالب:تحويل تصنيف',),
        'en': ('Category redirect',),
    }

    # Global bot allowed languages on
    # https://meta.wikimedia.org/wiki/BPI#Current_implementation
    # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
    cross_allowed = [
        'ar', 'hi', 'ja', 'ko', 'zh',
    ]
