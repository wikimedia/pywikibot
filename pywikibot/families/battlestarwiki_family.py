# -*- coding: utf-8  -*-
__version__ = '$Id$'

from pywikibot import family

# The Battlestar Wiki family, a set of Battlestar wikis.
# http://battlestarwiki.org/

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'battlestarwiki'

        self.languages_by_size = ['en', 'de', 'fr', 'zh', 'es', 'ms', 'tr', 'simple']

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.battlestarwiki.org' % lang

        # A few selected big languages for things that we do not want to loop over
        # all languages. This is only needed by the titletranslate.py module, so
        # if you carefully avoid the options, you could get away without these
        # for another wiki family.

        alphabetic = ['de', 'en', 'es', 'fr', 'tr', 'zh']

    def hostname(self,code):
        return '%s.battlestarwiki.org' % code

    def version(self, code):
        return "1.15.0"
