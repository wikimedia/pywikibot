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
            'en': 'lyrics.wikia.com',
           }

        self.namespaces[4] = {
            '_default': [u'LyricWiki', self.namespaces[4]['_default']],
        }
        self.namespaces[5] = {
            '_default': [u'LyricWiki talk', self.namespaces[5]['_default']],
        }
        self.namespaces[110] = { '_default': u'Forum', }
        self.namespaces[111] = { '_default': u'Forum talk', }
        self.namespaces[112] = { '_default': u'Gracenote', }
        self.namespaces[113] = { '_default': u'Gracenote talk', }
        self.namespaces[400] = { '_default': u'Video', }
        self.namespaces[401] = { '_default': u'Video talk', }
        self.namespaces[500] = { '_default': u'User blog', }
        self.namespaces[501] = { '_default': u'User blog comment', }
        self.namespaces[502] = { '_default': u'Blog', }
        self.namespaces[503] = { '_default': u'Blog talk', }

    def version(self, code):
        return "1.15.1"

    def scriptpath(self, code):
        return ''

    def apipath(self, code):
        return '/api.php'