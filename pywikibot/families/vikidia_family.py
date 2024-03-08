"""Family module for Vikidia."""
#
# (C) Pywikibot team, 2010-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family
from pywikibot.tools import classproperty


class Family(family.SubdomainFamily):

    """Family class for Vikidia."""

    name = 'vikidia'
    domain = 'vikidia.org'

    codes = {
        'ar', 'ca', 'de', 'el', 'en', 'es', 'eu', 'fr', 'hy', 'it', 'nl', 'oc',
        'pt', 'ru', 'scn',
    }

    # Sites we want to edit but not count as real languages
    test_codes = ['central', 'test']

    @classproperty
    def domains(cls):
        """List of domains used by Vikidia family."""
        return [
            cls.domain,
            'wikikids.nl'  # nl
        ]

    @classproperty
    def langs(cls):
        """Property listing family languages."""
        cls.langs = super().langs
        cls.langs['nl'] = cls.domains[1]
        return cls.langs

    def scriptpath(self, code):
        """Return the script path for this family."""
        if code == 'nl':
            return ''
        return super().scriptpath(code)
