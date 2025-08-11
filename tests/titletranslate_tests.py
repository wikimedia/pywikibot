#!/usr/bin/env python3
"""Tests for titletranslate module."""
#
# (C) Pywikibot team, 2022-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

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

    def test_translate(self, key) -> None:
        """Test translate method."""
        site = self.get_site(key)
        result = translate(page=self.get_mainpage(site), auto=False,
                           hints=['5:', 'nl,en,zh'], site=site)
        self.assertLength(result, 6)
        result = translate(page=self.get_mainpage(site))
        self.assertIsEmpty(result)
        result = translate(page=self.get_mainpage(site), hints=['nl'])
        self.assertLength(result, 1)
        with self.assertRaisesRegex(RuntimeError,
                                    'Either page or site parameter must be '
                                    r'given with translate\(\)'):
            translate()


if __name__ == '__main__':
    unittest.main()
