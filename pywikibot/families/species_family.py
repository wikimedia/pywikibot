# -*- coding: utf-8 -*-
"""Family module for Wikimedia species wiki."""
#
# (C) Pywikibot team, 2007-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family


# The wikispecies family
class Family(family.WikimediaOrgFamily):

    """Family class for Wikimedia species wiki."""

    name = 'species'

    interwiki_forward = 'wikipedia'
