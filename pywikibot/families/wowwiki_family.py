# -*- coding: utf-8 -*-
"""Family module for WOW Wiki."""
#
# (C) Pywikibot team, 2009-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot import family
from pywikibot.tools import deprecated, classproperty


class Family(family.SubdomainFamily, family.FandomFamily):

    """Family class for WOW Wiki."""

    name = 'wowwiki'
    domain = 'wowwiki.fandom.com'

    codes = (
        'ar', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fa', 'fi', 'fr', 'he',
        'hu', 'is', 'it', 'ja', 'ko', 'lt', 'lv', 'nl', 'nn', 'no', 'pl', 'pt',
        'pt-br', 'ru', 'sk', 'tr', 'uk', 'zh', 'zh-tw'
    )

    interwiki_removals = ['hr', 'ro', 'sr', 'sv']

    @classproperty
    @deprecated('codes attribute', since='20190422')
    def languages_by_size(cls):
        """DEPRECATED. languages_by_size property for compatibility purpose."""
        return list(cls.codes)

    @classproperty
    def langs(cls):
        """Property listing family languages."""
        cls.langs = super(Family, cls).langs
        cls.langs.update({code: cls.domains[1] for code in ('es', 'et')})
        cls.langs['uk'] = 'uk.' + cls.domains[2]
        return cls.langs

    @classproperty
    def disambiguationTemplates(cls):  # noqa: N802
        """Property listing disambiguation templates."""
        cls.disambiguationTemplates = \
            super(Family, cls).disambiguationTemplates
        cls.disambiguationTemplates['en'] = ['disambig', 'disambig/quest',
                                             'disambig/quest2',
                                             'disambig/achievement2']
        return cls.disambiguationTemplates

    @classproperty
    def disambcatname(cls):
        """Property listing disambiguation category name."""
        cls.disambcatname = super(Family, cls).disambcatname
        cls.disambcatname['en'] = 'Disambiguations'
        return cls.disambcatname

    # Wikia's default CategorySelect extension always puts categories last
    @classproperty
    def categories_last(cls):
        """Property listing site keys for categories at last position."""
        return cls.langs.keys()

    @classproperty
    def domains(cls):
        """List of domains used by family wowwiki."""
        return [cls.domain, 'worldofwarcraft.fandom.com', 'warcraft.wikia.com']

    def protocol(self, code):
        """Return the protocol for this family."""
        if code == 'uk':
            return 'http'
        return super(Family, self).protocol(code)

    def scriptpath(self, code):
        """Return the script path for this family."""
        if code == 'uk':
            return ''
        return super(Family, self).scriptpath(code)
