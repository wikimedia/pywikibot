# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The Wikimedia Strategy family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'strategy'
        self.langs = {
            'strategy': 'strategy.wikimedia.org',
        }
        self.interwiki_forward = 'wikipedia'

    def version(self, code):
        return '1.17wmf1'

    def dbName(self, code):
        return 'strategywiki_p'

    def shared_image_repository(self, code):
        return ('commons', 'commons')

    def ssl_pathprefix(self, code):
        return "/wikipedia/strategy"
