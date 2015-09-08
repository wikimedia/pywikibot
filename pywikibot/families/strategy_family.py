# -*- coding: utf-8  -*-
"""Family module for Wikimedia Strategy Wiki."""
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The Wikimedia Strategy family
class Family(family.WikimediaOrgFamily):

    """Family class for Wikimedia Strategy Wiki."""

    name = 'strategy'

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()

        self.interwiki_forward = 'wikipedia'

    def dbName(self, code):
        """Return the database name for this family."""
        return 'strategywiki_p'
