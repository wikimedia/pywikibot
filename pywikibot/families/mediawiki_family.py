# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The MediaWiki family
# user-config.py: usernames['mediawiki']['mediawiki'] = 'User name'

class Family(family.WikimediaFamily):
    def __init__(self):
        super(Family, self).__init__()
        self.name = 'mediawiki'

        self.langs = {
            'mediawiki': 'www.mediawiki.org',
        }

    def ssl_pathprefix(self, code):
        return "/wikipedia/mediawiki"
