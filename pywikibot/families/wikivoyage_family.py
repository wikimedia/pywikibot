# -*- coding: utf-8 -*-
"""Family module for Wikivoyage."""

__version__ = '$Id$'

# The new wikivoyage family that is hosted at wikimedia

from pywikibot import family


class Family(family.WikimediaFamily):

    """Family class for Wikivoyage."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'wikivoyage'
        self.languages_by_size = [
            'en', 'de', 'fr', 'it', 'pt', 'nl', 'pl', 'ru', 'es', 'vi', 'sv',
            'zh', 'he', 'ro', 'uk', 'el', 'fa'
        ]

        self.langs = dict([(lang, '%s.wikivoyage.org' % lang)
                           for lang in self.languages_by_size])
        # Global bot allowed languages on https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = ['es', 'ru', ]

    def shared_data_repository(self, code, transcluded=False):
        """Return the shared data repository for this site."""
        return ('wikidata', 'wikidata')
