#!/usr/bin/env python3
#
# (C) Pywikibot team, 2008-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the tools.MediaWikiVersion class."""
from __future__ import annotations

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

    def test_normal_versions(self) -> None:
        """Test comparison between release versions."""
        self.assertGreater(self._make('1.43'), self._make('1.42.0'))
        self.assertEqual(self._make('1.43'), self._make('1.43'))

    def test_wmf_versions(self) -> None:
        """Test comparison between wmf versions."""
        self.assertGreater(self._make('1.43wmf10'), self._make('1.43wmf9'))
        self.assertEqual(self._make('1.43wmf10'), self._make('1.43wmf10'))

    def test_combined_versions(self) -> None:
        """Test comparison between wmf versions and release versions."""
        self.assertGreater(self._make('1.43wmf10'), self._make('1.42.3'))
        self.assertGreater(self._make('1.43'), self._make('1.43wmf10'))

    def test_non_wmf_scheme(self) -> None:
        """Test version numbers not following the wmf-scheme."""
        self.assertGreater(self._make('1.43alpha'), self._make('1.42.3'))
        self.assertGreater(self._make('1.43alpha'), self._make('1.43wmf1'))
        self.assertGreater(self._make('1.43beta1'), self._make('1.43alpha'))
        self.assertGreater(self._make('1.43beta2'), self._make('1.43beta1'))
        self.assertGreater(self._make('1.43-rc.1'), self._make('1.43beta2'))
        self.assertGreater(self._make('1.43-rc.2'), self._make('1.43-rc.1'))
        self.assertGreater(self._make('1.43'), self._make('1.43-rc.2'))
        self.assertEqual(self._make('1.43rc1'), self._make('1.43-rc.1'))

    def _version_check(self, version, digits, dev_version, suffix) -> None:
        v = self._make(version)
        self.assertEqual(v.version, digits)
        self.assertEqual(v._dev_version, dev_version)
        self.assertEqual(v.suffix, suffix)

    def test_invalid_type_comparison(self) -> None:
        """Compare with a type other than a version or string."""
        self.assertNotEqual(self._make('1.42.0'), ['wrong type'])

        exc = "Comparison between 'MediaWikiVersion' and 'list' unsupported"

        with self.assertRaisesRegex(TypeError, exc):
            assert self._make('1.42.0') > ['wrong type']

    def test_interpretation(self) -> None:
        """Test if the data is correctly interpreted."""
        self._version_check('1.43', (1, 43), (4, ), '')
        self._version_check('1.43wmf1', (1, 43), (0, 1), 'wmf1')
        self._version_check('1.43alpha', (1, 43), (1, ), 'alpha')
        self._version_check('1.27.0-alpha', (1, 27, 0), (1, ), '-alpha')
        self._version_check('1.43beta1', (1, 43), (2, 1), 'beta1')
        self._version_check('1.45-beta.1', (1, 45), (2, 1), '-beta.1')
        self._version_check('1.43rc1', (1, 43), (3, 1), 'rc1')
        self._version_check('1.43-rc1', (1, 43), (3, 1), '-rc1')
        self._version_check('1.43-rc.1', (1, 43), (3, 1), '-rc.1')
        self._version_check('1.45-rc-1', (1, 45), (3, 1), '-rc-1')
        self._version_check('1.43text', (1, 43), (4, ), 'text')

    def test_invalid_versions(self) -> None:
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
                ValueError,
                'Found "wmf" in "wmf-1"'):
            MediaWikiVersion('1.43wmf-1')

    def test_generator(self) -> None:
        """Test from_generator classmethod."""
        self.assertEqual(MediaWikiVersion.from_generator('MediaWiki 1.2.3'),
                         self._make('1.2.3'))
        with self.assertRaisesRegex(
                ValueError,
                self.GENERATOR_STRING_RE):
            MediaWikiVersion.from_generator('Invalid 1.2.3')


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
