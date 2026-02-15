#
# (C) Pywikibot team, 2022-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the WikiHistoryMixin."""
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

    def test_wikiwho_exceptions(self) -> None:
        """Test that get_annotations fails for unsupported configurations."""
        en_site = pywikibot.Site('wikipedia:en')
        page = pywikibot.Page(en_site, 'NonExistentPageXYZ123')
        with self.assertRaisesRegex(pywikibot.exceptions.NoPageError,
                                    "doesn't exist"):
            page.get_annotations()

        page = pywikibot.Page(en_site, 'Talk:Wikipedia')
        with self.assertRaisesRegex(
            NotImplementedError,
                'WikiWho API is not implemented for Talk: namespace'):
            page.get_annotations()

        page = pywikibot.Page(pywikibot.Site('wikipedia:ru'),
                              'Python')
        with self.assertRaisesRegex(
            NotImplementedError,
                'WikiWho API is not implemented for wikipedia:ru'):
            page.get_annotations()

    def test_wikiwho_url_construction(self) -> None:
        """Test WikiWho URL construction."""
        page = pywikibot.Page(pywikibot.Site('wikipedia:en'), 'Test')
        url = page._build_wikiwho_url('all_content')
        expected = ('https://wikiwho-api.wmcloud.org/en/api/v1.0.0-beta/'
                    'all_content/Test/')
        self.assertEqual(url, expected)

        page = pywikibot.Page(pywikibot.Site('wikipedia:en'),
                              'Python (programming language)')
        url = page._build_wikiwho_url('all_content')
        self.assertIn('Python%20%28programming%20language%29', url)

    def test_wikiwho_supported_languages(self) -> None:
        """Test that WIKIWHO_CODES contains expected languages."""
        from pywikibot.page._toolforge import WikiWhoMixin
        codes = WikiWhoMixin.WIKIWHO_CODES
        expected_langs = ['ar', 'de', 'en', 'es', 'eu', 'fr', 'hu', 'id',
                          'it', 'ja', 'nl', 'pl', 'pt', 'tr', 'zh']
        for lang in expected_langs:
            self.assertIn(lang, codes)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
