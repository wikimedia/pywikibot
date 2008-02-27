# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The MediaWiki family
# user-config.py: usernames['mediawiki']['mediawiki'] = 'User name'

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'mediawiki'

        self.langs = {
            'mediawiki': 'www.mediawiki.org',
        }

        self.namespaces[4] = {
            '_default': [u'Project', self.namespaces[4]['_default']],
        }
        self.namespaces[5] = {
            '_default': [u'Project talk', self.namespaces[5]['_default']],
        }
        self.namespaces[100] = {
            '_default': u'Manual',
        }
        self.namespaces[101] = {
            '_default': u'Manual talk',
        }
        self.namespaces[102] = {
            '_default': u'Extension',
        }
        self.namespaces[103] = {
            '_default': u'Extension talk',
        }

    def version(self, code):
        return "1.12alpha"

    def shared_image_repository(self, code):
        return ('commons', 'commons')
