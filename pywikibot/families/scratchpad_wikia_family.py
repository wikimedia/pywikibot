# -*- coding: utf-8  -*-
import family, config

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'scratchpad_wikia'

        self.langs = {
            'de':'de.mini.wikia.com',
            'en':'scratchpad.wikia.com',
            'fr':'bloc-notes.wikia.com',
            'ja':'ja.scratchpad.wikia.com',
            'zh':'zh.scratchpad.wikia.com',
            }

        # Most namespaces are inherited from family.Family.
        self.namespaces[1]['fr'] = u'Discuter'

        self.namespaces[3]['fr'] = u'Discussion Utilisateur'

        self.namespaces[4] = {
            '_default': u'Scratchpad',
            'de': u'Mini-Wikia',
            'fr': u'Bloc notes',
            'ja': u'Scratchpad Wiki',
            'zh': u'圍紀實驗室',
        }
        self.namespaces[5] = {
            '_default': u'Scratchpad talk',
            'de': u'Mini-Wikia Diskussion',
            'en': u'Scratchpad talk',
            'fr': u'Discussion Bloc notes',
            'ja': u'Scratchpad Wiki‐ノート',
            'zh': u'圍紀實驗室 talk',
        }
        self.namespaces[7]['fr'] = u'Discussion Fichier'

        self.namespaces[11]['fr'] = u'Discussion Modèle'

        self.namespaces[13]['fr'] = u'Discussion Aide'

        self.namespaces[15]['fr'] = u'Discussion Catégorie'

        self.namespaces[400] = {
            '_default': u'Video',
        }
        self.namespaces[401] = {
            '_default': u'Video talk',
        }
        self.namespaces[500] = {
            '_default': u'User blog',
            'de': u'Benutzer Blog',
        }
        self.namespaces[501] = {
            '_default': u'User blog comment',
            'de': u'Benutzer Blog Kommentare',
        }
        self.namespaces[502] = {
            '_default': u'Blog',
        }
        self.namespaces[503] = {
            '_default': u'Blog talk',
            'de': u'Blog Diskussion',
        }
        self.namespaces[110] = {
            '_default': u'Forum',
        }
        self.namespaces[111] = {
            '_default': u'Forum talk',
        }
        # A few selected big languages for things that we do not want to loop over
        # all languages. This is only needed by the titletranslate.py module, so
        # if you carefully avoid the options, you could get away without these
        # for another wikimedia family.

        self.languages_by_size = ['en','de']

    def version(self, code):
        return "1.14.0"

    def scriptpath(self, code):
        return ''

