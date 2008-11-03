# -*- coding: utf-8  -*-
from pywikibot import family

# Wikitech site

class Family(family.Family):

    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikitech'
        self.langs = {
            'en': 'wikitech.leuksman.com',
        }

    def version(self, code):
        return "1.12alpha"

    def scriptpath(self, code):
        return ''
