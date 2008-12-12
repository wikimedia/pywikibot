# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The Wikimedia Commons family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'commons'
        self.langs = {
            'commons': 'commons.wikimedia.org',
        }

        self.interwiki_forward = 'wikipedia'
        self.disambiguationTemplates = {
            'commons': [u'Disambig', u'Disambiguation', u'Razločitev',
                        u'Begriffsklärung']
        }
        self.disambcatname = {
            'commons':  u'Disambiguation'
        }

    def version(self, code):
        return '1.14alpha'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
