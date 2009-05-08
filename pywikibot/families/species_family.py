# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The wikispecies family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'species'
        self.langs = {
            'species': 'species.wikimedia.org',
        }
        self.interwiki_forward = 'wikipedia'

    def version(self,code):
        return '1.15alpha'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
