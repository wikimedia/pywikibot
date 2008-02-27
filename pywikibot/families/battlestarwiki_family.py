# -*- coding: utf-8  -*-
from pywikibot import family
    
# The Battlestar Wiki family, a set of Battlestar wikis.
# http://battlestarwiki.org/

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'battlestarwiki'
    
        self.langs = {
            'de': None,
            'en': None,
            'es': None,
            'fr': None,
            'tr': None,
            'zh': None,
            }

        # Most namespaces are inherited from family.
		
        self.namespaces[4] = {
            '_default': u'Battlestar Wiki',
        }
        self.namespaces[5] = {
            '_default': u'Battlestar Wiki talk',
            'de': u'Battlestar Wiki Diskussion',
            'es': u'Battlestar Wiki Discusión',
            'fr': u'Discussion Battlestar Wiki',
            'tr': u'Battlestar Wiki tartışma',
        }

        # Custom namespaces that a needed

        self.namespaces[100] = { '_default': u'Portal', }
        self.namespaces[101] = { '_default': u'Portal talk', }
        self.namespaces[102] = { '_default': u'Sources', }
        self.namespaces[103] = { '_default': u'Sources talk', }
        self.namespaces[104] = { '_default': u'Quotes', }
        self.namespaces[105] = { '_default': u'Quotes talk', }
        self.namespaces[106] = { '_default': u'Podcast', }
        self.namespaces[107] = { '_default': u'Podcast talk', }

        # A few selected big languages for things that we do not want to loop over
        # all languages. This is only needed by the titletranslate.py module, so
        # if you carefully avoid the options, you could get away without these
        # for another wiki family.
        self.languages_by_size = ['en', 'de']
		
        alphabetic = ['de', 'en', 'es', 'fr', 'tr', 'zh']

    def hostname(self,code):
        return '%s.battlestarwiki.org' % code

    def version(self, code):
        return "1.9"
