"""Family module for Lingua Libre."""
#
# (C) Pywikibot team, 2021
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The Lingua Libre family
class Family(family.WikimediaFamily):

    """Family class for Lingua Libre."""

    name = 'lingualibre'

    langs = {
        'lingualibre': 'lingualibre.org'
    }

    interwiki_forward = 'wikipedia'

    def scriptpath(self, code):
        """Return the script path for this family."""
        return ''
