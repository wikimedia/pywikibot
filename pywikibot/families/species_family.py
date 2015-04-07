# -*- coding: utf-8  -*-
"""Family module for Wikimedia species wiki."""
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The wikispecies family
class Family(family.WikimediaFamily):

    """Family class for Wikimedia species wiki."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'species'
        self.langs = {
            'species': 'species.wikimedia.org',
        }
        self.interwiki_forward = 'wikipedia'
