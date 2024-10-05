#!/usr/bin/env python3
"""Tests for fixes module."""
#
# (C) Pywikibot team, 2022-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import sys
import unittest

import make_dist
from pywikibot import __version__
from tests.aspects import TestCase


class TestMakeDist(TestCase):

    """Test the make_dist script."""

    net = False

    def test_handle_args_empty(self):
        """Test make_dist handle_args function."""
        args = make_dist.handle_args()
        self.assertEqual(args, (False, ) * 5)

    def test_handle_args_scripts(self):
        """Test make_dist handle_args function."""
        sys.argv += ['-local', 'scripts', '-remote']
        local, remote, clear, upgrade, scripts = make_dist.handle_args()
        self.assertTrue(local)
        self.assertEqual(remote, 'dev' not in __version__)
        self.assertFalse(clear)
        self.assertFalse(upgrade)
        self.assertTrue(scripts)

    def test_handle_args(self):
        """Test make_dist handle_args function."""
        sys.argv += ['-clear', '-local', '-remote', '-upgrade']
        local, remote, clear, upgrade, scripts = make_dist.handle_args()
        self.assertTrue(local)
        self.assertEqual(remote, 'dev' not in __version__)
        self.assertTrue(clear)
        self.assertTrue(upgrade)
        self.assertFalse(scripts)

    def test_main(self):
        """Test main result."""
        saved_argv = sys.argv
        sys.argv = [*saved_argv, '-clear']
        self.assertTrue(make_dist.main())

        # no build or twine modules
        self.assertFalse(make_dist.main())
        sys.argv = [*saved_argv, '-local']
        self.assertFalse(make_dist.main())
        sys.argv = saved_argv


if __name__ == '__main__':
    unittest.main()
