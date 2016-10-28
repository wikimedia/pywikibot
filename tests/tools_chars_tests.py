#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test tools.chars package."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import unicodedata

from distutils.version import StrictVersion

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
        # Cn are undefined characters (and were defined later in Unicode)
        for char in chars._category_cf:
            cat = unicodedata.category(char)
            if cat not in ('Cf', 'Cn'):
                invalid[char] = cat
        if StrictVersion(unicodedata.unidata_version) < StrictVersion('6.3'):
            # This category has changed with Unicode 6.3 to Cf
            self.assertEqual(invalid.pop('\u180e'), 'Zs')
        self.assertCountEqual(invalid.items(), [])


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
