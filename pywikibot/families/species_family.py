# -*- coding: utf-8 -*-
"""Family module for Wikimedia species wiki."""
#
# (C) Pywikibot team, 2007-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The wikispecies family
class Family(family.WikimediaOrgFamily):

    """Family class for Wikimedia species wiki."""

    name = 'species'

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()

        self.interwiki_forward = 'wikipedia'
