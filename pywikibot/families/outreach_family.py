"""Family module for Wikimedia outreach wiki."""
#
# (C) Pywikibot team, 2014-2023
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family


# Outreach wiki custom family
class Family(family.WikimediaOrgFamily):

    """Family class for Wikimedia outreach wiki."""

    name = 'outreach'

    interwiki_forward = 'wikipedia'
