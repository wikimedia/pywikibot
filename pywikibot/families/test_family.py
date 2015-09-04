# -*- coding: utf-8  -*-
"""Family module for test.wikipedia.org."""
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The test wikipedia family
class Family(family.SingleSiteFamily, family.WikimediaFamily):

    """Family class for test.wikipedia.org."""

    name = 'test'
    domain = 'test.wikipedia.org'
