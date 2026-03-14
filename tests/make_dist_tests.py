#!/usr/bin/env python3
#
# (C) Pywikibot team, 2022-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for fixes module."""
from __future__ import annotations

import sys
import unittest

import make_dist
from pywikibot import __version__
from tests.aspects import TestCase


class TestMakeDist(TestCase):

    """Test the make_dist script."""

    net = False

    def test_handle_args_empty(self) -> None:
        """Test make_dist handle_args function."""
        args = make_dist.handle_args()
        self.assertEqual(args, (False, ) * 5 + ('', ))

    def test_handle_args_scripts(self) -> None:
        """Test make_dist handle_args function."""
        sys.argv += ['-local', 'scripts', '-remote']
        local, remote, clear, upgrade, scripts, msg = make_dist.handle_args()
        self.assertTrue(local)
        self.assertTrue(remote)
        self.assertFalse(clear)
        self.assertFalse(upgrade)
        self.assertTrue(scripts)
        self.assertEqual(msg, '')

    def test_handle_args(self) -> None:
        """Test make_dist handle_args function."""
        sys.argv += ['-clear', '-local', '-remote', '-upgrade']
        local, remote, clear, upgrade, scripts, msg = make_dist.handle_args()
        self.assertTrue(local)
        self.assertEqual(remote, 'dev' not in __version__)
        self.assertTrue(clear)
        self.assertTrue(upgrade)
        self.assertFalse(scripts)
        if 'dev' in __version__:
            self.assertStartsWith(
                msg,
                'Distribution must not be a developmental release to upload'
            )
        else:
            self.assertEqual(msg, '')

    def test_main(self) -> None:
        """Test main result."""
        saved_argv = sys.argv
        sys.argv = [*saved_argv, '-clear']
        self.assertTrue(make_dist.main())

        try:
            import build  # noqa: autoflake
        except ModuleNotFoundError:
            # no build or twine modules
            self.assertFalse(make_dist.main())
            sys.argv = [*saved_argv, '-local']
            self.assertFalse(make_dist.main())
            sys.argv = saved_argv


if __name__ == '__main__':
    unittest.main()
