# -*- coding: utf-8  -*-

__version__ = '$Id$'

import family

# The project wiki of OpenStreetMap (OSM).

class Family(family.Family):

    def __init__(self):
        family.Family.__init__(self)
        self.name = 'osm'
        self.langs = {
            'en': 'wiki.openstreetmap.org',
        }

    def scriptpath(self, code):
        return ''

    def version(self, code):
        return "1.13.3"
