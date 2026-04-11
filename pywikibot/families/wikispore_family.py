#
# (C) Pywikibot team, 2020-2026
#
# Distributed under the terms of the MIT license.
#
"""Family module for Wikispore.

.. version-added:: 4.1
"""
from __future__ import annotations

from pywikibot import family


class Family(family.Family):

    """Family class for Wikispore.

    .. version-added:: 4.1
    """

    name = 'wikispore'
    langs = {
        'en': 'wikispore.wmflabs.org',
        'test': 'wikispore-test.wmflabs.org',
    }
