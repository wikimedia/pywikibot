#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for WikiWhoMixin pickle subdirectory structure."""
from __future__ import annotations

import unittest
from pathlib import Path

from pywikibot.page._toolforge import WikiWhoMixin
from tests.aspects import TestCase


class TestWikiWhoPicklePaths(TestCase):

    """Test WikiWhoMixin pickle subdirectory path calculation."""

    net = False

    def test_pickle_path_basic(self) -> None:
        """Test basic pickle path calculation."""
        path = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 100000, '/tmp/cache')
        expected = Path('/tmp/cache/en/100000/100000.p')
        self.assertEqual(path, expected)

    def test_pickle_path_subdirectory_calculation(self) -> None:
        """Test subdirectory calculated as floor(page_id/1000)*1000."""
        # page_id 100000 -> subdirectory 100000
        path1 = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 100000, '/tmp/cache')
        self.assertEqual(path1.parent.name, '100000')

        # page_id 100002 -> subdirectory 100000
        path2 = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 100002, '/tmp/cache')
        self.assertEqual(path2.parent.name, '100000')

        # page_id 100999 -> subdirectory 100000
        path3 = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 100999, '/tmp/cache')
        self.assertEqual(path3.parent.name, '100000')

        # page_id 200005 -> subdirectory 200000
        path4 = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 200005, '/tmp/cache')
        self.assertEqual(path4.parent.name, '200000')

    def test_pickle_path_different_languages(self) -> None:
        """Test pickle paths for different language codes."""
        path_en = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 100000, '/tmp/cache')
        path_de = WikiWhoMixin._get_wikiwho_pickle_path(
            'de', 100000, '/tmp/cache')
        path_fi = WikiWhoMixin._get_wikiwho_pickle_path(
            'fi', 100000, '/tmp/cache')

        self.assertEqual(
            path_en, Path('/tmp/cache/en/100000/100000.p'))
        self.assertEqual(
            path_de, Path('/tmp/cache/de/100000/100000.p'))
        self.assertEqual(
            path_fi, Path('/tmp/cache/fi/100000/100000.p'))

    def test_pickle_path_filename(self) -> None:
        """Test pickle filename is page_id.p."""
        path1 = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 123456, '/tmp/cache')
        self.assertEqual(path1.name, '123456.p')

        path2 = WikiWhoMixin._get_wikiwho_pickle_path(
            'de', 999999, '/tmp/cache')
        self.assertEqual(path2.name, '999999.p')

    def test_pickle_path_full_structure(self) -> None:
        """Test complete directory structure."""
        # Test case from task description
        path = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 100000, '/cache')
        self.assertEqual(path, Path('/cache/en/100000/100000.p'))

        # Additional examples from task
        path = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 100002, '/cache')
        self.assertEqual(path, Path('/cache/en/100000/100002.p'))

        path = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 200005, '/cache')
        self.assertEqual(path, Path('/cache/en/200000/200005.p'))

    def test_pickle_path_edge_cases(self) -> None:
        """Test edge cases for subdirectory calculation."""
        # page_id 0 -> subdirectory 0
        path = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 0, '/tmp/cache')
        self.assertEqual(path.parent.name, '0')

        # page_id 1 -> subdirectory 0
        path = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 1, '/tmp/cache')
        self.assertEqual(path.parent.name, '0')

        # page_id 999 -> subdirectory 0
        path = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 999, '/tmp/cache')
        self.assertEqual(path.parent.name, '0')

        # page_id 1000 -> subdirectory 1000
        path = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 1000, '/tmp/cache')
        self.assertEqual(path.parent.name, '1000')

    def test_pickle_path_returns_pathlib_path(self) -> None:
        """Test that method returns pathlib.Path object."""
        path = WikiWhoMixin._get_wikiwho_pickle_path(
            'en', 100000, '/tmp/cache')
        self.assertIsInstance(path, Path)


if __name__ == '__main__':
    unittest.main()
