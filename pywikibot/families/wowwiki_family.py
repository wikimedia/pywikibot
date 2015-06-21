# -*- coding: utf-8  -*-
"""Family module for WOW Wiki."""
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot import family
from pywikibot.tools import deprecated


class Family(family.Family):

    """Family class for WOW Wiki."""

    name = 'wowwiki'

    interwiki_removals = ['hr', 'ro', 'sr']

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()

        self.langs = {
            'cs': 'cs.wow.wikia.com',
            'da': 'da.wowwiki.com',
            'de': 'de.wow.wikia.com',
            'el': 'el.wow.wikia.com',
            'en': 'www.wowwiki.com',
            'es': 'es.wow.wikia.com',
            'fa': 'fa.wow.wikia.com',
            'fi': 'fi.wow.wikia.com',
            'fr': 'fr.wowwiki.com',
            'he': 'he.wow.wikia.com',
            'hu': 'hu.wow.wikia.com',
            'is': 'is.wow.wikia.com',
            'it': 'it.wow.wikia.com',
            'ja': 'ja.wow.wikia.com',
            'ko': 'ko.wow.wikia.com',
            'lt': 'lt.wow.wikia.com',
            'lv': 'lv.wow.wikia.com',
            'nl': 'nl.wow.wikia.com',
            'no': 'no.wowwiki.com',
            'pl': 'pl.wow.wikia.com',
            'pt': 'pt.wow.wikia.com',
            'pt-br': 'pt-br.wow.wikia.com',
            'ru': 'ru.wow.wikia.com',
            'sk': 'sk.wow.wikia.com',
            'sv': 'sv.warcraft.wikia.com',
            'tr': 'tr.wow.wikia.com',
            'zh-tw': 'zh-tw.wow.wikia.com',
            'zh': 'zh.wow.wikia.com'
        }

        self.disambiguationTemplates['en'] = ['disambig', 'disambig/quest',
                                              'disambig/quest2',
                                              'disambig/achievement2']
        self.disambcatname['en'] = "Disambiguations"

        # Wikia's default CategorySelect extension always puts categories last
        self.categories_last = self.langs.keys()

    def scriptpath(self, code):
        """Return the script path for this family."""
        return ''

    @deprecated('APISite.version()')
    def version(self, code):
        """Return the version for this family."""
        return '1.19.20'
