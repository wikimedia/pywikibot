#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Family module for Beta Wikibooks."""
from __future__ import annotations

from pywikibot import family


class Family(family.BetaSubdomainFamily):

    """Family class for Beta Wikibooks."""

    name = 'betawikibooks'

    test_codes = ['en', 'es', 'he']
