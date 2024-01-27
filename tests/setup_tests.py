#!/usr/bin/env python3
"""Test setup.py.

.. versionadded:: 9.0
"""
#
# (C) Pywikibot team, 2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest

import pywikibot
import setup

from tests.aspects import TestCase


class TestSetup(TestCase):

    """Test setup.py functions."""

    site = False
    net = False

    def test_get_validated_version(self):
        """Test :func:`setup.get_validated_version` function."""
        self.assertEqual(setup.get_validated_version(), pywikibot.__version__)

    def test_read_desc(self):
        """Test :func:`setup.read_desc` function."""
        desc = setup.read_desc('README.rst')
        coc = setup.read_desc('CODE_OF_CONDUCT.rst')
        self.assertIn(coc, desc)

    def test_get_pywikibot_packages(self):
        """Test :func:`setup.get_packages` function for pywikibot."""
        name = 'pywikibot'
        packages = setup.get_packages(name)
        self.assertEqual(packages[0], name)
        self.assertIn(name + '.scripts', packages)
        self.assertLength(packages, 14)

    def test_get_tests_packages(self):
        """Test :func:`setup.get_packages` function for tests."""
        name = 'tests'
        packages = setup.get_packages(name)
        self.assertEqual(packages[0], name)
        self.assertIn(name + '.data', packages)
        self.assertLength(packages, 10)

    def test_get_scripts_packages(self):
        """Test :func:`setup.get_packages` function for scripts."""
        name = 'scripts'
        packages = setup.get_packages(name)
        self.assertEqual(packages[0], name)
        self.assertIn(name + '.userscripts', packages)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
