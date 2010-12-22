# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The Wikitech family

class Family(family.Family):

    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikitech'
        self.langs = {
            'en': 'wikitech.wikimedia.org',
        }

    def version(self, code):
        return '1.16wmf4'

    def scriptpath(self, code):
        return ''
