"""Family module for Lingua Libre.

.. versionaddded: 6.5
"""
#
# (C) Pywikibot team, 2021-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


class Family(family.WikimediaFamily):

    """Family class for Lingua Libre.

    .. versionaddded: 6.5
    """

    name = 'lingualibre'

    langs = {
        'lingualibre': 'lingualibre.org'
    }

    interwiki_forward = 'wikipedia'

    def scriptpath(self, code) -> str:
        """Return the script path for this family."""
        return ''

    def interface(self, code) -> str:
        """Return 'DataSite'."""
        return 'DataSite'
