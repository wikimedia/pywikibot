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

__version__ = '$Id$'


class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikivoyage."""

    name = 'wikivoyage'

    def __init__(self):
        """Constructor."""
        self.languages_by_size = [
            'en', 'de', 'fa', 'it', 'fr', 'ru', 'pl', 'nl', 'pt', 'fi', 'es',
            'zh', 'he', 'vi', 'sv', 'el', 'ro', 'uk',
        ]

        super(Family, self).__init__()

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/BPI#Current_implementation
        # & https://meta.wikimedia.org/wiki/Special:WikiSets/2
        self.cross_allowed = [
            'el', 'en', 'es', 'fa', 'ru',
        ]
