#!/usr/bin/env python3
#
# (C) Pywikibot team, 2024-2026
#
# Distributed under the terms of the MIT license.
#
"""Test cases for the :mod:`version` module."""
from __future__ import annotations

import time
import types
import unittest
from contextlib import suppress
from pathlib import Path, PurePosixPath, PureWindowsPath
from unittest.mock import patch

from pywikibot import version
from tests.aspects import TestCase


class LocalVersionTestCase(TestCase):

    """Test local version information."""

    net = False

    def test_nightly_version(self) -> None:
        """Test version file of nightly dump."""
        path = Path(__file__).parent / 'data'
        tag, rev, date, hsh, *dummy = version.getversion_nightly(path)
        self.assertEqual(tag, 'nightly/core_stable')
        self.assertEqual(rev, '1')
        self.assertIsInstance(date, time.struct_time)
        self.assertEqual(hsh, 'e8f64f2')
        self.assertEqual(dummy, [])

    def test_package_version(self) -> None:
        """Test package version."""
        tag, rev, date, hsh, *dummy = version.getversion_package()
        self.assertEqual(tag, 'pywikibot/__init__.py')
        self.assertEqual(rev, '-1 (unknown)')
        self.assertIsInstance(date, time.struct_time)
        self.assertEqual(hsh, '')
        self.assertEqual(dummy, [])

    def test_module_filename_path_containment(self) -> None:
        """Test module filenames are contained by path components."""
        cases = (
            (PurePosixPath,
             '/srv/pywikibot',
             '/srv/pywikibot/module.py',
             '/srv/pywikibot-extra/module.py'),
            (PureWindowsPath,
             r'C:\Users\bot\pywikibot',
             r'C:\Users\bot\pywikibot\module.py',
             r'C:\Users\bot\pywikibot-extra\module.py'),
            (PureWindowsPath,
             r'\\server\share\pywikibot',
             r'\\server\share\pywikibot\module.py',
             r'\\server\share\pywikibot-extra\module.py'),
        )

        for path_type, program_dir, module_path, sibling_path in cases:
            module = types.SimpleNamespace(__file__=module_path)
            with self.subTest(path_type=path_type,
                              program_dir=program_dir), \
                    patch.object(version, 'Path', path_type), \
                    patch.object(version, '_get_program_dir',
                                 return_value=program_dir), \
                    patch.object(version.os.path, 'exists',
                                 return_value=True):
                self.assertEqual(version.get_module_filename(module),
                                 module_path)

                module.__file__ = sibling_path
                self.assertIsNone(version.get_module_filename(module))


class RemoteVersionTestCase(TestCase):

    """Test remote version information."""

    net = True

    def test_onlinerepo_version(self) -> None:
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
