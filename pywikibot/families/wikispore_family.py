# -*- coding: utf-8 -*-
"""Family module for Wikispore."""
#
# (C) Pywikibot team, 2020
#
# Distributed under the terms of the MIT license.
#
from pywikibot import family
from pywikibot.tools import deprecated


class Family(family.Family):  # noqa: D101

    """Family class for Wikispore."""

    name = 'wikispore'
    langs = {
        'en': 'wikispore.wmflabs.org',
        'test': 'wikispore-test.wmflabs.org',
    }

    @deprecated('APISite.version()', since='20141225')
    def version(self, code):
        return '1.36.0-alpha'

    def protocol(self, code):
        return 'https'
