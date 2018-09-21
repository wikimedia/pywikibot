# -*- coding: utf-8 -*-
"""Family module for Wikitech."""
#
# (C) Pywikibot team, 2005-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family


# The Wikitech family
class Family(family.WikimediaOrgFamily):

    """Family class for Wikitech."""

    name = 'wikitech'
    code = 'en'

    def protocol(self, code):
        """Return the protocol for this family."""
        return 'https'
