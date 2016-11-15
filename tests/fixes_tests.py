# -*- coding: utf-8 -*-
"""Tests for fixes module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import fixes

from tests import unittest, join_data_path
from tests.aspects import TestCase


class TestFixes(TestCase):

    """Test the fixes module."""

    net = False

    def setUp(self):
        """Backup the current fixes."""
        super(TestFixes, self).setUp()
        self._old_fixes = fixes.fixes

    def tearDown(self):
        """Recover the current fixes."""
        fixes.fixes = self._old_fixes
        super(TestFixes, self).tearDown()

    def test_overwrite_value(self):
        """Test loading a fix file overwriting the fixes."""
        fixes.fixes = {}
        old_fixes = fixes.fixes
        fixes._load_file(join_data_path('set-fixes.py'))
        self.assertIsNot(fixes.fixes, old_fixes)

    def test_update_value(self):
        """Test loading a fix file changing the fixes."""
        fixes.fixes = {}
        old_fixes = fixes.fixes
        fixes._load_file(join_data_path('fixes.py'))
        self.assertIs(fixes.fixes, old_fixes)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
