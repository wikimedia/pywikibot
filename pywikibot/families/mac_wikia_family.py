# -*- coding: utf-8  -*-
from pywikibot import family

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

        self.languages_by_size = ['en','de']

    def version(self, code):
        return "1.14"

    def scriptpath(self, code):
        return ''

