# -*- coding: utf-8 -*-

__version__ = '$Id$'

# The wikis of Chapters of the Wikimedia Foundation living at a xy.wikimedia.org url

from pywikibot import family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikimediachapter'

        self.countries = [
            'ar', 'bd', 'co', 'dk', 'fi', 'mk', 'mx', 'nl', 'no', 'nyc', 'pl',
            'rs', 'ru', 'se', 'ua', 'uk', 've',
        ]

        self.countrylangs = {
            'ar': 'es', 'bd': 'bn', 'co': 'es', 'dk': 'da', 'fi': 'fi',
            'mk': 'mk', 'mx': 'es', 'nl': 'nl', 'no': 'no', 'nyc': 'en',
            'pl': 'pl', 'rs': 'sr', 'ru': 'ru', 'se': 'sv', 'ua': 'uk',
            'uk': 'en-gb', 've': 'en',
        }

        self.langs = dict([(country, '%s.wikimedia.org' % country)
                           for country in self.countries])

