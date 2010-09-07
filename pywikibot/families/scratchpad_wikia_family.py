# -*- coding: utf-8  -*-
from pywikibot import family

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

        # A few selected big languages for things that we do not want to loop
        # over all languages. This is only needed by the titletranslate.py
        # module, so if you carefully avoid the options, you could get away
        # without these for another wikimedia family.

        self.languages_by_size = ['en','de']

    def version(self, code):
        return "1.14.0"

    def scriptpath(self, code):
        return ''

