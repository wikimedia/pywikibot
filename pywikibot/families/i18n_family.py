# -*- coding: utf-8 -*-
"""Family module for Translate Wiki."""
#
# (C) Pywikibot team, 2007-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family


# The Wikimedia i18n family
class Family(family.SingleSiteFamily):

    """Family class for Translate Wiki."""

    name = 'i18n'
    domain = 'translatewiki.net'

    def protocol(self, code):
        """Return https as the protocol for this family."""
        return 'https'
