# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The test wikidata family
class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikidata'
        self.langs = {
            'repo': 'wikidata-test-repo.wikimedia.de',
            'client': 'wikidata-test-client.wikimedia.de',
        }
