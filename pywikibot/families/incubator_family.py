# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The Wikimedia Incubator family

class Family(family.WikimediaFamily):
    def __init__(self):
        super(Family, self).__init__()
        self.name = 'incubator'
        self.langs = {
            'incubator': 'incubator.wikimedia.org',
        }

    def ssl_pathprefix(self, code):
        return "/wikipedia/incubator"
