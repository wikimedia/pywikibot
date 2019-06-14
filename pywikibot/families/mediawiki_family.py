# -*- coding: utf-8 -*-
"""Family module for MediaWiki wiki."""
#
# (C) Pywikibot team, 2006-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family


# The MediaWiki family
class Family(family.WikimediaFamily, family.SingleSiteFamily):

    """Family class for MediaWiki wiki."""

    name = 'mediawiki'
    domain = 'www.mediawiki.org'

    interwiki_forward = 'wikipedia'
