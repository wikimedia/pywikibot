#
# (C) Pywikibot team, 2023-2026
#
# Distributed under the terms of the MIT license.
#
"""Family module for Wikifunctions.

.. version-added:: 8.4
"""
from __future__ import annotations

from pywikibot import family


class Family(family.SingleSiteFamily, family.WikimediaFamily):

    """Family class for Wikifunctions."""

    name = 'wikifunctions'
    domain = 'www.wikifunctions.org'
