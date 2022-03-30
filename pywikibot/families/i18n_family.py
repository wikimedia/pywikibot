"""Family module for Translate Wiki."""
#
# (C) Pywikibot team, 2007-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The Wikimedia i18n family
class Family(family.SingleSiteFamily):

    """Family class for Translate Wiki."""

    name = 'i18n'
    domain = 'translatewiki.net'

    def protocol(self, code) -> str:
        """Return https as the protocol for this family."""
        return 'https'
