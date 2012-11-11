# -*- coding: utf-8 -*-
from pywikibot import family

__version__ = '$Id$'

#Family file for the original wikivoyage

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'oldwikivoyage'
        self.langs = {
            'de': u'www.wikivoyage-old.org',
            'en': u'en.wikivoyage-old.org',
            'fr': u'fr.wikivoyage-old.org',
            'it': u'www.wikivoyage-old.org',
            'nl': u'nl.wikivoyage-old.org',
            'ru': u'ru.wikivoyage-old.org',
            'shared': u'www.wikivoyage-old.org',
            'sv': u'sv.wikivoyage-old.org',
            'wts': u'wts.wikivoyage-old.org',
        }

    def scriptpath(self, code):
        return {
            'de': u'/w/de',
            'en': u'/w',
            'fr': u'/w',
            'it': u'/w/it',
            'nl': u'/w',
            'ru': u'/w',
            'shared': u'/w/shared',
            'sv': u'/w',
            'wts': u'/w',
        }[code]

    def version(self, code):
        return {
            'de': u'1.13.1',
            'en': u'1.19.1',
            'fr': u'1.19.1',
            'it': u'1.13.1',
            'nl': u'1.19.1',
            'ru': u'1.19.1',
            'sv': u'1.19.1',
            'shared': u'1.13.1',
            'wts': u'1.19.1',
        }[code]

    def shared_image_repository(self, code):
        return ('shared', 'oldwikivoyage')
