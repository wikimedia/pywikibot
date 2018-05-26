# -*- coding: utf-8 -*-
"""Family module for Wikimania wikis."""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family


# The Wikimania family
class Family(family.WikimediaFamily):

    """Family class for Wikimania wikis."""

    name = 'wikimania'

    closed_wikis = [
        '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
        '2014', '2015', '2016', '2017'
    ]

    langs = {
        '2018': 'wikimania2018.wikimedia.org'
    }

    interwiki_forward = 'wikipedia'
