# -*- coding: utf-8  -*-
"""Family module for Battlestar Wiki."""

__version__ = '$Id$'

from pywikibot import family


# The Battlestar Wiki family, a set of Battlestar wikis.
# http://battlestarwiki.org/
class Family(family.Family):

    """Family class for Battlestar Wiki."""

    def __init__(self):
        """Constructor."""
        family.Family.__init__(self)
        self.name = 'battlestarwiki'

        self.languages_by_size = ['en', 'de', 'fr', 'zh', 'es', 'ms', 'tr', 'simple']

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.battlestarwiki.org' % lang

    def hostname(self, code):
        """Return the hostname for a site in this family."""
        return '%s.battlestarwiki.org' % code

    def version(self, code):
        """Return the version for this family."""
        return "1.16.4"
