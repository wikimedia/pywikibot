#
# (C) Pywikibot team, 2006-2026
#
# Distributed under the terms of the MIT license.
#
"""Family module for Incubator Wiki."""
from __future__ import annotations

from pywikibot import family


# The Wikimedia Incubator family
class Family(family.WikimediaOrgFamily):

    """Family class for Incubator Wiki."""

    name = 'incubator'

    interwiki_forward = 'wikipedia'
