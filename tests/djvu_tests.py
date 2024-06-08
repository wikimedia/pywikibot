#!/usr/bin/env python3
"""Unit tests for tools.djvu.py."""

#
# (C) Pywikibot team, 2015-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import os
import subprocess
import unittest
from contextlib import suppress

from pywikibot.tools.djvu import DjVuFile
from tests import create_path_func, join_data_path
from tests.aspects import TestCase
from tests.utils import skipping


join_djvu_data_path = create_path_func(join_data_path, 'djvu')
file_djvu = join_djvu_data_path('myfilé.djvu')  # test non-ASCII name


class TestDjVuFile(TestCase):

    """Test DjVuFile class."""

    net = False

    file_djvu_wo_text = join_djvu_data_path('myfile_wo_text.djvu')
    test_txt = 'A file with non-ASCII characters, \nlike é or ç'

    @classmethod
    def setUpClass(cls):
        """Skip if djvulibre library not installed."""
        super().setUpClass()
        with skipping(OSError, msg='djvulibre library not installed.'):
            dp = subprocess.Popen(['djvudump'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            dp.communicate()

    def setUp(self):  # pragma: no cover
        """Set up test."""
        super().setUp()
        self.djvu = DjVuFile(file_djvu)

    def test_number_of_images(self):  # pragma: no cover
        """Test page number generator."""
        self.assertEqual(self.djvu.number_of_images(), 4)

    def test_page_info(self):  # pragma: no cover
        """Test page info retrieval."""
        self.assertEqual(self.djvu.page_info(1),
                         ('{myfile.djvu}', ('1092x221', 600)))

    def test_get_most_common_info(self):  # pragma: no cover
        """Test that most common (size, dpi) are returned."""
        self.assertEqual(self.djvu.get_most_common_info(), ('1092x221', 600))

    def test_has_text(self):  # pragma: no cover
        """Test if djvu file contains text."""
        self.assertTrue(self.djvu.has_text())
        djvu = DjVuFile(self.file_djvu_wo_text)
        self.assertFalse(djvu.has_text())

    def test_get_existing_page_number(self):  # pragma: no cover
        """Test text is returned for existing page number."""
        self.assertTrue(self.djvu.has_text())
        txt = self.djvu.get_page(1)
        self.assertEqual(txt, self.test_txt)

    def test_get_not_existing_page_number(self):  # pragma: no cover
        """Test error is raised if djvu page number is out of range."""
        self.assertTrue(self.djvu.has_text())
        with self.assertRaises(ValueError):
            self.djvu.get_page(100)

    def test_get_not_existing_page(self):  # pragma: no cover
        """Test error is raised if djvu file has no text."""
        self.assertFalse(self.djvu.has_text())
        with self.assertRaises(ValueError):
            self.djvu.get_page(1)

    def test_whiten_not_existing_page_number(self):  # pragma: no cover
        """Test djvu page cannot be whitend if page number is out of range."""
        with self.assertRaises(ValueError):
            self.djvu.whiten_page(100)

    def test_delete_not_existing_page_number(self):  # pragma: no cover
        """Test djvu page cannot be deleted if page number is out of range."""
        with self.assertRaises(ValueError):
            self.djvu.delete_page(100)

    def test_clear_cache(self):  # pragma: no cover
        """Test if djvu file contains text."""
        self.assertTrue(self.djvu.has_text())
        self.djvu._has_text = False
        self.assertFalse(self.djvu.has_text())
        self.assertTrue(self.djvu.has_text(force=True))


class TestDjVuFileWithoutLib(TestCase):

    """Test DjVuFile class without library installed."""

    net = False

    file_djvu_not_existing = join_djvu_data_path('not_existing.djvu')

    def setUp(self):
        """Set up test."""
        super().setUp()
        self.djvu = DjVuFile(file_djvu)

    def test_file_existence(self):
        """Test file existence checks."""
        self.assertEqual(os.path.abspath(file_djvu), self.djvu.file)
        with self.assertRaises(IOError):
            DjVuFile(self.file_djvu_not_existing)

    def test_str_method(self):
        """Test __str__() method."""
        self.assertEqual(str(self.djvu), f"DjVuFile('{file_djvu}')")

    def test_repr_method(self):
        """Test __repr__() method."""
        self.assertEqual(repr(self.djvu),
                         f"pywikibot.tools.djvu.DjVuFile('{file_djvu}')")


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
