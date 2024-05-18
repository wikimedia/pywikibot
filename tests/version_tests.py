#!/usr/bin/env python3
"""Test cases for the :mod:`version` module."""
#
# (C) Pywikibot team, 2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import time
import unittest
from contextlib import suppress
from pathlib import Path

from pywikibot import version
from tests.aspects import TestCase


class LocalVersionTestCase(TestCase):

    """Test local version infomation."""

    net = False

    def test_nightly_version(self):
        """Test version file of nightly dump."""
        path = Path(__file__).parent / 'data'
        tag, rev, date, hsh, *dummy = version.getversion_nightly(path)
        self.assertEqual(tag, 'nightly/core_stable')
        self.assertEqual(rev, '1')
        self.assertIsInstance(date, time.struct_time)
        self.assertEqual(hsh, 'e8f64f2')
        self.assertEqual(dummy, [])

    def test_package_version(self):
        """Test package version."""
        tag, rev, date, hsh, *dummy = version.getversion_package()
        self.assertEqual(tag, 'pywikibot/__init__.py')
        self.assertEqual(rev, '-1 (unknown)')
        self.assertIsInstance(date, time.struct_time)
        self.assertEqual(hsh, '')
        self.assertEqual(dummy, [])


class RemoteVersionTestCase(TestCase):

    """Test remote version infomation."""

    net = True

    def test_onlinerepo_version(self):
        """Test online repository hash."""
        for branch in ('master', 'stable'):
            with self.subTest(branch=branch):
                hsh = version.getversion_onlinerepo('branches/' + branch)
                try:
                    int(hsh, 16)
                except ValueError:  # pragma: no cover
                    self.fail(
                        f'{hsh!r} is not a valid hash of {branch} branch')


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
