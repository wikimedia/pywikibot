"""Family module for Foundation wiki.

.. versionadded:: 3.0
"""
#
# (C) Pywikibot team, 2019-2022
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family


class Family(family.WikimediaFamily, family.SingleSiteFamily):

    """Family class for Foundation wiki.

    .. versionadded:: 3.0
    """

    name = 'foundation'
    domain = 'foundation.wikimedia.org'

    interwiki_forward = 'wmf'
