# -*- coding: utf-8 -*-
"""Family module for Wikimedia chapter wikis."""
#
# (C) Pywikibot team, 2012-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family
from pywikibot.tools import deprecated


class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family for Wikimedia chapters hosted on wikimedia.org."""

    name = 'wikimediachapter'
    code_aliases = {}

    codes = [
        'ar', 'br', 'bd', 'co', 'dk', 'fi', 'mk', 'mx', 'nl', 'no',
        'nyc', 'pl', 'rs', 'ru', 'se', 'ua', 'uk', 've',
    ]

    @property
    @deprecated
    def countries(self):
        """Deprecated."""
        return self.codes
