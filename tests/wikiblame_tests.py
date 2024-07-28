"""Tests for the WikiHistoryMixin."""
#
# (C) Pywikibot team, 2022-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import re
import unittest
from contextlib import suppress

import pywikibot
from tests.aspects import TestCase, require_modules


class TestWikiBlameMixin(TestCase):

    """Test WikiBlameMixin using nds wiki."""

    family = 'wikipedia'
    code = 'nl'

    def test_exceptions(self):
        """Test that main_authors fails if page does not exist."""
        page = pywikibot.Page(self.site, 'Pywikibot')
        title = re.escape(page.title(as_link=True))
        with self.assertRaisesRegex(pywikibot.exceptions.NoPageError,
                                    f"Page {title} doesn't exist"):
            page.authorship()

        page = pywikibot.Page(self.site, 'Project:Pywikibot')
        with self.assertRaisesRegex(
            NotImplementedError,
                'main_authors method is implemented for main namespace only'):
            page.authorship()

    @require_modules('wikitextparser')
    def test_main_authors(self):
        """Test main_authors() method."""
        page = pywikibot.Page(self.site, 'Python (programmeertaal)')
        auth = page.authorship(5)
        self.assertLessEqual(len(auth), 5)
        self.assertLessEqual(sum(pct for _, pct in auth.values()), 100)
        user, values = next(iter(auth.items()))
        self.assertEqual(user, 'Emperor045')
        self.assertIsInstance(values[0], int)
        self.assertIsInstance(values[1], float)

    @require_modules('wikitextparser')
    def test_restrictions(self):
        """Test main_authors() method with restrictions."""
        page = pywikibot.Page(pywikibot.Site('wikipedia:en'), 'Python')
        auth = page.authorship(min_chars=100, min_pct=5.0)
        self.assertLessEqual(len(auth), 4)
        for k, (chars, pct) in auth.items():
            with self.subTest(user=k):
                self.assertGreaterEqual(chars, 100)
                self.assertGreaterEqual(pct, 5.0)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
