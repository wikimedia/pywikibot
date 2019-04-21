# -*- coding: utf-8 -*-
"""Family module for LyricWiki."""
#
# (C) Pywikibot team, 2007-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family
from pywikibot.tools import classproperty, deprecated


# The LyricWiki family

# user-config.py:
# usernames['lyricwiki']['en'] = 'user'
class Family(family.SubdomainFamily, family.FandomFamily):

    """Family class for LyricWiki."""

    name = 'lyricwiki'
    domain = 'lyrics.fandom.com'
    codes = ('en', 'ru')

    @deprecated('APISite.version()', since='20141225')
    def version(self, code):
        return '1.19.24'

    def protocol(self, code):
        """Return 'https' as the protocol."""
        return 'https'

    @classproperty
    def langs(cls):
        """Property listing family languages."""
        return {code: cls.domain for code in cls.codes}
