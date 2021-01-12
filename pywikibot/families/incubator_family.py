"""Family module for Incubator Wiki."""
#
# (C) Pywikibot team, 2006-2020
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The Wikimedia Incubator family
class Family(family.WikimediaOrgFamily):

    """Family class for Incubator Wiki."""

    name = 'incubator'

    interwiki_forward = 'wikipedia'
