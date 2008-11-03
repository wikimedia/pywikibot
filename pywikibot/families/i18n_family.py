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

    def version(self, code):
        return "1.14alpha"
