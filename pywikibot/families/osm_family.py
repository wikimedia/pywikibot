# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The project wiki of OpenStreetMap (OSM).

class Family(family.Family):

    def __init__(self):
        family.Family.__init__(self)
        self.name = 'osm'
        self.langs = {
            'en': 'wiki.openstreetmap.org',
        }

    def version(self, code):
        return "1.16.2"
