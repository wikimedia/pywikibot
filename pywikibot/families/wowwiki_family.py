"""Family module for WOW wiki."""
#
# (C) Pywikibot team, 2009-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family
from pywikibot.tools import classproperty


class Family(family.FandomFamily):

    """Family class for WOW Wiki."""

    name = 'wowwiki'
    domain = 'wowwiki.fandom.com'

    codes = (
        'ar', 'cs', 'da', 'de', 'el', 'en', 'es', 'et', 'fa', 'fi', 'fr', 'he',
        'hu', 'is', 'it', 'ja', 'ko', 'lt', 'lv', 'nl', 'no', 'pl', 'pt',
        'pt-br', 'ru', 'sk', 'sv', 'tr', 'uk', 'zh', 'zh-tw'
    )

    removed_wikis = ['hr', 'ro', 'sr']

    code_aliases = {'nn': 'no'}

    @classproperty
    def langs(cls):
        """Property listing family languages."""
        cls.langs = super().langs
        # override deviations
        for i, lang in enumerate(['es', 'et', 'sv'], start=1):
            cls.langs[lang] = cls.domains[i]
        cls.langs['uk'] = cls.domains[-1]
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

    # Wikia's default CategorySelect extension always puts categories last
    @classproperty
    def categories_last(cls):
        """Property listing site keys for categories at last position."""
        return cls.langs.keys()

    @classproperty
    def domains(cls):
        """List of domains used by family wowwiki."""
        return [cls.domain,
                'wow-es.gamepedia.com',  # es
                'worldofwarcraft.fandom.com',  # et
                'warcraft.fandom.com']  # sv, uk

    def scriptpath(self, code):
        """Return the script path for this family."""
        if code == 'es':
            return ''
        return super().scriptpath(code)
