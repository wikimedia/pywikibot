"""Family module for Wikitech."""
#
# (C) Pywikibot team, 2005-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The Wikitech family
class Family(family.WikimediaOrgFamily):

    """Family class for Wikitech."""

    name = 'wikitech'
    code = 'en'

    def protocol(self, code) -> str:
        """Return the protocol for this family."""
        return 'https'
