#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Family module for Beta Wikivoyage."""
from __future__ import annotations

from pywikibot import family


class Family(family.BetaSubdomainFamily):

    """Family class for Beta Wikivoyage."""

    name = 'betawikivoyage'

    test_codes = ['en', 'pl', 'zh']
