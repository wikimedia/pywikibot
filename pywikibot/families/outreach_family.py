# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family


# Outreach wiki custom family
class Family(family.WikimediaFamily):
    def __init__(self):
        super(Family, self).__init__()
        self.name = u'outreach'
        self.langs = {
            'outreach': 'outreach.wikimedia.org',
        }
        self.interwiki_forward = 'wikipedia'
