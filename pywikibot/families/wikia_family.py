# -*- coding: utf-8  -*-

__version__ = '$Id$'

import family

# The Wikia Search family
# user-config.py: usernames['wikia']['wikia'] = 'User name'

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = u'wikia'

        self.langs = {
            u'wikia': None,
        }

    def hostname(self, code):
        return u'www.wikia.com'
    
    def version(self, code):
        return "1.15.1"

    def scriptpath(self, code):
        return ''

    def apipath(self, code):
        return '/api.php'
