# -*- coding: utf-8 -*-
"""Family module for OpenStreetMap wiki."""
#
# (C) Pywikibot team, 2009-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family


# The project wiki of OpenStreetMap (OSM).
class Family(family.SingleSiteFamily):

    """Family class for OpenStreetMap wiki."""

    name = 'osm'
    domain = 'wiki.openstreetmap.org'
    code = 'en'

    def protocol(self, code):
        """Return https as the protocol for this family."""
        return 'https'
