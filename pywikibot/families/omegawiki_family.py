# -*- coding: utf-8  -*-
"""Family module for Omega Wiki."""
__version__ = '$Id$'

from pywikibot import family


# Omegawiki, the Ultimate online dictionary
class Family(family.Family):

    """Family class for Omega Wiki."""

    def __init__(self):
        """Constructor."""
        family.Family.__init__(self)
        self.name = 'omegawiki'
        self.langs['omegawiki'] = 'www.omegawiki.org'

        # On most Wikipedias page names must start with a capital letter, but some
        # languages don't use this.

        self.nocapitalize = list(self.langs.keys())

    def hostname(self, code):
        """Return the hostname for this family."""
        return 'www.omegawiki.org'

    def version(self, code):
        """Return the version for this family."""
        return "1.22.6"

    def scriptpath(self, code):
        """Return the script path for this family."""
        return ''

    def path(self, code):
        """Return the path to index.php for this family."""
        return '/index.php'

    def apipath(self, code):
        """Return the path to api.php for this family."""
        return '/api.php'

    def protocol(self, code):
        """Return https as the protocol for this family."""
        return "https"

    def ignore_certificate_error(self, code):
        """Ignore certificate errors."""
        return True  # has an expired certificate.
