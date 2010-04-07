# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The Wikimedia Commons family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'commons'
        self.langs = {
            'commons': 'commons.wikimedia.org',
        }

        self.interwiki_forward = 'wikipedia'

        self.category_redirect_templates = {
            'commons': (u'Category redirect',
                        u'Categoryredirect',
                        u'See cat',
                        u'Seecat',
                        u'Catredirect',
                        u'Cat redirect',
                        u'CatRed',
                        u'Cat-red',
                        u'Catredir',
                        u'Redirect category'),
        }

        self.disambiguationTemplates = {
            'commons': [u'Disambig', u'Disambiguation', u'Razločitev',
                        u'Begriffsklärung']
        }

        self.disambcatname = {
            'commons':  u'Disambiguation'
        }
        self.cross_projects = [
            'wikipedia', 'wiktionary', 'wikibooks', 'wikiquote', 'wikisource', 'wikinews', 'wikiversity',
            'meta', 'mediawiki', 'test', 'incubator', 'species',
        ]


    def version(self, code):
        return '1.16wmf3'

    def dbName(self, code):
        return 'commonswiki_p'

    def shared_image_repository(self, code):
        return ('commons', 'commons')

    def ssl_pathprefix(self, code):
        return "/wikipedia/commons"

