#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Unit tests for djvu.py."""

#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#

from __future__ import absolute_import, unicode_literals

import os
import subprocess

from pywikibot.tools.djvu import DjVuFile
from pywikibot.tools import PY2

from tests import join_data_path, create_path_func
from tests.aspects import unittest, TestCase

join_djvu_data_path = create_path_func(join_data_path, 'djvu')

if not PY2:
    unicode = str


class TestDjVuFile(TestCase):

    """Test DjVuFile class."""

    net = False

    file_djvu_not_existing = join_djvu_data_path('not_existing.djvu')
    file_djvu = join_djvu_data_path('myfilé.djvu')  # test non-ascii name
    file_djvu_wo_text = join_djvu_data_path('myfile_wo_text.djvu')
    test_txt = 'A file with non-ASCII characters, \nlike é or ç'

    @classmethod
    def setUpClass(cls):
        """Setup tests."""
        super(TestDjVuFile, cls).setUpClass()
        try:
            dp = subprocess.Popen(['djvudump'],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            stdoutdata, stderrdata = dp.communicate()
        except OSError:
            raise unittest.SkipTest('djvulibre library not installed.')

    def test_repr_method(self):
        """Test __repr__() method."""
        djvu = DjVuFile(self.file_djvu)
        expected = "pywikibot.tools.djvu.DjVuFile('%s')" % self.file_djvu
        if PY2:
            expected = expected.encode('utf-8')
        self.assertEqual(repr(djvu), expected)

    def test_str_method(self):
        """Test __str__() method."""
        djvu = DjVuFile(self.file_djvu)
        expected = "DjVuFile('%s')" % self.file_djvu
        if PY2:
            expected = expected.encode('utf-8')
        self.assertEqual(str(djvu), expected)

    def test_unicode_method(self):
        """Test __unicode__() method."""
        djvu = DjVuFile(self.file_djvu)
        expected = "DjVuFile('%s')" % self.file_djvu
        if PY2:
            self.assertEqual(unicode(djvu), expected)
        else:
            self.assertEqual(djvu.__unicode__(), expected)

    def test_file_existance(self):
        """Test file existence checks."""
        djvu = DjVuFile(self.file_djvu)
        self.assertEqual(os.path.abspath(self.file_djvu), djvu.file)
        self.assertRaises(IOError, DjVuFile, self.file_djvu_not_existing)

    def test_number_of_images(self):
        """Test page number generator."""
        djvu = DjVuFile(self.file_djvu)
        self.assertEqual(djvu.number_of_images(), 4)

    def test_page_info(self):
        """Test page info retrieval."""
        djvu = DjVuFile(self.file_djvu)
        self.assertEqual(djvu.page_info(1),
                         ('{myfile.djvu}', ('1092x221', 600)))

    def test_get_most_common_info(self):
        """Test that most common (size, dpi) are returned."""
        djvu = DjVuFile(self.file_djvu)
        self.assertEqual(djvu.get_most_common_info(), ('1092x221', 600))

    def test_has_text(self):
        """Test if djvu file contains text."""
        djvu = DjVuFile(self.file_djvu)
        self.assertTrue(djvu.has_text())
        djvu = DjVuFile(self.file_djvu_wo_text)
        self.assertFalse(djvu.has_text())

    def test_get_existing_page_number(self):
        """Test text is returned for existing page number."""
        djvu = DjVuFile(self.file_djvu)
        self.assertTrue(djvu.has_text())
        txt = djvu.get_page(1)
        self.assertEqual(txt, self.test_txt)

    def test_get_not_existing_page_number(self):
        """Test error is raised if djvu page number is out of range."""
        djvu = DjVuFile(self.file_djvu)
        self.assertTrue(djvu.has_text())
        self.assertRaises(ValueError, djvu.get_page, 100)

    def test_get_not_existing_page(self):
        """Test error is raised if djvu file has no text."""
        djvu = DjVuFile(self.file_djvu_wo_text)
        self.assertFalse(djvu.has_text())
        self.assertRaises(ValueError, djvu.get_page, 1)

    def test_whiten_not_existing_page_number(self):
        """Test djvu page cannot be whitend if page number is out of range."""
        djvu = DjVuFile(self.file_djvu)
        self.assertRaises(ValueError, djvu.whiten_page, 100)

    def test_delete_not_existing_page_number(self):
        """Test djvu page cannot be deleted if page number is out of range."""
        djvu = DjVuFile(self.file_djvu)
        self.assertRaises(ValueError, djvu.delete_page, 100)

    def test_clear_cache(self):
        """Test if djvu file contains text."""
        djvu = DjVuFile(self.file_djvu)
        self.assertTrue(djvu.has_text())
        djvu._has_text = False
        self.assertFalse(djvu.has_text())
        self.assertTrue(djvu.has_text(force=True))


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
