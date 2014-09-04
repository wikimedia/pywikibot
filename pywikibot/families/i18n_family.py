# -*- coding: utf-8  -*-
"""Family module for Translate Wiki."""

__version__ = '$Id$'

from pywikibot import family


# The Wikimedia i18n family
class Family(family.Family):

    """Family class for Translate Wiki."""

    def __init__(self):
        """Constructor."""
        family.Family.__init__(self)
        self.name = 'i18n'
        self.langs = {
            'i18n': 'translatewiki.net',
        }

    def version(self, code):
        """Return the version for this family."""
        return "1.23alpha"
