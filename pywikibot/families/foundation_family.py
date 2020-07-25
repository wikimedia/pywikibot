# -*- coding: utf-8 -*-
"""Family module for Foundation wiki."""
#
# (C) Pywikibot team, 2019-2020
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The Foundation family
class Family(family.WikimediaFamily, family.SingleSiteFamily):

    """Family class for Foundation wiki."""

    name = 'foundation'
    domain = 'foundation.wikimedia.org'

    interwiki_forward = 'wmf'
