# -*- coding: utf-8  -*-

import family

# Bot wiki - the (semi-)official pywikipedia wiki

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)

        self.name = 'botwiki'

        self.langs = {
                'botwiki': 'botwiki.sno.cc',
        }
        self.namespaces[4] = {
            'botwiki': [u'Botwiki'],
        }
        self.namespaces[5] = {
            'botwiki': [u'Botwiki talk'],
        }
        self.namespaces[100] = {
            'botwiki': [u'Manual'],
        }
        self.namespaces[101] = {
            'botwiki': [u'Manual talk'],
        }
        self.namespaces[102] = {
            'botwiki': [u'Python'],
        }
        self.namespaces[103] = {
            'botwiki': [u'Python talk'],
        }
        self.namespaces[104] = {
            'botwiki': [u'Php'],
        }
        self.namespaces[105] = {
            'botwiki': [u'Php talk'],
        }
        self.namespaces[106] = {
            'botwiki': [u'Perl'],
        }
        self.namespaces[107] = {
            'botwiki': [u'Perl talk'],
        }
        self.namespaces[108] = {
            'botwiki': [u'AWB'],
        }
        self.namespaces[109] = {
            'botwiki': [u'AWB talk'],
        }
        self.namespaces[110] = {
            'botwiki': [u'IRC'],
        }
        self.namespaces[111] = {
            'botwiki': [u'IRC talk'],
        }
        self.namespaces[112] = {
            'botwiki': [u'Other'],
        }
        self.namespaces[113] = {
            'botwiki': [u'Other talk'],
        }

    def version(self, code):
        return "1.11.0"
