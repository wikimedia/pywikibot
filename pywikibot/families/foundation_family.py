"""Family module for Foundation wiki.

.. version-added:: 3.0
"""
#
# (C) Pywikibot team, 2019-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family


class Family(family.WikimediaFamily, family.SingleSiteFamily):

    """Family class for Foundation wiki.

    .. version-added:: 3.0
    """

    name = 'foundation'
    domain = 'foundation.wikimedia.org'

    interwiki_forward = 'wmf'
