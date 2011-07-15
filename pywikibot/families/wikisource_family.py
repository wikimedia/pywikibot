# -*- coding: utf-8  -*-
from pywikibot import family

__version__ = '$Id$'

# The Wikimedia family that is known as Wikisource

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikisource'

        self.languages_by_size = [
            'en', 'ru', 'zh', 'pt', 'de', 'fr', 'it', 'es', 'he', 'ar', 'fa',
            'hu', 'pl', 'cs', 'th', 'ro', 'ko', 'hr', 'te', 'fi', 'sv', 'sl',
            'bn', 'vi', 'nl', 'tr', 'uk', 'ja', 'sr', 'el', 'ml', 'la', 'az',
            'br', 'li', 'yi', 'sa', 'mk', 'hy', 'is', 'vec', 'ta', 'ca', 'bs',
            'id', 'da', 'eo', 'no', 'et', 'bg', 'sah', 'lt', 'gl', 'kn', 'cy',
            'sk', 'zh-min-nan', 'fo',
        ]

        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikisource.org' % lang
        self.langs['-'] = 'wikisource.org'

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
        # Global bot allowed languages on http://meta.wikimedia.org/wiki/Bot_policy/Implementation#Current_implementation
        self.cross_allowed = [
            'el','fa','it','ko','no','vi','zh'
        ]
        # CentralAuth cross avaliable projects.
        self.cross_projects = [
            'wikipedia', 'wiktionary', 'wikibooks', 'wikiquote', 'wikinews', 'wikiversity',
            'meta', 'mediawiki', 'test', 'incubator', 'commons', 'species'
        ]

        self.authornamespaces = {
            '_default': [0],
            'ar': [102],
            'bg': [100],
            'cs': [100],
            'da': [102],
            'en': [102],
            'fa': [102],
            'fr': [102],
            'hr': [100],
            'hu': [100],
            'hy': [100],
            'it': [102],
            'ko': [100],
            'la': [102],
            'nl': [102],
            'no': [102],
            'pl': [104],
            'pt': [102],
            'sv': [106],
            'tr': [100],
            'vi': [102],
            'zh': [102],
            }

        self.crossnamespace[0] = {
            '_default': self.authornamespaces,
        }
        self.crossnamespace[100] = {
            'bg': self.authornamespaces,
            'cs': self.authornamespaces,
            'hr': self.authornamespaces,
            'hu': self.authornamespaces,
            'hy': self.authornamespaces,
            'ko': self.authornamespaces,
            'tr': self.authornamespaces,
        }

        self.crossnamespace[102] = {
            'ar': self.authornamespaces,
            'da': self.authornamespaces,
            'en': self.authornamespaces,
            'fa': self.authornamespaces,
            'fr': self.authornamespaces,
            'it': self.authornamespaces,
            'la': self.authornamespaces,
            'nl': self.authornamespaces,
            'no': self.authornamespaces,
            'pt': self.authornamespaces,
            'vi': self.authornamespaces,
            'zh': self.authornamespaces,
        }

        self.crossnamespace[104] = {
            'pl': self.authornamespaces,
        }

        self.crossnamespace[106] = {
            'sv': self.authornamespaces,
        }

    def version(self, code):
        return '1.17wmf1'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
