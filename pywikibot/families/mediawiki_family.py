"""Family module for MediaWiki wiki."""
#
# (C) Pywikibot team, 2006-2020
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The MediaWiki family
class Family(family.WikimediaFamily, family.SingleSiteFamily):

    """Family class for MediaWiki wiki."""

    name = 'mediawiki'
    domain = 'www.mediawiki.org'

    interwiki_forward = 'wikipedia'
