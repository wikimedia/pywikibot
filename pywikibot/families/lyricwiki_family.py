# -*- coding: utf-8  -*-
"""Family module for LyricWiki."""
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import family


# The LyricWiki family

# user_config.py:
# usernames['lyricwiki']['en'] = 'user'
class Family(family.SingleSiteFamily, family.WikiaFamily):

    """Family class for LyricWiki."""

    name = 'lyricwiki'
    code = 'en'
    domain = 'lyrics.wikia.com'
