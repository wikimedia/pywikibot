#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Test cases for the :mod:`config` module."""
from __future__ import annotations

import sys
import unittest
from contextlib import suppress
from pathlib import Path, PurePosixPath, PureWindowsPath
from tempfile import TemporaryDirectory
from unittest.mock import patch
from zipfile import ZipFile

from pywikibot import config
from pywikibot.family import Family
from tests.aspects import TestCase


class ConfigPathTestCase(TestCase):

    """Test configuration path helpers."""

    net = False

    def test_register_families_zip(self) -> None:
        """Discover and load archived families without duplicate paths."""
        with TemporaryDirectory() as tmp, \
                patch.dict(config.family_files, {}, clear=True), \
                patch.dict(Family._families, {}, clear=True), \
                patch.dict(sys.modules), \
                patch.object(sys, 'path', sys.path.copy()):
            archive = Path(tmp) / 'families.zip'
            folder = archive / 'families'
            expected = {}
            with ZipFile(archive, 'w') as zip_file:
                for name in ('zipalpha', 'zipbeta'):
                    filename = name + '_family.py'
                    zip_file.writestr(
                        'families/' + filename,
                        'from pywikibot.family import Family as BaseFamily\n'
                        'class Family(BaseFamily):\n'
                        f'    name = {name!r}\n'
                        "    langs = {'en': 'example.invalid'}\n")
                    expected[name] = str(folder / filename)
                zip_file.writestr('other/unused_family.py', '')

            config.register_families_folder(folder, not_exists_ok=True)
            self.assertEqual(config.family_files, expected)
            for name in expected:
                self.assertEqual(Family.load(name).name, name)
            self.assertEqual(sys.path.count(str(folder)), 1)

            config.register_families_folder(archive)
            expected['unused'] = str(archive / 'other/unused_family.py')
            self.assertEqual(config.family_files, expected)

    def test_register_families_missing_folder(self) -> None:
        """Retain missing-folder and non-directory error handling."""
        with TemporaryDirectory() as tmp, \
                patch.dict(config.family_files, {}, clear=True):
            archive = Path(tmp) / 'families.zip'
            with ZipFile(archive, 'w') as zip_file:
                zip_file.writestr('families/example_family.py', '')
            for folder in (Path(tmp) / 'missing', archive / 'missing'):
                with self.subTest(folder=folder):
                    with self.assertRaises(FileNotFoundError):
                        config.register_families_folder(folder)
                    config.register_families_folder(folder,
                                                    not_exists_ok=True)
            file_path = Path(tmp) / 'plain.txt'
            file_path.touch()
            with self.assertRaises(NotADirectoryError):
                config.register_families_folder(file_path)
            self.assertEqual(config.family_files, {})

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
