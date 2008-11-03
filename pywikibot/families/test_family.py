# -*- coding: utf-8  -*-

from pywikibot import family

# The test wikipedia family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'test'
        self.langs = {
            'test': 'test.wikipedia.org',
        }

    def version(self, code):
        return '1.13alpha'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
