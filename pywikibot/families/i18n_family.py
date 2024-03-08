"""Family module for Translate Wiki."""
#
# (C) Pywikibot team, 2007-2023
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family


# The Wikimedia i18n family
class Family(family.SingleSiteFamily):

    """Family class for Translate Wiki."""

    name = 'i18n'
    domain = 'translatewiki.net'
