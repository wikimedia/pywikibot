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

    def version(self, code):
        return "1.15.1"

    def scriptpath(self, code):
        return ''

    def apipath(self, code):
        return '/api.php'