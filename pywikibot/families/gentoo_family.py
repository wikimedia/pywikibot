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

        self.languages_by_size = ['en', 'de', 'es', 'fr', 'cs', 'nl', 'tr', 'ru', 'fi']
        for l in self.languages_by_size:
            self.langs[l] = '%s.gentoo-wiki.com' % l

        self.known_families.pop('gentoo-wiki')

    def version(self, code):
        return "1.16alpha"
