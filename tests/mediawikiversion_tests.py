#!/usr/bin/env python3
"""Tests for the tools.MediaWikiVersion class."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot.tools import MediaWikiVersion
from tests.aspects import TestCase


class TestMediaWikiVersion(TestCase):

    """Test MediaWikiVersion class comparisons."""

    GENERATOR_STRING_RE = 'Generator string'
    INVALID_VERSION_RE = 'Invalid version number'
    net = False

    def _make(self, version):
        """Create a MediaWikiVersion instance and check that the str stays."""
        v = MediaWikiVersion(version)
        self.assertEqual(str(v), version)
        return v

    def test_normal_versions(self):
        """Test comparison between release versions."""
        self.assertGreater(self._make('1.33'), self._make('1.32.0'))
        self.assertEqual(self._make('1.33'), self._make('1.33'))

    def test_wmf_versions(self):
        """Test comparison between wmf versions."""
        self.assertGreater(self._make('1.33wmf10'), self._make('1.33wmf9'))
        self.assertEqual(self._make('1.33wmf10'), self._make('1.33wmf10'))

    def test_combined_versions(self):
        """Test comparison between wmf versions and release versions."""
        self.assertGreater(self._make('1.33wmf10'), self._make('1.32.3'))
        self.assertGreater(self._make('1.33'), self._make('1.33wmf10'))

    def test_non_wmf_scheme(self):
        """Test version numbers not following the wmf-scheme."""
        self.assertGreater(self._make('1.33alpha'), self._make('1.32.3'))
        self.assertGreater(self._make('1.33alpha'), self._make('1.33wmf1'))
        self.assertGreater(self._make('1.33beta1'), self._make('1.33alpha'))
        self.assertGreater(self._make('1.33beta2'), self._make('1.33beta1'))
        self.assertGreater(self._make('1.33-rc.1'), self._make('1.33beta2'))
        self.assertGreater(self._make('1.33-rc.2'), self._make('1.33-rc.1'))
        self.assertGreater(self._make('1.33'), self._make('1.33-rc.2'))
        self.assertEqual(self._make('1.33rc1'), self._make('1.33-rc.1'))

    def _version_check(self, version, digits, dev_version, suffix):
        v = self._make(version)
        self.assertEqual(v.version, digits)
        self.assertEqual(v._dev_version, dev_version)
        self.assertEqual(v.suffix, suffix)

    def test_invalid_type_comparison(self):
        """Compare with a type other than a version or string."""
        self.assertNotEqual(self._make('1.32.0'), ['wrong type'])

        exc = "Comparison between 'MediaWikiVersion' and 'list' unsupported"

        with self.assertRaisesRegex(TypeError, exc):
            assert self._make('1.32.0') > ['wrong type']

    def test_interpretation(self):
        """Test if the data is correctly interpreted."""
        self._version_check('1.33', (1, 33), (4, ), '')
        self._version_check('1.33wmf1', (1, 33), (0, 1), 'wmf1')
        self._version_check('1.33alpha', (1, 33), (1, ), 'alpha')
        self._version_check('1.27.0-alpha', (1, 27, 0), (1, ), '-alpha')
        self._version_check('1.33beta1', (1, 33), (2, 1), 'beta1')
        self._version_check('1.33rc1', (1, 33), (3, 1), 'rc1')
        self._version_check('1.33-rc1', (1, 33), (3, 1), '-rc1')
        self._version_check('1.33-rc.1', (1, 33), (3, 1), '-rc.1')
        self._version_check('1.33text', (1, 33), (4, ), 'text')

    def test_invalid_versions(self):
        """Verify that insufficient version fail creating."""
        with self.assertRaisesRegex(
                ValueError,
                self.INVALID_VERSION_RE):
            MediaWikiVersion('invalid')
        with self.assertRaisesRegex(
                ValueError,
                self.INVALID_VERSION_RE):
            MediaWikiVersion('1number')
        with self.assertRaisesRegex(
                ValueError,
                self.INVALID_VERSION_RE):
            MediaWikiVersion('1.missing')
        with self.assertRaisesRegex(
                AssertionError,
                'Found \"wmf\" in \"wmf-1\"'):
            MediaWikiVersion('1.33wmf-1')

    def test_generator(self):
        """Test from_generator classmethod."""
        self.assertEqual(MediaWikiVersion.from_generator('MediaWiki 1.2.3'),
                         self._make('1.2.3'))
        with self.assertRaisesRegex(
                ValueError,
                self.GENERATOR_STRING_RE):
            MediaWikiVersion.from_generator('Invalid 1.2.3')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
