# -*- coding: utf-8  -*-
"""Family module for WOW Wiki."""
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import family
from pywikibot.tools import deprecated


class Family(family.SubdomainFamily, family.WikiaFamily):

    """Family class for WOW Wiki."""

    name = 'wowwiki'
    domain = 'wow.wikia.com'

    languages_by_size = [
        'cs', 'da', 'de', 'el', 'en', 'es', 'fa', 'fi', 'fr', 'he', 'hu', 'is',
        'it', 'ja', 'ko', 'lt', 'lv', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ru',
        'sk', 'sv', 'tr', 'zh', 'zh-tw'
    ]

    interwiki_removals = ['hr', 'ro', 'sr']

    def __init__(self):
        """Constructor."""
        super(Family, self).__init__()
        # Override 'sv'.  http://sv.wow.wikia.com is an empty wiki.
        # The interwikimap in this family map 'sv' to this empty wiki.
        self.langs['sv'] = 'sv.warcraft.wikia.com'

        self.disambiguationTemplates['en'] = ['disambig', 'disambig/quest',
                                              'disambig/quest2',
                                              'disambig/achievement2']
        self.disambcatname['en'] = "Disambiguations"

        # Wikia's default CategorySelect extension always puts categories last
        self.categories_last = self.langs.keys()

    @property
    def domains(self):
        """List of domains used by family wowwiki."""
        return (self.domain, 'wowwiki.com', 'warcraft.wikia.com')

    @deprecated('APISite.version()')
    def version(self, code):
        """Return the version for this family."""
        return '1.19.20'
