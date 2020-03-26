# -*- coding: utf-8 -*-
"""Family module for Wikimania wikis."""
#
# (C) Pywikibot team, 2017-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family
from pywikibot.tools import classproperty


# The Wikimania family
class Family(family.SubdomainFamily, family.WikimediaFamily):

    """Family class for Wikimania wikis."""

    name = 'wikimania'

    closed_wikis = [
        '2005', '2006', '2007', '2008', '2009', '2010', '2011', '2012', '2013',
        '2014', '2015', '2016', '2017', '2018'
    ]

    codes = ['wikimania', 'team']

    code_aliases = {'2019': 'wikimania'}

    interwiki_forward = 'wikipedia'

    @classproperty
    def langs(cls):
        """Property listing family languages."""
        cls.langs = super(Family, cls).langs
        for lang, url in cls.langs.items():
            if not url.startswith(cls.name):
                cls.langs[lang] = cls.name + url
        return cls.langs
