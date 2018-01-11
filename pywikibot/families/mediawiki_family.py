# -*- coding: utf-8 -*-
"""Family module for MediaWiki wiki."""
#
# (C) Pywikibot team, 2006-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family


# The MediaWiki family
class Family(family.WikimediaFamily, family.SingleSiteFamily):

    """Family module for MediaWiki wiki."""

    name = 'mediawiki'
    domain = 'www.mediawiki.org'
