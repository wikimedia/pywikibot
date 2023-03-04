#!/usr/bin/env python3
"""Tests for the site module."""
#
# (C) Pywikibot team, 2018-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

import pywikibot
from tests.aspects import DefaultSiteTestCase


class TestLinterPages(DefaultSiteTestCase):

    """Test linter_pages methods."""

    def setUp(self):
        """Skip tests if Linter extension is missing."""
        super().setUp()
        if not self.site.has_extension('Linter'):
            self.skipTest(
                f'The site {self.site} does not use Linter extension')

    def test_linter_pages(self):
        """Test the deprecated site.logpages() method."""
        le = list(self.site.linter_pages(
            lint_categories='obsolete-tag|missing-end-tag', total=5))
        self.assertLessEqual(len(le), 5)
        for entry in le:
            self.assertIsInstance(entry, pywikibot.Page)
            self.assertIn(entry._lintinfo['category'],
                          ['obsolete-tag', 'missing-end-tag'])


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
