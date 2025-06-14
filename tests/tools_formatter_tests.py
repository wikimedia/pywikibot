#!/usr/bin/env python3
"""Tests for the ``pywikibot.tools.formatter`` module."""
#
# (C) Pywikibot team, 2015-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest
from contextlib import suppress

from pywikibot.tools import formatter
from tests.aspects import TestCase


class TestListOutputter(TestCase):

    """Test ListFormatter class."""

    net = False

    def test_SequenceOutputter(self) -> None:
        """Test format method."""
        options = ['foo', 'bar']
        outputter = formatter.SequenceOutputter(options)
        self.assertEqual(outputter.out, '\n  1 - foo\n  2 - bar\n')
        outputter.format_string = '({index} {width} {item})'
        self.assertEqual(outputter.out, '\n(1 1 foo)\n(2 1 bar)\n')
        outputter.format_string = '{item}'
        self.assertEqual(outputter.out, '\nfoo\nbar\n')


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
