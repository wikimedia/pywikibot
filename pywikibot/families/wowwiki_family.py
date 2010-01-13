# -*- coding: utf-8  -*-

__version__ = '$Id$'

from pywikibot import family


class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = 'wowwiki'

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
            'hr': 'hr.wow.wikia.com',
            'hu': 'hu.wow.wikia.com',
            'is': 'is.wow.wikia.com',
            'it': 'it.wow.wikia.com',
            'ja': 'ja.wow.wikia.com',
            'ko': 'ko.wow.wikia.com',
            'lt': 'lt.wow.wikia.com',
            'lv': 'lv.wow.wikia.com',
            'nl': 'nl.wow.wikia.com',
            'no': 'no.wow.wikia.com',
            'pl': 'pl.wow.wikia.com',
            'pt': 'pt.wow.wikia.com',
            'pt-br': 'pt-br.wow.wikia.com',
            'ro': 'ro.wow.wikia.com',
            'ru': 'ru.wow.wikia.com',
            'sk': 'sk.wow.wikia.com',
            'sr': 'sr.wow.wikia.com',
            'sv': 'sv.warcraft.wikia.com',
            'tr': 'tr.wow.wikia.com',
            'zh-tw': 'zh-tw.wow.wikia.com',
            'zh': 'zh.wow.wikia.com'
        }

        self.content_id = "article"

        self.disambiguationTemplates['en'] = ['disambig', 'disambig/quest',
                                              'disambig/quest2',
                                              'disambig/achievement2']
        self.disambcatname['en'] = "Disambiguations"

    def scriptpath(self, code):
        return ''

    def version(self, code):
        return '1.15.1'
