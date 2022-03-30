"""Family module for Wikispore.

.. versionadded:: 4.1
"""
#
# (C) Pywikibot team, 2020-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


class Family(family.Family):

    """Family class for Wikispore.

    .. versionadded:: 4.1
    """

    name = 'wikispore'
    langs = {
        'en': 'wikispore.wmflabs.org',
        'test': 'wikispore-test.wmflabs.org',
    }

    def protocol(self, code) -> str:
        return 'https'
