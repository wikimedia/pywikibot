# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The meta wikimedia family

class Family(family.WikimediaFamily):
    def __init__(self):
        super(Family, self).__init__()
        self.name = 'meta'
        self.langs = {
            'meta': 'meta.wikimedia.org',
        }
        self.interwiki_forward = 'wikipedia'
        self.cross_allowed = ['meta',]

    def ssl_pathprefix(self, code):
        return "/wikipedia/meta"
