# -*- coding: utf-8  -*-

import family

# I added this becouse someone asked me to. The url op the wiki:  nl.wikibond.org

class Family(family.Family):
   
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikibond'
        self.langs = {
            'nl': 'nl.wikibond.org',
        }
        self.namespaces[4] = {
            'nl': [u'WikiBond'],
        }
        self.namespaces[5] = {
            'nl': [u'Overleg WikiBond'],
        }

    def path(self, code):
        return '/wikibond/index.php'

    def version(self, code):
        return "1.11alpha"
