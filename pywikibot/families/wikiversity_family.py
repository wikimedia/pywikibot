# -*- coding: utf-8  -*-
import urllib
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wikiversity

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikiversity'

        self.languages_by_size = [
            'en', 'fr', 'es', 'de', 'it', 'el', 'cs', 'ja', 'pt',
        ]

        self.langs = {
            'beta': 'beta.wikiversity.org',
        }
        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikiversity.org' % lang

    def version(self,code):
        return '1.14alpha'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
