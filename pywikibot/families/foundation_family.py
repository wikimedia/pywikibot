"""Family module for Foundation wiki.

.. versionadded 3.0
"""
#
# (C) Pywikibot team, 2019-2021
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


class Family(family.WikimediaFamily, family.SingleSiteFamily):

    """Family class for Foundation wiki.

    .. versionadded 3.0
    """

    name = 'foundation'
    domain = 'foundation.wikimedia.org'

    interwiki_forward = 'wmf'
