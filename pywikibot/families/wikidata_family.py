# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family

# The wikidata family


class Family(family.WikimediaFamily):
    def __init__(self):
        super(Family, self).__init__()
        self.name = 'wikidata'
        self.langs = {
            'wikidata': 'www.wikidata.org',
            'repo': 'wikidata-test-repo.wikimedia.de',
            'client': 'wikidata-test-client.wikimedia.de',
            'test': 'test.wikidata.org',
        }

    def shared_data_repository(self, code, transcluded=False):
        """Always return a repository tupe. This enables testing whether
        the site opject is the repository itself, see Site.is_data_repository()

        """
        if transcluded:
            return (None, None)
        else:
            if code == 'wikidata':
                return ('wikidata', 'wikidata')
            elif code == 'test':
                return ('test', 'wikidata')
            else:
                return ('repo', 'wikidata')

    def globes(self, code):
        """Supported globes for Coordinate datatype"""
        return {'earth': 'http://www.wikidata.org/entity/Q2'}
