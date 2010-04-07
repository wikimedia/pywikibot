# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The meta wikimedia family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'meta'
        self.langs = {
            'meta': 'meta.wikimedia.org',
        }
        self.interwiki_forward = 'wikipedia'
        self.cross_allowed = ['meta',]
        self.cross_projects = [
            'wikipedia', 'wiktionary', 'wikibooks', 'wikiquote', 'wikisource', 'wikinews', 'wikiversity',
            'mediawiki', 'test', 'incubator', 'commons', 'species',
        ]

    def version(self,code):
        return '1.16-wmf'

    def shared_image_repository(self, code):
        return ('commons', 'commons')

    def ssl_pathprefix(self, code):
        return "/wikipedia/meta"
