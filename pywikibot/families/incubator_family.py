# -*- coding: utf-8  -*-
"""Family module for Incubator Wiki."""
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The Wikimedia Incubator family
class Family(family.WikimediaFamily):

    """Family class for Incubator Wiki."""

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        self.name = 'incubator'
        self.langs = {
            'incubator': 'incubator.wikimedia.org',
        }
