# -*- coding: utf-8 -*-
"""Family module for Vikidia."""
#
# (C) Pywikibot team, 2010-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family


class Family(family.SubdomainFamily):

    """Family class for Vikidia."""

    name = 'vikidia'
    domain = 'vikidia.org'

    codes = ['ca', 'de', 'el', 'en', 'es', 'eu', 'fr', 'hy', 'it', 'ru', 'scn']

    # Sites we want to edit but not count as real languages
    test_codes = ['central', 'test']

    def protocol(self, code):
        """Return https as the protocol for this family."""
        return 'https'
