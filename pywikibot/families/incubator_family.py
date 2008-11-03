# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The Wikimedia Incubator family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'incubator'
        self.langs = {
            'incubator': 'incubator.wikimedia.org',
        }

    def version(self, code):
        return '1.13alpha'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
