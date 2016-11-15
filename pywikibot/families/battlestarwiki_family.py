# -*- coding: utf-8 -*-
"""Family module for Battlestar Wiki."""
#
# (C) Pywikibot team, 2007-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The Battlestar Wiki family, a set of Battlestar wikis.
class Family(family.SubdomainFamily):

    """Family class for Battlestar Wiki."""

    name = 'battlestarwiki'
    domain = 'battlestarwiki.org'

    codes = ['en', 'de']

    interwiki_removals = ['fr', 'zh', 'es', 'ms', 'tr', 'simple']
