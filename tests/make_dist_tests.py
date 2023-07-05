#!/usr/bin/env python3
"""Tests for fixes module."""
#
# (C) Pywikibot team, 2022-2023
#
# Distributed under the terms of the MIT license.
#
import sys
import unittest

from pywikibot import __version__
from tests.aspects import TestCase, require_modules


@require_modules('dataclasses')  # Python 3.7+
class TestMakeDist(TestCase):

    """Test the make_dist script."""

    net = False

    def test_handle_args_empty(self):
        """Test make_dist handle_args function."""
        from make_dist import handle_args
        args = handle_args()
        self.assertEqual(args, (False, ) * 4)

    def test_handle_args(self):
        """Test make_dist handle_args function."""
        from make_dist import handle_args
        sys.argv += ['-clear', '-local', '-remote', '-upgrade']
        local, remote, clear, upgrade = handle_args()
        self.assertTrue(local)
        self.assertEqual(remote, 'dev' not in __version__)
        self.assertTrue(clear)
        self.assertTrue(upgrade)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
