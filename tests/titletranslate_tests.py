#!/usr/bin/env python3
"""Tests for titletranslate module."""
#
# (C) Pywikibot team, 2022
#
# Distributed under the terms of the MIT license.
#
import unittest

from pywikibot.titletranslate import translate
from tests.aspects import TestCase


class TestTitleTranslate(TestCase):

    """Tests for titletranslate module."""

    sites = {
        'dewikt': {
            'family': 'wiktionary',
            'code': 'de',
        },
        'enwiki': {
            'family': 'wikipedia',
            'code': 'en',
        },
        'zhwikisource': {
            'family': 'wikisource',
            'code': 'zh',
        },
    }

    def test_translate(self, key):
        """Test translate method."""
        site = self.get_site(key)
        result = translate(page=self.get_mainpage(site), auto=False,
                           hints=['5:', 'nl,en,zh'], site=site)
        self.assertLength(result, 6)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
