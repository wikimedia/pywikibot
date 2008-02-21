# -*- coding: utf-8  -*-

import urllib
import family, config

__version__ = '$Id$'

# An inofficial Gentoo wiki project.
# Ask for permission at http://gentoo-wiki.com/Help:Bots before running a bot.
# Be very careful, and set a long throttle: "until we see it is good one edit
# ever minute and one page fetch every 30 seconds, maybe a *bit* faster later".

class Family(family.Family):

    def __init__(self):
        family.Family.__init__(self)
        self.name = 'gentoo'

        self.langs = {
            'en':'gentoo-wiki.com',
            'de':'de.gentoo-wiki.com',
            'es':'es.gentoo-wiki.com',
            'fr':'fr.gentoo-wiki.com',
            'he':'he.gentoo-wiki.com',
            'hu':'hu.gentoo-wiki.com',
            'nl':'nl.gentoo-wiki.com',
            'pt':'pt.gentoo-wiki.com',
            'ru':'ru.gentoo-wiki.com',
            'zh':'zh.gentoo-wiki.com',
        }

        # TODO: sort
        self.languages_by_size = ['en', 'de', 'es', 'fr', 'he', 'hu', 'nl', 'pt', 'ru', 'zh']

        # he: also uses the default 'Media'
        del self.namespaces[-2]['he']

        self.namespaces[4] = {
            '_default': [u'Gentoo Linux Wiki', self.namespaces[4]['_default']],
        }
        self.namespaces[5] = {
            '_default': [u'Gentoo Linux Wiki talk', self.namespaces[5]['_default']],
            'de': u'Gentoo Linux Wiki Diskussion',
            'es': u'Gentoo Linux Wiki Discusión',
            'fr': u'Discussion Gentoo Linux Wiki',
            'he': u'שיחת Gentoo Linux Wiki',
            'hu': u'Gentoo Linux Wiki vita',
            'nl': u'Overleg Gentoo Linux Wiki',
            'pt': u'Gentoo Linux Wiki Discussão',
            'ru': u'Обсуждение Gentoo Linux Wiki',
        }
        self.namespaces[100] = {
            '_default': [u'Index'],
        }
        self.namespaces[101] = {
            '_default': [u'Index Talk'],
        }
        self.namespaces[110] = {
            '_default': [u'Ucpt'],
        }
        self.namespaces[111] = {
            '_default': [u'Ucpt talk'],
        }

        self.known_families.pop('gentoo-wiki')

    def scriptpath(self, code):
        return ''

    def apipath(self, code):
        # API not implemented on this wiki
        raise NotImplementedError(
            "The %s family does not yet support api.php." % self.name())

    def nicepath(self, code):
        return '/'

    def version(self, code):
        return "1.9alpha"
