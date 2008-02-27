# -*- coding: utf-8  -*-
from pywikibot import family
import config

# ZRHwiki, formerly known as SouthernApproachWiki, a wiki about Zürich Airport.

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'southernapproach'
        self.langs = {
            'de':'www.zrhwiki.ch',
        }
        # Most namespaces are inherited from family.Family.
        self.namespaces[4] = {
            '_default': [u'ZRHwiki', self.namespaces[4]['_default']],
        }
        self.namespaces[5] = {
            '_default': [u'ZRHwiki Diskussion', self.namespaces[5]['_default']],
        }

    def version(self, code):
        return "1.12alpha"
