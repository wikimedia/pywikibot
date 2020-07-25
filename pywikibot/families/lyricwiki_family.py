# -*- coding: utf-8 -*-
"""Family module for LyricWiki."""
#
# (C) Pywikibot team, 2007-2020
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


# The LyricWiki family

# user-config.py:
# usernames['lyricwiki']['en'] = 'user'
class Family(family.FandomFamily):

    """Family class for LyricWiki."""

    name = 'lyricwiki'
    domain = 'lyrics.fandom.com'
    codes = ('en', 'ru')
