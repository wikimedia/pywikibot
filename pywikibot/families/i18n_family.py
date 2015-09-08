# -*- coding: utf-8  -*-
"""Family module for Translate Wiki."""
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The Wikimedia i18n family
class Family(family.SingleSiteFamily):

    """Family class for Translate Wiki."""

    name = 'i18n'
    domain = 'translatewiki.net'

    def protocol(self, code):
        """Return https as the protocol for this family."""
        return "https"
