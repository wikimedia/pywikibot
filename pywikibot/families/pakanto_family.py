# -*- coding: utf-8  -*-

__version__ = '$Id$'

import family

# The Pakanto wiki, a project to maintain Linux package descriptions

class Family(family.Family):
    
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'pakanto'
        self.langs = {
            'pakanto': 'pakanto.org',
        }
        
        self.namespaces[4] = {
            '_default': [u'Pakanto', self.namespaces[4]['_default']],
        }
        self.namespaces[5] = {
            '_default': [u'Pakanto talk', self.namespaces[5]['_default']],
        }

    def path(self, code):
        return '/index.php'

    def querypath(self, code):
        return '/query.php'

    def version(self, code):
        return "1.11alpha"

