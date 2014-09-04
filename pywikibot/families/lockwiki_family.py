# -*- coding: utf-8  -*-
"""Family module for Lock Wiki."""

__version__ = '$Id$'

from pywikibot import family


# The locksmithwiki family
class Family(family.Family):

    """Family class for Lock Wiki."""

    def __init__(self):
        """Constructor."""
        family.Family.__init__(self)
        self.name = 'lockwiki'
        self.langs = {
            'en': 'www.locksmithwiki.com',
        }

    def scriptpath(self, code):
        """Return the script path for this family."""
        return '/lockwiki'

    def version(self, code):
        """Return the version for this family."""
        return '1.15.1'

    def nicepath(self, code):
        """Return the nice article path for this family."""
        return "%s/" % self.path(self, code)
