"""Family module for Wikimedia species wiki."""
#
# (C) Pywikibot team, 2007-2021
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The Wikispecies family
class Family(family.WikimediaOrgFamily):

    """Family class for Wikimedia species wiki."""

    name = 'species'

    interwiki_forward = 'wikipedia'
