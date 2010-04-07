# -*- coding: utf-8  -*-

__version__ = '$Id$'

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
        return '1.16-wmf'

    def shared_image_repository(self, code):
        return ('commons', 'commons')

    def ssl_pathprefix(self, code):
        return "/wikipedia/test"
