# -*- coding: utf-8 -*-
"""Family module for Wikiversity."""
#
# (C) Pywikibot team, 2007-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikiversity
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikiversity."""

    name = 'wikiversity'

    def __init__(self):
        """Constructor."""
        self.languages_by_size = [
            'de', 'en', 'fr', 'ru', 'cs', 'it', 'beta', 'pt', 'es', 'ar', 'sv',
            'fi', 'sl', 'el', 'ja', 'ko',
        ]

        super(Family, self).__init__()

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/BPI#Current_implementation
        # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
        self.cross_allowed = ['ja', 'ko', ]
