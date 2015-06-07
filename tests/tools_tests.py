#!/usr/bin/python
"""Test tools package alone which don't fit into other tests."""
# -*- coding: utf-8  -*-
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
from __future__ import unicode_literals

__version__ = '$Id$'

import os.path
import subprocess

from pywikibot import tools

from tests import _data_dir
from tests.aspects import unittest, TestCase

_xml_data_dir = os.path.join(_data_dir, 'xml')


class ContextManagerWrapperTestCase(TestCase):

    """Test that ContextManagerWrapper is working correctly."""

    class DummyClass(object):

        """A dummy class which has some values and a close method."""

        class_var = 42

        def __init__(self):
            """Create instance with dummy values."""
            self.instance_var = 1337
            self.closed = False

        def close(self):
            """Just store that it has been closed."""
            self.closed = True

    net = False

    def test_wrapper(self):
        """Create a test instance and verify the wrapper redirects."""
        obj = self.DummyClass()
        wrapped = tools.ContextManagerWrapper(obj)
        self.assertIs(wrapped.class_var, obj.class_var)
        self.assertIs(wrapped.instance_var, obj.instance_var)
        self.assertIs(wrapped._wrapped, obj)
        self.assertFalse(obj.closed)
        with wrapped as unwrapped:
            self.assertFalse(obj.closed)
            self.assertIs(unwrapped, obj)
            unwrapped.class_var = 47
        self.assertTrue(obj.closed)
        self.assertEqual(wrapped.class_var, 47)

    def test_exec_wrapper(self):
        """Check that the wrapper permits exceptions."""
        wrapper = tools.ContextManagerWrapper(self.DummyClass())
        self.assertFalse(wrapper.closed)
        with self.assertRaises(ZeroDivisionError):
            with wrapper:
                1 / 0
        self.assertTrue(wrapper.closed)


class OpenCompressedTestCase(TestCase):

    """
    Unit test class for tools.

    The tests for open_compressed requires that article-pyrus.xml* contain all
    the same content after extraction. The content itself is not important.
    The file article-pyrus.xml_invalid.7z is not a valid 7z file and
    open_compressed will fail extracting it using 7za.
    """

    net = False

    @classmethod
    def setUpClass(cls):
        """Define base_file and original_content."""
        super(OpenCompressedTestCase, cls).setUpClass()
        cls.base_file = os.path.join(_xml_data_dir, 'article-pyrus.xml')
        with open(cls.base_file, 'rb') as f:
            cls.original_content = f.read()

    @staticmethod
    def _get_content(*args):
        """Use open_compressed and return content using a with-statement."""
        with tools.open_compressed(*args) as f:
            return f.read()

    def test_open_compressed_normal(self):
        """Test open_compressed with no compression in the standard library."""
        self.assertEqual(self._get_content(self.base_file), self.original_content)

    def test_open_compressed_bz2(self):
        """Test open_compressed with bz2 compressor in the standard library."""
        self.assertEqual(self._get_content(self.base_file + '.bz2'), self.original_content)
        self.assertEqual(self._get_content(self.base_file + '.bz2', True), self.original_content)

    def test_open_compressed_gz(self):
        """Test open_compressed with gz compressor in the standard library."""
        self.assertEqual(self._get_content(self.base_file + '.gz'), self.original_content)

    def test_open_compressed_7z(self):
        """Test open_compressed with 7za if installed."""
        try:
            subprocess.Popen(['7za'], stdout=subprocess.PIPE).stdout.close()
        except OSError:
            raise unittest.SkipTest('7za not installed')
        self.assertEqual(self._get_content(self.base_file + '.7z'), self.original_content)
        self.assertRaises(OSError, self._get_content, self.base_file + '_invalid.7z', True)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
