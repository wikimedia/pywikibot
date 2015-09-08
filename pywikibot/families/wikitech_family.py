# -*- coding: utf-8  -*-
"""Family module for Wikitech."""
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The Wikitech family
class Family(family.WikimediaOrgFamily):

    """Family class for Wikitech."""

    name = 'wikitech'
    code = 'en'

    def protocol(self, code):
        """Return the protocol for this family."""
        return 'https'
