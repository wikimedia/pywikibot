#!/usr/bin/env python3
#
# (C) Pywikibot team, 2024-2026
#
# Distributed under the terms of the MIT license.
#
"""Test setup.py."""
from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from packaging.requirements import Requirement
from packaging.version import Version

import pywikibot
import setup
from tests.aspects import TestCase


class TestSetup(TestCase):

    """Test setup.py functions."""

    site = False
    net = False

    def test_read_project(self) -> None:
        """Test :func:`setup.read_project` function."""
        self.assertEqual(setup.read_project(), 'pywikibot')

    def test_get_validated_version(self) -> None:
        """Test :func:`setup.get_validated_version` function."""
        self.assertEqual(setup.get_validated_version('pywikibot'),
                         pywikibot.__version__)

    @patch('subprocess.run')
    def test_get_validated_version_uses_latest_tag(self, mock_run) -> None:
        """Test that version validation uses the latest repository tag."""
        version = Version(pywikibot.__version__)
        newer_version = f'{version.major + 1}.0.0'
        older_version = f'{max(version.major - 1, 0)}.0.0'
        mock_run.return_value.stdout = (
            f'not-a-version\n{newer_version}\n{older_version}\n'
        )

        with patch.object(sys, 'argv', ['setup.py', 'sdist']):
            with patch('builtins.print') as mock_print:
                with self.assertRaisesRegex(
                        SystemExit,
                        r'Build of distribution package canceled'):
                    setup.get_validated_version('pywikibot')

        mock_print.assert_any_call(
            f'\n\nNew version {str(version)!r} is not higher than last '
            f'version {newer_version!r}.'
        )

    def test_requirements_file(self) -> None:
        """Test that pip requirements use valid dependency specifiers."""
        with open(setup.path / 'requirements.txt') as f:
            lines = [line.partition('#')[0].strip() for line in f]

        for requirement in lines:
            if requirement and not requirement.startswith('-'):
                with self.subTest(requirement=requirement):
                    Requirement(requirement)

    def test_all_no_gui_extra(self) -> None:
        """Test that the all-no-gui extra excludes only Tkinter."""
        expected = {
            requirement
            for name, requirements in setup.extra_deps.items()
            if name not in {'all-no-gui', 'Tkinter'}
            for requirement in requirements
        }
        self.assertSetEqual(set(setup.extra_deps['all-no-gui']), expected)
        self.assertNotIn(
            'pillow',
            {Requirement(requirement).name.lower()
             for requirement in setup.extra_deps['all-no-gui']},
        )

    def test_read_desc(self) -> None:
        """Test :func:`setup.read_desc` function."""
        desc = setup.read_desc('README.rst')
        coc = setup.read_desc('CODE_OF_CONDUCT.rst')
        self.assertIn(coc, desc)

    def test_get_pywikibot_packages(self) -> None:
        """Test :func:`setup.get_packages` function for pywikibot."""
        name = 'pywikibot'
        packages = setup.get_packages(name)
        self.assertEqual(packages[0], name)
        self.assertIn(name + '.scripts', packages)
        self.assertLength(packages, 14)

    def test_get_tests_packages(self) -> None:
        """Test :func:`setup.get_packages` function for tests."""
        name = 'tests'
        packages = setup.get_packages(name)
        self.assertEqual(packages[0], name)
        self.assertIn(name + '.data', packages)
        self.assertLength(packages, 11)

    def test_get_scripts_packages(self) -> None:
        """Test :func:`setup.get_packages` function for scripts."""
        name = 'scripts'
        packages = setup.get_packages(name)
        self.assertEqual(packages[0], name)
        self.assertIn(name + '.userscripts', packages)


if __name__ == '__main__':
    unittest.main()
