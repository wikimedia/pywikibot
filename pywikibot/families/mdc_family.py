# -*- coding: utf-8  -*-
import family

# The Mozilla Developer Center, Official Mozilla Documents.

class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'mdc'

        self.langs = {
            'ca': None,
            'cn': None,
            'de': None,
            'en': None,
            'es': None,
            'fr': None,
            'it': None,
            'ja': None,
            'ko': None,
            'nl': None,
            'pl': None,
            'pt': None,
            'zh_tw':None,
        }

        self.namespaces[4] = {
            '_default': u'MDC',
        }

        self.namespaces[5] = {
            '_default': u'MDC talk',
            'ca': u'MDC Discussió',
            'cn': u'MDC talk',
            'de': u'MDC Diskussion',
            'es': u'MDC Discusión',
            'fr': u'Discussion MDC',
            'it': u'Discussioni MDC',
            'ja': u'MDC�?ノート',
            'ko': u'MDC토론',
            'nl': u'Overleg MDC',
            'pl': u'Dyskusja MDC',
            'pt': u'MDC Discussão',
        }

    def hostname(self,code):
        return 'developer.mozilla.org'

    def scriptpath(self, code):
        return '/'+code+'/docs'

    def apipath(self, code):
        raise NotImplementedError(
            "The mdc family does not support api.php")

    def version(self, code):
        return "1.9.3"
