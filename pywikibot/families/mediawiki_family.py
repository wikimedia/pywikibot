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

    def version(self, code):
        return '1.16alpha-wmf'

    def shared_image_repository(self, code):
        return ('commons', 'commons')

    def ssl_pathprefix(self, code):
        return "/wikipedia/mediawiki"
