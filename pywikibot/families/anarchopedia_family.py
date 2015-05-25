# -*- coding: utf-8  -*-
"""Family module for Anarchopedia wiki."""
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot import family
from pywikibot.tools import deprecated


# The Anarchopedia family
class Family(family.Family):

    """Family class for Anarchopedia wiki."""

    interwiki_replacements = {
        # ISO 639-2 -> ISO 639-1 mappings
        'ara': 'ar',
        'chi': 'zh',
        'dan': 'da',
        'deu': 'de',
        'dut': 'nl',
        'ell': 'el',
        'eng': 'en',
        'epo': 'eo',
        'fas': 'fa',
        'fin': 'fi',
        'fra': 'fr',
        'ger': 'de',
        'gre': 'el',
        'heb': 'he',
        'hye': 'hy',
        'ind': 'id',
        'ita': 'it',
        'jpn': 'ja',
        'kor': 'ko',
        'lav': 'lv',
        'lit': 'lt',
        'nno': 'no',
        'nob': 'no',
        'nor': 'no',
        'pol': 'pl',
        'por': 'pt',
        'rum': 'ro',
        'rus': 'ru',
        'spa': 'es',
        'srp': 'sr',
        'sqi': 'sq',
        'swe': 'sv',
        'tur': 'tr',
        'zho': 'zh',

        # ISO 639-1 -> ISO 639-1 mappings
        'bs': 'hr',

        # Non-compliant mappings
        'bos': 'hr',
        'nsh': 'hr',
    }

    def __init__(self):
        """Constructor."""
        family.Family.__init__(self)
        self.name = 'anarchopedia'

        self.languages_by_size = [
            'ar', 'en', 'de', 'nl', 'el', 'it', 'fa', 'fi', 'fr', 'he', 'es',
            'hy', 'id', 'meta', 'ja', 'ko', 'lv', 'lt', 'no', 'hr', 'pl', 'pt',
            'ro', 'ru', 'hrv', 'sq', 'sr', 'sv', 'tr', 'zh', 'eo', 'da',
        ]
        for l in self.languages_by_size:
            self.langs[l] = '%s.anarchopedia.org' % l

        self.nocapitalize = list(self.langs.keys())

    @deprecated('APISite.version()')
    def version(self, code):
        """Return the version for this family."""
        return "1.14alpha"

    def scriptpath(self, code):
        """Return the script path for this family."""
        return ''

    def path(self, code):
        """Return the path to index.php for this family."""
        return '/index.php'

    def apipath(self, code):
        """Return the path to api.php for this family."""
        return '/api.php'
