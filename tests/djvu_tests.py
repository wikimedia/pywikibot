#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for djvutext.py script."""

#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#

from __future__ import absolute_import, unicode_literals

import subprocess

from pywikibot.tools.djvu import DjVuFile

from tests import join_data_path, create_path_func
from tests.aspects import unittest, TestCase

join_djvu_data_path = create_path_func(join_data_path, 'djvu')


class TestDjVuFile(TestCase):

    """Test DjVuFile class."""

    net = False

    file_djvu_not_existing = join_djvu_data_path('not_existing.djvu')
    file_djvu = join_djvu_data_path('myfile.djvu')
    file_djvu_wo_text = join_djvu_data_path('myfile_wo_text.djvu')
    test_txt = 'A file with non-ASCII characters, \nlike é or ç'

    @classmethod
    def setUpClass(cls):
        """Setup tests."""
        super(TestDjVuFile, cls).setUpClass()
        try:
            subprocess.Popen(['djvudump'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError:
            raise unittest.SkipTest('djvulibre library not installed.')

    def test_file_existance(self):
        """Test file existence checks."""
        djvu = DjVuFile(self.file_djvu)
        self.assertEqual(self.file_djvu, djvu.file_djvu)
        self.assertRaises(IOError, DjVuFile, self.file_djvu_not_existing)

    def test_number_of_images(self):
        """Test page number generator."""
        djvu = DjVuFile(self.file_djvu)
        self.assertEqual(djvu.number_of_images(), 4)

    def test_has_text(self):
        """Test if djvu file contains text."""
        djvu = DjVuFile(self.file_djvu)
        self.assertTrue(djvu.has_text())
        djvu = DjVuFile(self.file_djvu_wo_text)
        self.assertFalse(djvu.has_text())

    def test_get_existing_page_number(self):
        """Test if djvu file contains text."""
        djvu = DjVuFile(self.file_djvu)
        self.assertTrue(djvu.has_text())
        txt = djvu.get_page(1)
        self.assertEqual(txt, self.test_txt)

    def test_get_not_existing_page_number(self):
        """Test if djvu file contains text."""
        djvu = DjVuFile(self.file_djvu)
        self.assertTrue(djvu.has_text())
        self.assertRaises(ValueError, djvu.get_page, 100)

    def test_get_not_existing_page(self):
        """Test if djvu file contains text."""
        djvu = DjVuFile(self.file_djvu_wo_text)
        self.assertFalse(djvu.has_text())
        self.assertRaises(ValueError, djvu.get_page, 100)

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
