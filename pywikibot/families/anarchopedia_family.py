# -*- coding: utf-8  -*-
import family

# The Anarchopedia family

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'anarchopedia'

        langs = [
            'ara', 'bos', 'chi', 'dan', 'deu', 'dut', 'ell', 'eng', 'epo', 'fra',
            'ind', 'ita', 'jpn', 'lit', 'nno', 'nsh', 'nor', 'pol', 'por', 'rum',
            'rus', 'spa', 'srp', 'swe',
        ]
        for lang in langs:
            self.langs[lang] = '%s.anarchopedia.org' % lang

        interface_lang = {
            'ara': 'ar',
            'bos': 'sr',
            'chi': 'zh',
            'dan': 'da',
            'deu': 'de',
            'dut': 'nl',
            'ell': 'el',
            'eng': 'en',
            'epo': 'en',
            'fra': 'fr',
            'hrv': 'sr',
            'ind': 'id',
            'ita': 'it',
            'jpn': 'ja',
            'lit': 'lit',
            'nno': 'nn',
            'nor': 'no',
            'nsh': 'sr',
            'pol': 'pl',
            'por': 'pt',
            'rum': 'ro',
            'rus': 'ru',
            'spa': 'es',
            'srp': 'sr',
            'swe': 'sv',
        }
        copy = [-2, -1, 1, 2, 3, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
        for code, interface in interface_lang.items():
            for ns in copy:
                if self.namespaces[ns].has_key(interface):
                    self.namespaces[ns][code] = self.namespaces[ns][interface]

        self.namespaces[4] = {
            '_default': [u'Anarchopedia', self.namespaces[4]['_default']],
            'ara': u'أنارشوبيديا',
            'chi': u'安那其百科',
            'ell': u'Αναρχοπαίδεια',
            'jpn': u'アナーキォペディア',
            'rum': u'Anarhopedia',
        }
        self.namespaces[5] = {
            '_default': [u'Anarchopedia talk', self.namespaces[5]['_default']],
            'ara': u'نقاش أنارشوبيديا',
            'bos': u'Разговор о Anarchopedia',
            'chi': u'安那其百科 talk',
            'dan': u'Anarchopedia-diskussion',
            'deu': u'Anarchopedia Diskussion',
            'dut': u'Overleg Anarchopedia',
            'ell': u'Αναρχοπαίδεια συζήτηση',
            'fra': u'Discussion Anarchopedia',
            'ind': u'Pembicaraan Anarchopedia',
            'ita': u'Discussioni Anarchopedia',
            'jpn': u'アナーキォペディア‐ノート',
            'nno': u'Anarchopedia-diskusjon',
            'nsh': u'Разговор о Anarchopedia',
            'nor': u'Anarchopedia-diskusjon',
            'pol': u'Dyskusja Anarchopedia',
            'por': u'Anarchopedia Discussão',
            'rum': u'Discuţie Anarhopedia',
            'rus': u'Обсуждение Anarchopedia',
            'spa': u'Anarchopedia Discusión',
            'srp': u'Разговор о Anarchopedia',
            'swe': u'Anarchopediadiskussion',
        }

        self.nocapitalize = self.langs.keys()

        self.obsolete = {
            'ar': 'ara',
            'bs': 'bos',
            'zh': 'chi',
            'da': 'dan',
            'de': 'deu',
            'ger': 'deu',
            'nl': 'dut',
            'el': 'ell',
            'gre': 'ell',
            'en': 'eng',
            'eo': 'epo',
            'fr': 'fra',
            'id': 'ind',
            'it': 'ita',
            'ja': 'jpn',
            'lt': 'lit',
            'no': 'nor',
            'nn': 'nno',
            'sh': 'nsh',
            'pl': 'pol',
            'pt': 'por',
            'ro': 'rum',
            'ru': 'rus',
            'es': 'spa',
            'sr': 'srp',
            'hrv': 'srp',
            'hr': 'srp',
            'sv': 'swe',
        }

    def version(self, code):
        return "1.12alpha"

    def path(self, code):
        return '/index.php'
