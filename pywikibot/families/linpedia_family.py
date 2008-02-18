# -*- coding: utf-8  -*-
import family, config

# Linpedia.org, the GNU/Linux encyclopedia

class Family(family.Family):

    def __init__(self):
        family.Family.__init__(self)
	self.name = 'linpedia'
	
        self.langs = {
            'en':'www.linpedia.org',
        }

# Namespaces
        
        self.namespaces[4] = {
	    '_default': [u'Linpedia', self.namespaces[4]['_default']],
	    }
	self.namespaces[5] = {
	    '_default': [u'Linpedia talk', self.namespaces[5]['_default']],
	    }
	
    def version(self, code):
        return "1.4"

    def path(self, code):
        return '/wiki/index.php'
