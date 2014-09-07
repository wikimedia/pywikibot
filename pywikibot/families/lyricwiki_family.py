# -*- coding: utf-8  -*-
"""Family module for LyricWiki."""

__version__ = '$Id$'

from pywikibot import family


# The LyricWiki family

# user_config.py:
# usernames['lyricwiki']['en'] = 'user'
class Family(family.Family):

    """Family class for LyricWiki."""

    def __init__(self):
        """Constructor."""
        family.Family.__init__(self)
        self.name = 'lyricwiki'
        self.langs = {
            'en': 'lyrics.wikia.com',
        }

    def version(self, code):
        """Return the version for this family."""
        return '1.19.18'

    def scriptpath(self, code):
        """Return the script path for this family."""
        return ''

    def apipath(self, code):
        """Return the path to api.php for this family."""
        return '/api.php'
