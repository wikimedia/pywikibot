"""Family module for Abstract Wikipedia.

.. version-added:: 11.2
"""
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family


class Family(family.SingleSiteFamily, family.WikimediaFamily):

    """Family class for Abstract Wikipedia."""

    name = 'abstract'
    domain = 'abstract.wikipedia.org'
