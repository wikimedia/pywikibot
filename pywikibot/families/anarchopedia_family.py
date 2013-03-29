# -*- coding: utf-8  -*-
__version__ = '$Id$'

from pywikibot import family

# The Anarchopedia family

class Family(family.Family):
    def __init__(self):
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

        self.nocapitalize = self.langs.keys()

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

    def version(self, code):
        return "1.14alpha"

    def scriptpath(self, code):
        return ''

    def path(self, code):
        return '/index.php'

    def apipath(self, code):
        return '/api.php'
