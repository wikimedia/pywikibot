#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Family module for Beta Wikiquotes."""
from __future__ import annotations

from pywikibot import family


class Family(family.BetaSubdomainFamily):

    """Family class for Beta Wikiquotes."""

    name = 'betawikiquotes'

    test_codes = ['en']
