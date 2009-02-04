# -*- coding: utf-8  -*-
import urllib
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wikisource

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikisource'

        self.languages_by_size = [
            'en', 'fr', 'es', 'zh', 'de', 'it', 'pt', 'ru', 'th', 'pl',
            'ro', 'te', 'hr', 'he', 'cs', 'tr', 'fi', 'nl', 'hu', 'sr',
            'sv', 'ar', 'la', 'ml', 'is', 'ja', 'bs', 'uk', 'el', 'ca',
            'ko', 'sl', 'bn', 'hy', 'no', 'da', 'id', 'ta', 'az', 'mk',
            'kn', 'bg', 'fa', 'vi', 'sk', 'cy', 'et', 'lt', 'gl', 'zh-min-nan',
            'yi', 'ht', 'fo', 'ang', 'li',
        ]

        self.langs = {
            '-': 'wikisource.org',
        }
        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikisource.org' % lang

        self.alphabetic = ['ang','ar','az','bg','bs','ca','cs','cy',
                      'da','de','el','en','es','et','fa','fi',
                      'fo','fr','gl','he','hr','ht','hu','id',
                      'is','it','ja', 'ko','la','lt','ml','nl',
                      'no','pl','pt','ro','ru','sk','sl','sr',
                      'sv','te','th','tr','uk','vi','yi','zh']

        self.obsolete = {
            'ang': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Old_English_Wikisource
            
            
            'dk': 'da',
            'ht': None, # http://meta.wikimedia.org/wiki/Proposals_for_closing_projects/Closure_of_Haitian_Creole_Wikisource
            'jp': 'ja',
            'minnan':'zh-min-nan',
            'nb': 'no',
            'tokipona': None,
            'zh-tw': 'zh',
            'zh-cn': 'zh'
        }

        self.interwiki_putfirst = {
            'en': self.alphabetic,
            'fi': self.alphabetic,
            'fr': self.alphabetic,
            'he': ['en'],
            'hu': ['en'],
            'pl': self.alphabetic,
            'simple': self.alphabetic
        }

    def version(self, code):
        return '1.15alpha'

    def shared_image_repository(self, code):
        return ('commons', 'commons')

