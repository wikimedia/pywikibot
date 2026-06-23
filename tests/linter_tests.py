#!/usr/bin/env python3
#
# (C) Pywikibot team, 2018-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the site module."""
from __future__ import annotations

import unittest
from contextlib import suppress

import pywikibot
from tests.aspects import DefaultSiteTestCase


class TestLinterPages(DefaultSiteTestCase):

    """Test linter_pages methods."""

    def setUp(self) -> None:
        """Skip tests if Linter extension is missing."""
        super().setUp()
        if not self.site.has_extension('Linter'):
            self.skipTest(
                f'The site {self.site} does not use Linter extension')

    def test_linter_pages(self) -> None:
        """Test the deprecated site.logpages() method."""
        le = list(self.site.linter_pages(
            lint_categories='obsolete-tag|missing-end-tag', total=5))
        self.assertLessEqual(len(le), 5)
        for entry in le:
            self.assertIsInstance(entry, pywikibot.Page)
            self.assertIn(entry._lintinfo['category'],
                          ['obsolete-tag', 'missing-end-tag'])

    def test_pageids(self) -> None:
        """Test pageids parameter."""
        for test, arg in {
            'range': range(4711, 4750),
            'list of strings': ['4715', '4716', '4717', '4718', '4718'],
            'tuple of ints': (4715, 4716, 4717, 4718, 4718, 4719, 4720, 4721),
            'pipe': '4715|4716|4717|4718|4718|4719|4720|4721|4722|4723|4724',
            'pipe with spaces': '4715|4716 |4717| 4718|4718|4719|4720|4721',
            'string': '4717',
            'int': 4717,
        }.items():
            with self.subTest(arg=test):
                le = list(self.site.linter_pages(pageids=arg))
                for entry in le:
                    self.assertIsInstance(entry, pywikibot.Page)
                    info = entry._lintinfo
                    self.assertIsInstance(info['lintId'], int)
                    self.assertIsInstance(info['category'], str)
                    self.assertIsInstance(info['location'], list)
                    self.assertIsInstance(info['templateInfo'], dict)
                    self.assertIsInstance(info['params'], dict)

    def test_pageids_fail(self) -> None:
        """Test wrong pageids parameter raises APIError."""
        with self.assertRaisesRegex(
            pywikibot.exceptions.APIError,
            'Invalid value "4711-4750" for integer parameter "lntpageid"'
        ):
            list(self.site.linter_pages(pageids='4711-4750'))


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
