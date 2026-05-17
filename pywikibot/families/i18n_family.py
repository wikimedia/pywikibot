#
# (C) Pywikibot team, 2007-2026
#
# Distributed under the terms of the MIT license.
#
"""Family module for Translate Wiki."""
from __future__ import annotations

from pywikibot import family


# The Wikimedia i18n family
class Family(family.SingleSiteFamily):

    """Family class for Translate Wiki."""

    name = 'i18n'
    domain = 'translatewiki.net'
