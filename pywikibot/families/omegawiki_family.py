# -*- coding: utf-8  -*-
"""Family module for Omega Wiki."""
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot import family


# Omegawiki, the Ultimate online dictionary
class Family(family.SingleSiteFamily):

    """Family class for Omega Wiki."""

    name = 'omegawiki'
    domain = 'www.omegawiki.org'

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()

        # On most Wikipedias page names must start with a capital letter, but some
        # languages don't use this.

        self.nocapitalize = list(self.langs.keys())

    def scriptpath(self, code):
        """Return the script path for this family."""
        return ''

    def protocol(self, code):
        """Return https as the protocol for this family."""
        return "https"

    def ignore_certificate_error(self, code):
        """Ignore certificate errors."""
        return True  # has an expired certificate.
