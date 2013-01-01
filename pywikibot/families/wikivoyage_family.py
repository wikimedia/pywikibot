# -*- coding: utf-8 -*-

__version__ = '$Id$'

# The new wikivoyage family that is hosted at wikimedia

from pywikibot import family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikivoyage'
        self.languages_by_size = [
            'de', 'en', 'fr', 'it', 'nl', 'ru','sv',
        ]

        self.langs = dict([(lang, '%s.wikivoyage.org' % lang) for lang in self.languages_by_size])

        }

    def scriptpath(self, code):
        return u'/w'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
