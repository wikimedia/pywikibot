"""Family module for wikiHow wiki.

.. versionadded:: 3.0
"""
#
# (C) Pywikibot team, 2020-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family
from pywikibot.tools import classproperty


class Family(family.SubdomainFamily):

    """Family class for wikiHow Wiki.

    .. versionadded:: 3.0
    """

    name = 'wikihow'
    domain = 'wikihow.com'

    codes = (
        'ar', 'cs', 'de', 'en', 'es', 'fr', 'hi', 'id', 'it', 'ja', 'ko', 'nl',
        'pt', 'ru', 'th', 'tr', 'vi', 'zh',
    )

    removed_wikis = ['ca', 'cy', 'fa', 'he', 'pl', 'ur']

    title_delimiter_and_aliases = '- '
    """.. versionadded:: 7.0"""

    @classproperty
    def domains(cls):
        """List of domains used by family wikiHow."""
        return [
            cls.domain,
            'wikihow.cz',  # cs
            'wikihow.it',
            'wikihow.jp',  # ja
            'wikihow.com.tr',
            'wikihow.vn',  # vi
        ]

    @classproperty
    def langs(cls):
        """Property listing family languages."""
        code_replacement = {'cz': 'cs', 'jp': 'ja', 'vn': 'vi'}
        cls.langs = super().langs
        cls.langs['en'] = 'www.' + cls.domain
        for domain in cls.domains:
            if domain == cls.domain:
                continue
            *_, code = domain.rpartition('.')
            code = code_replacement.get(code, code)
            cls.langs[code] = 'www.' + domain
        return cls.langs

    def scriptpath(self, code) -> str:
        """Return the script path for this family."""
        return ''

    def protocol(self, code) -> str:
        """Return 'https' as the protocol."""
        return 'https'
