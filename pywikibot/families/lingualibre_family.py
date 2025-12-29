"""Family module for Lingua Libre.

.. versionadded:: 6.5
"""
#
# (C) Pywikibot team, 2021-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family


class Family(family.WikimediaFamily, family.WikibaseFamily):

    """Family class for Lingua Libre.

    .. versionadded:: 6.5
    """

    name = 'lingualibre'

    langs = {
        'lingualibre': 'lingualibre.org'
    }

    interwiki_forward = 'wikipedia'

    def scriptpath(self, code) -> str:
        """Return the script path for this family."""
        return ''
