# -*- coding: utf-8  -*-
from pywikibot import family
import config

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'mac.wikia'

        self.langs = {
            'de':'de.mac.wikia.com',
            'en':'mac.wikia.com',
            'es':'es.mac.wikia.com',
            'fr':'fr.mac.wikia.com',
            'id':'id.mac.wikia.com',
            'it':'it.mac.wikia.com',
            'zh':'zh.mac.wikia.com',
            }

        # Most namespaces are inherited from family.Family.
        self.namespaces[4] = {
            '_default': [u'WikiMac', self.namespaces[4]['_default']],
            'id': u'Indonesia Macintosh Society',
            'zh': u'维基麦',
        }
        self.namespaces[5] = {
            '_default': [u'WikiMac talk', self.namespaces[5]['_default']],
            'de': u'WikiMac Diskussion',
            'es': u'WikiMac Discusión',
            'fr': u'Discussion WikiMac',
            'id': u'Pembicaraan Indonesia Macintosh Society',
            'it': u'Discussioni WikiMac',
            'zh': u'维基麦 talk',
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
        return "1.10alpha"

    def scriptpath(self, code):
        return ''

