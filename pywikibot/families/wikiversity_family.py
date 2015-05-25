# -*- coding: utf-8  -*-
"""Family module for Wikiversity."""
from __future__ import unicode_literals

from pywikibot import family

__version__ = '$Id$'


# The Wikimedia family that is known as Wikiversity
class Family(family.WikimediaFamily):

    """Family class for Wikiversity."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'wikiversity'

        self.languages_by_size = [
            'de', 'en', 'fr', 'ru', 'cs', 'it', 'beta', 'pt', 'es', 'ar', 'sv',
            'fi', 'sl', 'el', 'ja', 'ko',
        ]

        self.langs = dict([(lang, '%s.wikiversity.org' % lang)
                           for lang in self.languages_by_size])

        # Global bot allowed languages on
        # https://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = ['ja', ]
