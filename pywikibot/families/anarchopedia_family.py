# -*- coding: utf-8  -*-
"""Family module for Anarchopedia wiki."""

__version__ = '$Id$'

from pywikibot import family
from pywikibot.tools import deprecated


# The Anarchopedia family
class Family(family.Family):

    """Family class for Anarchopedia wiki."""

    def __init__(self):
        """Constructor."""
        family.Family.__init__(self)
        self.name = 'anarchopedia'

        self.languages_by_size = [
            'ar', 'en', 'ger', 'de', 'nl', 'el', 'it', 'fa', 'fi', 'fr', 'he',
            'es', 'hy', 'id', 'meta', 'ja', 'ko', 'lv', 'lit', 'no', 'hrv',
            'pl', 'pt', 'ro', 'ru', 'sr', 'sq', 'da', 'sv', 'tr', 'zh', 'gre',
            'chi',
        ]
        for l in self.languages_by_size:
            self.langs[l] = '%s.anarchopedia.org' % l

        self.nocapitalize = list(self.langs.keys())

        self.obsolete = {
            'ara': 'ar',
            'bos': 'bs',
            'zho': 'zh',
            'dan': 'da',
            'deu': 'de',
            'dut': 'nl',
            'ell': 'el',
            'eng': 'en',
            'epo': 'eo',
            'fas': 'fa',
            'fra': 'fr',
            'fin': 'fi',
            'heb': 'he',
            'ind': 'id',
            'ita': 'it',
            'jpn': 'ja',
            'lit': 'lt',
            'lav': 'lv',
            'nor': 'no',
            'nsh': 'sh',
            'pol': 'pl',
            'por': 'pt',
            'rum': 'ro',
            'rus': 'ru',
            'spa': 'es',
            'srp': 'sr',
            'srp': 'hr',
            'swe': 'sv',
            'kor': 'ko',
            'sqi': 'sq',
            'hye': 'hy',
            'tur': 'tr',

            'ell': 'gre',
            'srp': 'hrv',
            'nno': None,
            'nob': None,
        }

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
