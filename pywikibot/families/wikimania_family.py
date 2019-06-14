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

    codes = ['wikimania']

    code_aliases = {'2019': 'wikimania'}

    interwiki_forward = 'wikipedia'

    @classproperty
    def langs(cls):
        """Property listing family languages."""
        codes = cls.codes + cls.closed_wikis

        # shortcut this classproperty
        cls.langs = {code: '{}{}.{}'.format(cls.name, code, cls.domain)
                     for code in codes if code != 'wikimania'}
        cls.langs['wikimania'] = 'wikimania.{}'.format(cls.domain)
        return cls.langs
