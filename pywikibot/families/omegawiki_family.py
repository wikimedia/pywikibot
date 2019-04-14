# -*- coding: utf-8 -*-
"""Family module for Omega Wiki."""
#
# (C) Pywikibot team, 2006-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family


# Omegawiki, the Ultimate online dictionary
class Family(family.SingleSiteFamily):

    """Family class for Omega Wiki."""

    name = 'omegawiki'
    domain = 'www.omegawiki.org'

    # On most Wikipedias page names must start with a capital letter, but some
    # languages don't use this.
    nocapitalize = ['omegawiki']

    def scriptpath(self, code):
        """Return the script path for this family."""
        return ''
