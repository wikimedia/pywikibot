# -*- coding: utf-8  -*-

__version__ = '$Id$'
from pywikibot import family, config

import family, config

# The test wikipedia family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'test'
        self.langs = {
            'test': 'test.wikipedia.org',
        }
        if config.SSL_connection:
            self.langs['test'] = None

    def version(self, code):
        return '1.16alpha-wmf'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
