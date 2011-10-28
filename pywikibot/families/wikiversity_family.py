# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wikiversity

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikiversity'

        self.languages_by_size = [
            'en', 'fr', 'de', 'ru', 'beta', 'cs', 'it', 'pt', 'es', 'ar', 'el',
            'sv', 'fi', 'ja',
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikiversity.org' % lang

        # Global bot allowed languages on http://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = ['ja',]

    def shared_image_repository(self, code):
        return ('commons', 'commons')
