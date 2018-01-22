# -*- coding: utf-8 -*-
"""Family module for test.wikipedia.org."""
#
# (C) Pywikibot team, 2007-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family


# The test wikipedia family
class Family(family.SingleSiteFamily, family.WikimediaFamily):

    """Family class for test.wikipedia.org."""

    name = 'test'
    domain = 'test.wikipedia.org'
    test_codes = ('test', )
