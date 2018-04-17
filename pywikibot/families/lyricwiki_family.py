# -*- coding: utf-8 -*-
"""Family module for LyricWiki."""
#
# (C) Pywikibot team, 2007-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family


# The LyricWiki family

# user-config.py:
# usernames['lyricwiki']['en'] = 'user'
class Family(family.SingleSiteFamily, family.WikiaFamily):

    """Family class for LyricWiki."""

    name = 'lyricwiki'
    code = 'en'
    domain = 'lyrics.wikia.com'
