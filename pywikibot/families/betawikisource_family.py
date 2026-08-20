#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Family module for Beta Wikisource."""
from __future__ import annotations

from pywikibot import family


class Family(family.BetaSubdomainFamily):

    """Family class for Beta Wikisource."""

    name = 'betawikisource'

    test_codes = ['en']

    authornamespaces = {
        '_default': [0],
        'beta': [102],
    }
