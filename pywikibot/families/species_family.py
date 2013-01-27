# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The wikispecies family

class Family(family.WikimediaFamily):
    def __init__(self):
        super(Family, self).__init__()
        self.name = 'species'
        self.langs = {
            'species': 'species.wikimedia.org',
        }
        self.interwiki_forward = 'wikipedia'

    def ssl_pathprefix(self, code):
        return "/wikipedia/species"
