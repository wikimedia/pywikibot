# -*- coding: utf-8  -*-
__version__ = '$Id$'

import family

# The official Beta Wiki.
class Family(family.Family):

    def __init__(self):

        family.Family.__init__(self)
        self.name = 'fon'

        self.langs = {
            'en': None,
        }

    def hostname(self, code):
        return 'wiki.fon.com'

    def scriptpath(self, code):
        return '/mediawiki'

    def version(self, code):
        return "1.15.1"
