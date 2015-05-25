#!/usr/bin/python
"""Test tools.chars package."""
# -*- coding: utf-8  -*-
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
from __future__ import unicode_literals

__version__ = '$Id$'

import sys
import unicodedata

from pywikibot.tools import chars

from tests.aspects import unittest, TestCase


class CharsTestCase(TestCase):

    """General test case testing the module."""

    net = False

    def test_replace(self):
        """Test replace_invisible."""
        self.assertEqual(chars.replace_invisible('Hello world!'), 'Hello world!')
        self.assertEqual(chars.replace_invisible('\u200eRTL\u200f'), '<200e>RTL<200f>')

    def test_contains(self):
        """Test contains_invisible."""
        self.assertFalse(chars.contains_invisible('Hello world!'))
        self.assertTrue(chars.contains_invisible('\u200eRTL\u200f'))

    def test_category_cf(self):
        """Test that all characters in _category_cf are actually in Cf."""
        invalid = {}
        for char in chars._category_cf:
            cat = unicodedata.category(char)
            if cat != 'Cf':
                invalid[char] = cat
        if sys.version_info[0] == 2:
            # These weren't defined in Unicode 5.2 (which is what Py2 is using)
            self.assertEqual(invalid.pop('\u0604'), 'Cn')
            self.assertEqual(invalid.pop('\u061c'), 'Cn')
            self.assertEqual(invalid.pop('\u2066'), 'Cn')
            self.assertEqual(invalid.pop('\u2067'), 'Cn')
            self.assertEqual(invalid.pop('\u2068'), 'Cn')
            self.assertEqual(invalid.pop('\u2069'), 'Cn')
            # This category has changed between Unicode 6 and 7 to Cf
            self.assertEqual(invalid.pop('\u180e'), 'Zs')
        self.assertCountEqual(invalid.items(), [])


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
