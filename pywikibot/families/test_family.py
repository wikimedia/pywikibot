# -*- coding: utf-8  -*-
"""Family module for test.wikipedia.org."""
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The test wikipedia family
class Family(family.WikimediaFamily):

    """Family class for test.wikipedia.org."""

    name = 'test'
    langs = {'test': 'test.wikipedia.org'}

    def from_url(self, url):
        """Return None to indicate no code of this family is accepted."""
        return None  # Don't accept this, but 'test' of 'wikipedia'
