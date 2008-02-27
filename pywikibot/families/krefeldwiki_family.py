# -*- coding: utf-8  -*-

from pywikibot import family

# The city wiki of Krefeld, Germany, Europe.

class Family(family.Family):

    def __init__(self):
        family.Family.__init__(self)
        self.name = 'krefeldwiki'

        self.langs = {
            'de': 'krefeldwiki.de',
        }

        self.namespaces[4] = {
            '_default': [u'Krefeld Wiki', self.namespaces[4]['_default']],
        }

        self.namespaces[5] = {
            '_default': [u'Krefeld Wiki Diskussion', self.namespaces[5]['_default']],
        }

        self.namespaces[106] = {
            '_default': [u'Formular', 'Form'],
        }

        self.namespaces[107] = {
            '_default': [u'Formular Diskussion', 'Form talk'],
        }

        self.namespaces[110] = {
            '_default': [u'Relation', 'Relation'],
        }

        self.namespaces[111] = {
            '_default': [u'Relation Diskussion', 'Relation talk'],
        }

        self.namespaces[112] = {
            '_default': [u'Attribut', 'Attribut'],
        }

        self.namespaces[113] = {
            '_default': [u'Attribut Diskussion', 'Attribut talk'],
        }

        self.namespaces[114] = {
            '_default': [u'Datentyp', 'Data type'],
        }

        self.namespaces[115] = {
            '_default': [u'Datentyp Diskussion', 'Data type talk'],
        }

    def version(self, code):
        return "1.10.1"

    def scriptpath(self, code):
        return '/w'

    def path(self, code):
        return '%s/index.php5' % self.scriptpath(code)
