#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Family module for Beta Wiktionary."""
from __future__ import annotations

from pywikibot import family


class Family(family.BetaSubdomainFamily):

    """Family class for Beta Wiktionary."""

    name = 'betawiktionary'

    test_codes = ['de', 'en', 'fr', 'he']
