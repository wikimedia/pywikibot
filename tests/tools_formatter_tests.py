# -*- coding: utf-8 -*-
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
from pywikibot.tools import UnicodeMixin

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


# TODO: add tests for background colors.
class TestColorFormat(TestCase):

    """Test color_format function in bot module."""

    class DummyUnicode(UnicodeMixin):

        """Dummy class that __unicode__ returns a non-ascii unicode value."""

        def __unicode__(self):
            """Return ä."""
            return 'ä'

    net = False

    def assert_format(self, format_string, expected, *args, **kwargs):
        """Assert that color_format returns the expected string and type."""
        result = formatter.color_format(format_string, *args, **kwargs)
        self.assertEqual(result, expected)
        self.assertIsInstance(result, type(expected))

    def test_no_colors(self):
        """Test without colors in template string."""
        self.assert_format('', '')
        self.assert_format('42', '42')
        self.assert_format('{0}', '42', 42)
        self.assert_format('before {0} after', 'before 42 after', 42)
        self.assert_format('{ans}', '42', ans=42)

    def test_colors(self):
        """Test with colors in template string."""
        self.assert_format('{0}{black}', '42\03{black}', 42)
        self.assert_format('{ans}{black}', '42\03{black}', ans=42)
        self.assertRaisesRegex(
            ValueError, r'.*conversion.*', formatter.color_format,
            '{0}{black!r}', 42)
        self.assertRaisesRegex(
            ValueError, r'.*format spec.*', formatter.color_format,
            '{0}{black:03}', 42)

    def test_marker(self):
        r"""Test that the \03 marker is only allowed in front of colors."""
        self.assert_format('{0}\03{black}', '42\03{black}', 42)
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

    def test_non_ascii(self):
        """Test non-ASCII replacements."""
        self.assert_format('{0}', 'ä', 'ä')
        self.assert_format('{black}{0}', '\03{black}ä', 'ä')
        self.assert_format('{0}', 'ä', self.DummyUnicode())
        self.assert_format('{black}{0}', '\03{black}ä', self.DummyUnicode())

    def test_bytes_format(self):
        """Test that using `bytes` is not allowed."""
        self.assertRaises(TypeError, formatter.color_format, b'{0}', 'a')
        self.assertRaises(TypeError, formatter.color_format, b'{black}{0}', 'a')

    def test_variant_colors(self):
        """Test variant colors with {color} parameter."""
        self.assert_format('{0}{color}', '42\03{black}', 42, color='black')
        self.assert_format('{ans}{color}', '42\03{black}', ans=42,
                           color='black')
        self.assert_format('{color}', '42', color=42)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
