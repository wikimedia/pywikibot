#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Test cases for the :mod:`config` module."""
from __future__ import annotations

import unittest
from contextlib import suppress
from pathlib import Path, PurePosixPath, PureWindowsPath
from unittest.mock import patch

from pywikibot import config
from tests.aspects import TestCase


class ConfigPathTestCase(TestCase):

    """Test configuration path helpers."""

    net = False

    def test_shortpath_path_containment(self) -> None:
        """Test shortpath uses path components for containment."""
        base_dir = Path.cwd() / 'pywikibot'
        child = base_dir / 'data' / 'file.txt'
        sibling = base_dir.with_name(base_dir.name + '-extra') / 'file.txt'

        with patch.object(config, 'base_dir', str(base_dir)):
            self.assertEqual(config.shortpath(str(base_dir)), '')
            self.assertEqual(config.shortpath(str(child)),
                             str(Path('data') / 'file.txt'))
            self.assertEqual(config.shortpath(str(sibling)), str(sibling))

    def test_shortpath_path_flavours(self) -> None:
        """Test POSIX, Windows drive, and Windows UNC path handling."""
        cases = (
            (PurePosixPath,
             '/srv/pywikibot',
             '/srv/pywikibot/data/file.txt',
             '/srv/pywikibot-extra/file.txt',
             'data/file.txt'),
            (PureWindowsPath,
             r'C:\Users\bot\pywikibot',
             r'C:\Users\bot\pywikibot\data\file.txt',
             r'C:\Users\bot\pywikibot-extra\file.txt',
             r'data\file.txt'),
            (PureWindowsPath,
             r'\\server\share\pywikibot',
             r'\\server\share\pywikibot\data\file.txt',
             r'\\server\share\pywikibot-extra\file.txt',
             r'data\file.txt'),
        )

        for path_type, base, child, sibling, relative_child in cases:
            with self.subTest(path_type=path_type, base=base), \
                    patch.object(config, 'Path', path_type), \
                    patch.object(config, 'base_dir', base):
                self.assertEqual(config.shortpath(base), '')
                self.assertEqual(config.shortpath(child), relative_child)
                self.assertEqual(config.shortpath(sibling), sibling)

    def test_shortpath_different_windows_drive(self) -> None:
        """Test paths on another Windows drive are not shortened."""
        base = r'C:\Users\bot\pywikibot'
        path = r'D:\pywikibot\file.txt'
        with patch.object(config, 'Path', PureWindowsPath), \
                patch.object(config, 'base_dir', base):
            self.assertEqual(config.shortpath(path), path)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
