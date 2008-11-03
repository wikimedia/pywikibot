# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The meta wikimedia family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'meta'
        self.langs = {
            'meta': 'meta.wikimedia.org',
        }
        self.interwiki_forward = 'wikipedia'

    def version(self,code):
        return '1.13alpha'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
