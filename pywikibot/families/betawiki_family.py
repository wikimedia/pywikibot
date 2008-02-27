# -*- coding: utf-8  -*-

from pywikibot import family

# The official Beta Wiki.
class Family(family.Family):

    def __init__(self):

        family.Family.__init__(self)
        self.name = 'betawiki' #Set the family name; this should be the same as in the filename.

        self.langs = {
            'en': 'www.ucip.org', #Put the hostname here.
        }

        self.namespaces[4] = {
            '_default': [u'BetaWiki', self.namespaces[4]['_default']],
        }

        self.namespaces[5] = {
            '_default': [u'BetaWiki talk', self.namespaces[5]['_default']],
        }

    def version(self, code):
        return "1.5.4"  #The MediaWiki version used. Not very important in most cases.

    def scriptpath(self, code):
        return '/beta' #The value of {{SCRIPTPATH}} on this wiki

    def apipath(self, code):
        # Betawiki uses old, pre-API MediaWiki version
        raise NotImplementedError(
            "The %s family does not support api.php" % self.name)
