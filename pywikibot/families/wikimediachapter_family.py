# -*- coding: utf-8 -*-
"""Family module for Wikimedia chapter, thematic organisation and WUG wikis."""
#
# (C) Pywikibot team, 2012-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family
from pywikibot.tools import deprecated, classproperty


class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for WCH, WTO and WUG wikis hosted on wikimedia.org."""

    name = 'wikimediachapter'
    code_aliases = {
        'et': 'ee'
    }

    closed_wikis = ['nz', 'pa-us', ]

    codes = [
        'am', 'ar', 'bd', 'be', 'br', 'ca', 'cn', 'co', 'dk', 'ec', 'ee', 'fi',
        'ge', 'gr', 'hi', 'id', 'id-internal', 'il', 'mai', 'mk', 'mx',
        'ng', 'nl', 'no', 'nyc', 'pl', 'pt', 'punjabi', 'romd', 'rs', 'ru',
        'se', 'tr', 'ua', 'uk', 've', 'wb',
    ]

    @classproperty
    @deprecated(since='20150621')
    def countries(cls):
        """Deprecated."""
        return cls.codes
