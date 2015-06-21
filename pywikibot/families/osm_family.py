# -*- coding: utf-8  -*-
"""Family module for OpenStreetMap wiki."""
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The project wiki of OpenStreetMap (OSM).
class Family(family.SingleSiteFamily):

    """Family class for OpenStreetMap wiki."""

    name = 'osm'
    domain = 'wiki.openstreetmap.org'
    code = 'en'

    def protocol(self, code):
        """Return https as the protocol for this family."""
        return "https"
