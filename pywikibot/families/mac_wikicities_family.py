# -*- coding: utf-8  -*-
import family, config
    
class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'mac_wikicities'
        
        self.langs = {
            'de':'de.mac.wikicities.com',
            'en':'en.mac.wikicities.com',
            'es':'es.mac.wikicities.com',
            'fr':'fr.mac.wikicities.com',
            'it':'it.mac.wikicities.com',
            'zh':'zh.mac.wikicities.com',
            }
    
        # Most namespaces are inherited from family.Family.
        self.namespaces[4] = {
            '_default': [u'WikiMac', self.namespaces[4]['_default']],
        }
        self.namespaces[5] = {
            '_default': [u'WikiMac talk', self.namespaces[5]['_default']],
            'de': u'WikiMac Diskussion',
        }
            
        # A few selected big languages for things that we do not want to loop over
        # all languages. This is only needed by the titletranslate.py module, so
        # if you carefully avoid the options, you could get away without these
        # for another wikimedia family.
    
        self.languages_by_size = ['en','de']

    def version(self, code):
        return "1.10alpha"
    
    def path(self, code):
        return '/index.php'
