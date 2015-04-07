# -*- coding: utf-8  -*-
"""Tests for the tools.MediaWikiVersion class."""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'


from pywikibot.tools import MediaWikiVersion as V

from tests.aspects import unittest, TestCase


class TestMediaWikiVersion(TestCase):

    """Test MediaWikiVersion class comparisons."""

    net = False

    def _make(self, version):
        """Create a MediaWikiVersion instance and check that the str stays."""
        v = V(version)
        self.assertEqual(str(v), version)
        return v

    def test_normal_versions(self):
        """Test comparison between release versions."""
        self.assertGreater(self._make('1.23'), self._make('1.22.0'))
        self.assertTrue(self._make('1.23') == self._make('1.23'))
        self.assertEqual(self._make('1.23'), self._make('1.23'))

    def test_wmf_versions(self):
        """Test comparison between wmf versions."""
        self.assertGreater(self._make('1.23wmf10'), self._make('1.23wmf9'))
        self.assertEqual(self._make('1.23wmf10'), self._make('1.23wmf10'))

    def test_combined_versions(self):
        """Test comparison between wmf versions and release versions."""
        self.assertGreater(self._make('1.23wmf10'), self._make('1.22.3'))
        self.assertGreater(self._make('1.23'), self._make('1.23wmf10'))

    def test_non_wmf_scheme(self):
        """Test version numbers not following the wmf-scheme."""
        self.assertGreater(self._make('1.23alpha'), self._make('1.22.3'))
        self.assertGreater(self._make('1.23alpha'), self._make('1.23wmf1'))
        self.assertGreater(self._make('1.23beta1'), self._make('1.23alpha'))
        self.assertGreater(self._make('1.23beta2'), self._make('1.23beta1'))
        self.assertGreater(self._make('1.23-rc.1'), self._make('1.23beta2'))
        self.assertGreater(self._make('1.23-rc.2'), self._make('1.23-rc.1'))
        self.assertGreater(self._make('1.23'), self._make('1.23-rc.2'))
        self.assertEqual(self._make('1.23rc1'), self._make('1.23-rc.1'))

    def _version_check(self, version, digits, dev_version, suffix):
        v = self._make(version)
        self.assertEqual(v.version, digits)
        self.assertEqual(v._dev_version, dev_version)
        self.assertEqual(v.suffix, suffix)

    def test_interpretation(self):
        """Test if the data is correctly interpreted."""
        self._version_check('1.23', (1, 23), (4, ), '')
        self._version_check('1.23wmf1', (1, 23), (0, 1), 'wmf1')
        self._version_check('1.23alpha', (1, 23), (1, ), 'alpha')
        self._version_check('1.23beta1', (1, 23), (2, 1), 'beta1')
        self._version_check('1.23rc1', (1, 23), (3, 1), 'rc1')
        self._version_check('1.23-rc1', (1, 23), (3, 1), '-rc1')
        self._version_check('1.23-rc.1', (1, 23), (3, 1), '-rc.1')

    def test_invalid_versions(self):
        """Verify that insufficient version fail creating."""
        self.assertRaises(ValueError, V, 'invalid')
        self.assertRaises(ValueError, V, '1number')
        self.assertRaises(ValueError, V, '1.missing')
        self.assertRaises(ValueError, V, '1.23wmf-1')
        self.assertRaises(ValueError, V, '1.23text')


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
