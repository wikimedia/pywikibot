# -*- coding: utf-8 -*-

__version__ = '$Id$'

# The new wikivoyage family that is hosted at wikimedia

from pywikibot import family

class Family(family.WikimediaFamily):
    def __init__(self):
        super(Family, self).__init__()
        self.name = 'wikivoyage'
        self.languages_by_size = [
            'en', 'de', 'pt', 'nl', 'fr', 'it', 'ru', 'sv', 'es', 'ro', 'pl',
        ]

        self.langs = dict([(lang, '%s.wikivoyage.org' % lang)
                           for lang in self.languages_by_size])
