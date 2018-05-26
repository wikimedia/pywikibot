# -*- coding: utf-8 -*-
"""Family module for WOW Wiki."""
#
# (C) Pywikibot team, 2009-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import family
from pywikibot.tools import deprecated, classproperty


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

    # Override 'sv'. http://sv.wow.wikia.com is an empty wiki.
    # The interwikimap in this family map 'sv' to this empty wiki.
    @classproperty
    def langs(cls):
        cls.langs = super(Family, cls).langs
        cls.langs['sv'] = 'sv.warcraft.wikia.com'
        return cls.langs

    @classproperty
    def disambiguationTemplates(cls):
        cls.disambiguationTemplates = \
            super(Family, cls).disambiguationTemplates
        cls.disambiguationTemplates['en'] = ['disambig', 'disambig/quest',
                                             'disambig/quest2',
                                             'disambig/achievement2']
        return cls.disambiguationTemplates

    @classproperty
    def disambcatname(cls):
        cls.disambcatname = super(Family, cls).disambcatname
        cls.disambcatname['en'] = 'Disambiguations'
        return cls.disambcatname

    # Wikia's default CategorySelect extension always puts categories last
    @classproperty
    def categories_last(cls):
        return cls.langs.keys()

    @classproperty
    def domains(cls):
        """List of domains used by family wowwiki."""
        return (cls.domain, 'wowwiki.com', 'warcraft.wikia.com')

    @deprecated('APISite.version()')
    def version(self, code):
        """Return the version for this family."""
        return '1.19.20'
