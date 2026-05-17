#
# (C) Pywikibot team, 2005-2026
#
# Distributed under the terms of the MIT license.
#
"""Family module for Wikitech."""
from __future__ import annotations

from pywikibot import family


# The Wikitech family
class Family(family.WikimediaOrgFamily):

    """Family class for Wikitech."""

    name = 'wikitech'
    code = 'en'

    def protocol(self, code) -> str:
        """Return the protocol for this family."""
        return 'https'
