# -*- coding: utf-8  -*-
import urllib
from pywikibot import family
import config

__version__ = '$Id$'

# The Wikimedia family that is known as Wikiversity

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wikiversity'

        self.languages_by_size = [
            'en', 'fr', 'es', 'de', 'it', 'el',
        ]

        self.langs = {
            'beta': 'beta.wikiversity.org',
        }
        for lang in self.languages_by_size:
            self.langs[lang] = '%s.wikiversity.org' % lang

        # Most namespaces are inherited from family.Family.
        # Translation used on all wikis for the different namespaces.
        # (Please sort languages alphabetically)
        # You only need to enter translations that differ from _default.
        self.namespaces[4] = {
            '_default': [u'Wikiversity', self.namespaces[4]['_default']],
            'el': u'Βικιεπιστήμιο',
            'es': u'Wikiversidad',
            'fr': u'Wikiversité',
            'it': u'Wikiversità',
        }
        self.namespaces[5] = {
            '_default': [u'Wikiversity talk', self.namespaces[5]['_default']],
            'de': u'Wikiversity Diskussion',
            'el': u'Συζήτηση Βικιεπιστημίου',
            'es': u'Wikiversidad Discusión',
            'fr': u'Discussion Wikiversité',
            'it': u'Discussioni Wikiversità',
        }

        self.namespaces[100] = {
            'el': u'Σχολή',
            'en': u'School',
            'it': u'Facoltà',
        }
        self.namespaces[101] = {
            'el': u'Συζήτηση Σχολής',
            'en': u'School talk',
            'it': u'Discussioni facoltà',
        }
        self.namespaces[102] = {
            'el': u'Τμήμα',
            'en': u'Portal',
            'fr': u'Projet',
            'it': u'Corso',
        }
        self.namespaces[103] = {
            'el': u'Συζήτηση Τμήματος',
            'en': u'Portal talk',
            'fr': u'Discussion Projet',
            'it': u'Discussioni corso',
        }
        self.namespaces[104] = {
            'en': u'Topic',
            'it': u'Materia',
        }
        self.namespaces[105] = {
            'en': u'Topic talk',
            'it': u'Discussioni materia',
        }
        self.namespaces[106] = {
            'de': u'Kurs',
            'fr': u'Faculté',
            'it': u'Dipartimento',
        }
        self.namespaces[107] = {
            'de': u'Kurs Diskussion',
            'fr': u'Discussion Faculté',
            'it': u'Discussioni dipartimento',
        }
        self.namespaces[108] = {
            'de': u'Projekt',
            'fr': u'Département',
        }
        self.namespaces[109] = {
            'de': u'Projekt Diskussion',
            'fr': u'Discussion Département',
        }
        self.namespaces[110] = {
            'fr': u'Transwiki',
        }
        self.namespaces[111] = {
            'fr': u'Discussion Transwiki',
        }

    def version(self,code):
        return '1.13alpha'

    def shared_image_repository(self, code):
        return ('commons', 'commons')
