# -*- coding: utf-8  -*-
"""Tests for the C{pywikibot.tools.formatter} module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#
from pywikibot.tools import formatter

from tests.aspects import unittest, TestCase


class TestListOutputter(TestCase):

    """Test ListFormatter class."""

    net = False

    def test_SequenceOutputter(self):
        """Test format method."""
        options = ['foo', 'bar']
        outputter = formatter.SequenceOutputter(options)
        self.assertEqual(outputter.format_list(), '\n  1 - foo\n  2 - bar\n')
        outputter.format_string = '({index} {width} {item})'
        self.assertEqual(outputter.format_list(), '\n(1 1 foo)\n(2 1 bar)\n')
        outputter.format_string = '{item}'
        self.assertEqual(outputter.format_list(), '\nfoo\nbar\n')


class TestColorFormat(TestCase):

    """Test color_format function in bot module."""

    net = False

    def test_no_colors(self):
        """Test without colors in template string."""
        self.assertEqual(formatter.color_format('42'), '42')
        self.assertEqual(formatter.color_format('{0}', 42), '42')
        self.assertEqual(formatter.color_format('{ans}', ans=42), '42')

    def test_colors(self):
        """Test with colors in template string."""
        self.assertEqual(formatter.color_format('{0}{black}', 42),
                         '42\03{black}')
        self.assertEqual(formatter.color_format('{ans}{black}', ans=42),
                         '42\03{black}')
        self.assertRaisesRegex(
            ValueError, r'.*conversion.*', formatter.color_format,
            '{0}{black!r}', 42)
        self.assertRaisesRegex(
            ValueError, r'.*format spec.*', formatter.color_format,
            '{0}{black:03}', 42)

    def test_marker(self):
        r"""Test that the \03 marker is only allowed in front of colors."""
        self.assertEqual(formatter.color_format('{0}\03{black}', 42),
                         '42\03{black}')
        # literal before a normal field
        self.assertRaisesRegex(
            ValueError, r'.*\\03', formatter.color_format,
            '\03{0}{black}', 42)
        # literal before a color field
        self.assertRaisesRegex(
            ValueError, r'.*\\03', formatter.color_format,
            '{0}\03before{black}', 42)

    def test_color_kwargs(self):
        """Test with a color as keyword argument."""
        self.assertRaises(ValueError,
                          formatter.color_format, '{aqua}{black}', aqua=42)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
