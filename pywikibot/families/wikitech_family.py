# -*- coding: utf-8  -*-
"""Family module for Wikitech."""
__version__ = '$Id$'

from pywikibot import family


# The Wikitech family
class Family(family.Family):

    """Family class for Wikitech."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'wikitech'
        self.langs = {
            'en': 'wikitech.wikimedia.org',
        }

    def version(self, code):
        """Return the version for this family."""
        return '1.21wmf8'

    def protocol(self, code):
        """Return the protocol for this family."""
        return 'https'
