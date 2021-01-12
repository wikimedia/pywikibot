"""Family module for Wikispore."""
#
# (C) Pywikibot team, 2020
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family


class Family(family.Family):  # noqa: D101

    """Family class for Wikispore."""

    name = 'wikispore'
    langs = {
        'en': 'wikispore.wmflabs.org',
        'test': 'wikispore-test.wmflabs.org',
    }

    def protocol(self, code):
        return 'https'
