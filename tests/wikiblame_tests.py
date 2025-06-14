"""Tests for the WikiHistoryMixin."""
#
# (C) Pywikibot team, 2022-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import re
import unittest
from contextlib import suppress

import pywikibot
from tests.aspects import TestCase


class TestWikiBlameMixin(TestCase):

    """Test WikiBlameMixin using nds wiki."""

    family = 'wikipedia'
    code = 'nds'

    def test_exceptions(self) -> None:
        """Test that main_authors fails if page does not exist."""
        page = pywikibot.Page(self.site, 'Pywikibot')
        title = re.escape(page.title(as_link=True))
        with self.assertRaisesRegex(pywikibot.exceptions.NoPageError,
                                    f"Page {title} doesn't exist"):
            page.authorship()

        page = pywikibot.Page(self.site, 'Diskuschoon:Wikipedia')
        with self.assertRaisesRegex(
            NotImplementedError,
                'main_authors method is not implemented for Talk: namespace'):
            page.authorship()

        page = pywikibot.Page(pywikibot.Site('wikipedia:nl'),
                              'Project:Pywikibot')
        with self.assertRaisesRegex(
            NotImplementedError,
                'main_authors method is not implemented for wikipedia:nl'):
            page.authorship()

    def test_main_authors(self) -> None:
        """Test main_authors() method."""
        page = pywikibot.Page(self.site, 'Python (Programmeerspraak)')
        auth = page.authorship(5)
        self.assertLessEqual(len(auth), 5)
        self.assertLessEqual(sum(pct for _, pct in auth.values()), 100)
        user, values = next(iter(auth.items()))
        self.assertEqual(user, 'RebeccaBreu')
        self.assertIsInstance(values[0], int)
        self.assertIsInstance(values[1], float)

    def test_restrictions(self) -> None:
        """Test main_authors() method with restrictions."""
        page = pywikibot.Page(pywikibot.Site('wikipedia:en'), 'Python')
        auth = page.authorship(4, min_chars=100, min_pct=5.0)
        self.assertLessEqual(len(auth), 4)
        for k, (chars, pct) in auth.items():
            with self.subTest(user=k):
                self.assertGreaterEqual(chars, 100)
                self.assertGreaterEqual(pct, 5.0)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
