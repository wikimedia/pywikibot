# -*- coding: utf-8  -*-
__version__ = '$Id$'

from pywikibot import family

# ZRHwiki, formerly known as SouthernApproachWiki, a wiki about Zürich Airport.

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'southernapproach'
        self.langs = {
            'de':'www.zrhwiki.ch',
        }

    def version(self, code):
        return "1.17alpha"
