# -*- coding: utf-8 -*-
"""Family module for Wikimedia outreach wiki."""
#
# (C) Pywikibot team, 2014-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family


# Outreach wiki custom family
class Family(family.WikimediaOrgFamily):

    """Family class for Wikimedia outreach wiki."""

    name = 'outreach'

    interwiki_forward = 'wikipedia'
