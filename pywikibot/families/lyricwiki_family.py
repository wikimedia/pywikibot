# -*- coding: utf-8  -*-

import family

# The LyricWiki family

# user_config.py:
# usernames['lyricwiki']['en'] = 'user'

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'lyricwiki'
        self.langs = {
            'en': 'www.lyricwiki.org',
           }

        self.namespaces[4] = {
            '_default': [u'LyricWiki', self.namespaces[4]['_default']],
        }
        self.namespaces[5] = {
            '_default': [u'LyricWiki talk', self.namespaces[5]['_default']],
        }

    def version(self, code):
        return "1.7.1"

    def scriptpath(self, code):
        return ''

    def apipath(self, code):
        raise NotImplementedError(
            "The lyricwiki family does not support api.php")
