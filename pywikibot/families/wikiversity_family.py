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
            'en', 'fr', 'es', 'de', 'it', 'el', 'cs', 'ja', 'pt',
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
            'cs': u'Wikiverzita',
            'el': u'Βικιεπιστήμιο',
            'es': u'Wikiversidad',
            'fr': u'Wikiversité',
            'it': u'Wikiversità',
            'pt': u'Wikiversidade',
        }
        self.namespaces[5] = {
            '_default': [u'Wikiversity talk', self.namespaces[5]['_default']],
            'cs': u'Wikiverzita diskuse',
            'de': u'Wikiversity Diskussion',
            'el': u'Συζήτηση Βικιεπιστημίου',
            'es': u'Wikiversidad Discusión',
            'fr': u'Discussion Wikiversité',
            'it': u'Discussioni Wikiversità',
            'ja': u'Wikiversity‐ノート',
            'pt': u'Wikiversidade Discussão',
        }

        self.namespaces[100] = {
            'el': u'Σχολή',
            'en': u'School',
            'it': u'Facoltà',
            'ja': u'School',
        }
        self.namespaces[101] = {
            'el': u'Συζήτηση Σχολής',
            'en': u'School talk',
            'it': u'Discussioni facoltà',
            'ja': u'School‐ノート',
        }
        self.namespaces[102] = {
            'el': u'Τμήμα',
            'en': u'Portal',
            'fr': u'Projet',
            'it': u'Corso',
            'ja': u'Portal',
        }
        self.namespaces[103] = {
            'el': u'Συζήτηση Τμήματος',
            'en': u'Portal talk',
            'fr': u'Discussion Projet',
            'it': u'Discussioni corso',
            'ja': u'Portal‐ノート',
        }
        self.namespaces[104] = {
            'en': u'Topic',
            'it': u'Materia',
            'ja': u'Topic',
        }
        self.namespaces[105] = {
            'en': u'Topic talk',
            'it': u'Discussioni materia',
            'ja': u'Topic‐ノート',
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
