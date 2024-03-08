"""Family module for Wikifunction.

.. versionadded:: 8.4
"""
#
# (C) Pywikibot team, 2023
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family


class Family(family.SingleSiteFamily, family.WikimediaFamily):

    """Family class for Wikifunctions."""

    name = 'wikifunctions'
    domain = 'www.wikifunctions.org'
