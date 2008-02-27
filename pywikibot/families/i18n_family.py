# -*- coding: utf-8  -*-

__version__ = '$Id: incubator_family.py 4068 2007-08-18 13:10:09Z btongminh $'

from pywikibot import family

# The Wikimedia i18n family (should be called Betawiki, but already exists)

class Family(family.Family):
    
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'i18n'
        self.langs = {
            'i18n': 'translatewiki.net',
        }
        
        self.namespaces[4] = {
            '_default': [u'Betawiki'],
        }
        self.namespaces[5] = {
            '_default': [u'Betawiki talk'],
        }
        self.namespaces[100] = {
            '_default': [u'Portal'],
        }
        self.namespaces[101] = {
            '_default': [u'Portal talk'],
        }
        self.namespaces[1102] = {
            '_default': [u'Translating'],
        }
        self.namespaces[1103] = {
            '_default': [u'Translating talk'],
        }

    def version(self, code):
        return "1.12alpha"
