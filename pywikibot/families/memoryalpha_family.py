# -*- coding: utf-8  -*-
import family
    
# The Memory Alpha family, a set of StarTrek wikis.

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'memoryalpha'
    
        self.langs = {
            'de': None,
            'en': None,
            'eo': None,
            'es': None,
            'fr': None,
            'nl': None,
            'pl': None,
            'sv': None,
            }

        # Override defaults
        self.namespaces[2]['pl'] = u'Użytkownik'
        self.namespaces[3]['pl'] = u'Dyskusja użytkownika'
    
        # Most namespaces are inherited from family.Family.
		
        self.namespaces[4] = {
            '_default': u'Memory Alpha',
        }
        self.namespaces[5] = {
            '_default': u'Memory Alpha talk',
            'de': u'Memory Alpha Diskussion',
            'eo': u'Memory Alpha diskuto',
            'es': u'Memory Alpha Discusión',
            'fr': u'Discussion Memory Alpha',
            'nl': u'Overleg Memory Alpha',
            'pl': u'Dyskusja Memory Alpha',
            'sv': u'Memory Alphadiskussion',
        }
        self.namespaces[100] = {
			'_default': u'Forum',
		}
        self.namespaces[101] = {
			'_default': u'Forum talk',
			'de': u'Forum Diskussion',
		}
        
        # A few selected big languages for things that we do not want to loop over
        # all languages. This is only needed by the titletranslate.py module, so
        # if you carefully avoid the options, you could get away without these
        # for another wiki family.
        self.languages_by_size = ['en', 'de', 'es', 'nl', 'sv', 'fr', 'eo', 'pl']
		
        alphabetic = ['de', 'en', 'es', 'eo', 'fr', 'nl', 'pl', 'sv']

    def hostname(self,code):
        return 'www.memory-alpha.org'

    def path(self, code):
        return '/%s/index.php' % code

    def version(self, code):
        return "1.10alpha"
