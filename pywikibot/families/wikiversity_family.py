# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wikiversity

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikiversity'

        self.languages_by_size = [
            'en', 'fr', 'ru', 'beta', 'cs', 'de', 'it', 'pt', 'es', 'ar', 'el',
            'sv', 'fi', 'ja',
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikiversity.org' % lang

    def shared_image_repository(self, code):
        return ('commons', 'commons')
