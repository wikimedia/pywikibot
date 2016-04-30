# -*- coding: utf-8  -*-
"""Family module for Vikidia."""
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import family


class Family(family.SubdomainFamily):

    """Family class for Vikidia."""

    name = 'vikidia'
    domain = 'vikidia.org'

    codes = ['ca', 'de', 'en', 'es', 'eu', 'fr', 'it', 'ru', 'scn']

    # Sites we want to edit but not count as real languages
    test_codes = ['central', 'test']

    def protocol(self, code):
        """Return https as the protocol for this family."""
        return "https"

    def ignore_certificate_error(self, code):
        """Ignore certificate errors."""
        return True  # has self-signed certificate for a different domain.
