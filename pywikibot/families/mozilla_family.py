# -*- coding: utf-8  -*-

import family

# The official Mozilla Wiki.

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)

        self.name = 'mozilla'

        self.langs = {
                'en': 'wiki.mozilla.org',
        }
        self.namespaces[4] = {
            '_default': [u'MozillaWiki', self.namespaces[4]['_default']],
        }
        self.namespaces[5] = {
            '_default': [u'MozillaWiki talk', self.namespaces[5]['_default']],
        }

        self.content_id = "mainContent"

    def RversionTab(self, code):
        return r'<li\s*><a href=".*?title=.*?&amp;action=history".*?>.*?</a></li>'

    def version(self, code):
        return "1.6.8"

    def path(self, code):
        return '/index.php'
