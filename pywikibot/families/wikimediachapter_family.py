# -*- coding: utf-8 -*-
"""Family module for Wikimedia chapter, thematic organisation and WUG wikis."""
#
# (C) Pywikibot team, 2012-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family
from pywikibot.tools import deprecated, classproperty


class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for WCH, WTO and WUG wikis hosted on wikimedia.org."""

    name = 'wikimediachapter'
    code_aliases = {}

    closed_wikis = ['nz', 'pa-us', ]

    codes = [
        'am', 'ar', 'bd', 'be', 'br', 'ca', 'cn', 'co', 'dk', 'ec', 'et', 'fi',
        'il', 'mai', 'mk', 'mx', 'nl', 'no', 'nyc', 'pl', 'pt', 'rs', 'ru',
        'se', 'tr', 'ua', 'uk', 've', 'wb',
    ]

    @classproperty
    @deprecated
    def countries(cls):
        """Deprecated."""
        return cls.codes
