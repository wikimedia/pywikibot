# -*- coding: utf-8  -*-

__version__ = '$Id$'

import family

# The project wiki of Freeciv, an open source strategy game.

class Family(family.Family):

    def __init__(self):
        family.Family.__init__(self)
        self.name = 'freeciv'
        self.langs = {
            'ca': 'ca.freeciv.wikia.com',
            'da': 'da.freeciv.wikia.com',
            'de': 'de.freeciv.wikia.com',
            'en': 'freeciv.wikia.com',
            'es': 'es.freeciv.wikia.com',
            'fi': 'fi.freeciv.wikia.com',
            'fr': 'fr.freeciv.wikia.com',
            'ja': 'ja.freeciv.wikia.com',
            'ru': 'ru.freeciv.wikia.com',
        }

    def scriptpath(self, code):
        return ''

    def version(self, code):
        return "1.16.2"
