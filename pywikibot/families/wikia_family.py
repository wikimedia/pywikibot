# -*- coding: utf-8  -*-
"""Family module for Wikia."""
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot import family
from pywikibot.tools import deprecated


# The Wikia Search family
# user-config.py: usernames['wikia']['wikia'] = 'User name'
class Family(family.Family):

    """Family class for Wikia."""

    def __init__(self):
        """Constructor."""
        family.Family.__init__(self)
        self.name = u'wikia'

        self.langs = {
            'wikia': 'www.wikia.com',
        }

    def hostname(self, code):
        """Return the hostname for every site in this family."""
        return u'www.wikia.com'

    @deprecated('APISite.version()')
    def version(self, code):
        """Return the version for this family."""
        return "1.19.20"

    def scriptpath(self, code):
        """Return the script path for this family."""
        return ''

    def apipath(self, code):
        """Return the path to api.php for this family."""
        return '/api.php'
