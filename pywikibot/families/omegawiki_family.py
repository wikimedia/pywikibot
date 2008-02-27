# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# Omegawiki, the Ultimate online dictionary

class Family(family.Family):

    def __init__(self):
        family.Family.__init__(self)
        self.name = 'omegawiki'
        self.langs = {
            'en': 'omegawiki.org',
        }
        self.namespaces[4] = {
            '_default': [u'OmegaWiki'],
        }
        self.namespaces[5] = {
            '_default': [u'OmegaWiki talk'],
        }
        self.namespaces[6] = {
            '_default': [u'File'],
        }
        self.namespaces[7] = {
            '_default': [u'File talk'],
        }
        self.namespaces[16] = {
            '_default': [u'Expression'],
        }
        self.namespaces[17] = {
            '_default': [u'Expression talk'],
        }
        self.namespaces[18] = {
            '_default': [u'Collection'],
        }
        self.namespaces[19] = {
            '_default': [u'Collection talk'],
        }
        self.namespaces[20] = {
            '_default': [u'Relation'],
        }
        self.namespaces[21] = {
            '_default': [u'Relation talk'],
        }
        self.namespaces[22] = {
            '_default': [u'Portal'],
        }
        self.namespaces[23] = {
            '_default': [u'Portal talk'],
        }
        self.namespaces[24] = {
            '_default': [u'DefinedMeaning'],
        }
        self.namespaces[25] = {
            '_default': [u'DefinedMeaning talk'],
        }
        self.namespaces[26] = {
            '_default': [u'Search'],
        }
        self.namespaces[27] = {
            '_default': [u'Search talk'],
        }
        self.namespaces[28] = {
            '_default': [u'NeedsTranslationTo'],
        }
        self.namespaces[29] = {
            '_default': [u'NeedsTranslationTo talk'],
        }

        # On most Wikipedias page names must start with a capital letter, but some
        # languages don't use this.

        self.nocapitalize = self.langs.keys()

    def version(self, code):
        return "1.10alpha"

