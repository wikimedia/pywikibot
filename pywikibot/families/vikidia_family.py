# -*- coding: utf-8  -*-
"""Family module for Vikidia."""
__version__ = '$Id$'

from pywikibot import family


class Family(family.Family):

    """Family class for Vikidia."""

    name = 'vikidia'

    langs = {
        'en': 'en.vikidia.org',
        'es': 'es.vikidia.org',
        'fr': 'fr.vikidia.org',
        'it': 'it.vikidia.org',
        'ru': 'ru.vikidia.org',
    }

    def protocol(self, code):
        """Return https as the protocol for this family."""
        return "https"

    def ignore_certificate_error(self, code):
        """Ignore certificate errors."""
        return True  # has self-signed certificate for a different domain.
