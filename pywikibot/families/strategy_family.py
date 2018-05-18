# -*- coding: utf-8 -*-
"""Family module for Wikimedia Strategy Wiki."""
#
# (C) Pywikibot team, 2009-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family


# The Wikimedia Strategy family
class Family(family.WikimediaOrgFamily):

    """Family class for Wikimedia Strategy Wiki."""

    name = 'strategy'

    interwiki_forward = 'wikipedia'

    def dbName(self, code):
        """Return the database name for this family."""
        return 'strategywiki_p'
