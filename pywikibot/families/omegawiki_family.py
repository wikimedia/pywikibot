"""Family module for Omega Wiki."""
#
# (C) Pywikibot team, 2006-2020
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# Omegawiki, the Ultimate online dictionary
class Family(family.SingleSiteFamily):

    """Family class for Omega Wiki."""

    name = 'omegawiki'
    domain = 'www.omegawiki.org'

    def scriptpath(self, code):
        """Return the script path for this family."""
        return ''
