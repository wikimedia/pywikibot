"""Family module for WOW wiki."""
#
# (C) Pywikibot team, 2009-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot import family
from pywikibot.tools import classproperty, deprecated


class Family(family.FandomFamily):

    """Family class for WOW Wiki."""

    name = 'wowwiki'
    domain = 'wowwiki.fandom.com'

    codes = {
        'ar', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fa', 'fi', 'fr', 'he',
        'hu', 'it', 'ja', 'ko', 'nl', 'no', 'pl', 'pt', 'pt-br', 'ru', 'uk',
        'zh', 'zh-tw',
    }

    removed_wikis = ['is', 'hr', 'lt', 'lv', 'ro', 'sk', 'sr', 'sv', 'tr']

    code_aliases = {'nn': 'no'}

    @classproperty
    def langs(cls):
        """Property listing family languages."""
        cls.langs = super().langs
        # override deviations
        for i, lang in enumerate(['en', 'es', 'et', 'uk'], start=1):
            cls.langs[lang] = cls.domains[i]
        return cls.langs

    @classproperty
    def disambiguationTemplates(cls):  # noqa: N802
        """Property listing disambiguation templates."""
        cls.disambiguationTemplates = super().disambiguationTemplates
        cls.disambiguationTemplates['en'] = ['disambig', 'disambig/quest',
                                             'disambig/quest2',
                                             'disambig/achievement2']
        return cls.disambiguationTemplates

    @classproperty
    def disambcatname(cls):
        """Property listing disambiguation category name."""
        cls.disambcatname = super().disambcatname
        cls.disambcatname['en'] = 'Disambiguations'
        return cls.disambcatname

    # Wikia's default SelectCategory extension always puts categories last
    @classproperty
    @deprecated('site.has_extension("CategorySelect")', since='10.3.0')
    def categories_last(cls):
        """Property listing site keys for categories at last position.

        .. deprecated:: 10.3
           use :meth:`site.has_extension('CategorySelect')
           <pywikibot.site._apisite.APISite.has_extension>` instead
        """
        return cls.langs.keys()

    @classproperty
    def domains(cls):
        """List of domains used by family wowwiki."""
        return [cls.domain,
                'wowwiki-archive.fandom.com',  # en
                'wow.gamepedia.com',  # es
                'worldofwarcraft.fandom.com',  # et
                'warcraft.fandom.com']  # uk

    def scriptpath(self, code):
        """Return the script path for this family."""
        if code == 'es':
            return ''
        return super().scriptpath(code)
