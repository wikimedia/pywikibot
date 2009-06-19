# -*- coding: utf-8  -*-
import family, config

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'mac_wikia'

        self.langs = {
            'de':'de.mac.wikia.com',
            'en':'mac.wikia.com',
            'es':'es.mac.wikia.com',
            'fr':'fr.mac.wikia.com',
            'id':'id.mac.wikia.com',
            'it':'it.mac.wikia.com',
            'zh':'zh.mac.wikia.com',
            }

        # A few selected big languages for things that we do not want to loop over
        # all languages. This is only needed by the titletranslate.py module, so
        # if you carefully avoid the options, you could get away without these
        # for another wikimedia family.

        self.languages_by_size = ['en','de']

    def version(self, code):
        return "1.14"

    def scriptpath(self, code):
        return ''

