# -*- coding: utf-8  -*-
"""Family module for OpenStreetMap wiki."""

__version__ = '$Id$'

from pywikibot import family


# The project wiki of OpenStreetMap (OSM).
class Family(family.Family):

    """Family class for OpenStreetMap wiki."""

    def __init__(self):
        """Constructor."""
        family.Family.__init__(self)
        self.name = 'osm'
        self.langs = {
            'en': 'wiki.openstreetmap.org',
        }

    def version(self, code):
        """Return the version for this family."""
        return "1.22.7"
