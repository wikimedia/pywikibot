#!/usr/bin/env python3
"""Tests for the ``pywikibot.tools.formatter`` module."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot.tools import formatter
from tests.aspects import DeprecationTestCase, TestCase


class TestListOutputter(TestCase):

    """Test ListFormatter class."""

    net = False

    def test_SequenceOutputter(self):
        """Test format method."""
        options = ['foo', 'bar']
        outputter = formatter.SequenceOutputter(options)
        self.assertEqual(outputter.out, '\n  1 - foo\n  2 - bar\n')
        outputter.format_string = '({index} {width} {item})'
        self.assertEqual(outputter.out, '\n(1 1 foo)\n(2 1 bar)\n')
        outputter.format_string = '{item}'
        self.assertEqual(outputter.out, '\nfoo\nbar\n')


class TestColorFormat(DeprecationTestCase):

    """Test color_format function in bot module."""

    class DummyUnicode:

        """Dummy class that __str__ returns a non-ASCII Unicode value."""

        def __str__(self):
            """Return ä."""
            return 'ä'

    net = False

    def assert_format(self, format_string, expected, *args, **kwargs):
        """Assert that color_format returns the expected string and type."""
        result = formatter.color_format(format_string, *args, **kwargs)
        self.assertEqual(result, expected)
        self.assertIsInstance(result, type(expected))
        self.assertOneDeprecation()

    def test_no_colors(self):
        """Test without colors in template string."""
        self.assert_format('', '')
        self.assert_format('42', '42')
        self.assert_format('{0}', '42', 42)
        self.assert_format('before {0} after', 'before 42 after', 42)
        self.assert_format('{ans}', '42', ans=42)

    def test_colors(self):
        """Test with colors in template string."""
        self.assert_format('{0}{black}', '42<<black>>', 42)
        self.assert_format('{ans}{black}', '42<<black>>', ans=42)
        with self.assertRaisesRegex(ValueError, r'.*conversion.*'):
            formatter.color_format('{0}{black!r}', 42)
        with self.assertRaisesRegex(ValueError, r'.*format spec.*'):
            formatter.color_format('{0}{black:03}', 42)

    def test_marker(self):
        r"""Test that the \03 marker is only allowed in front of colors."""
        self.assert_format('{0}\03{black}', '42<<black>>', 42)
        # literal before a normal field
        with self.assertRaisesRegex(ValueError, r'.*\\03'):
            formatter.color_format('\03{0}{black}', 42)
        # literal before a color field
        with self.assertRaisesRegex(ValueError, r'.*\\03'):
            formatter.color_format('{0}\03before{black}', 42)

    def test_color_kwargs(self):
        """Test with a color as keyword argument."""
        with self.assertRaises(ValueError):
            formatter.color_format('{aqua}{black}', aqua=42)

    def test_non_ascii(self):
        """Test non-ASCII replacements."""
        self.assert_format('{0}', 'ä', 'ä')
        self.assert_format('{black}{0}', '<<black>>ä', 'ä')
        self.assert_format('{0}', 'ä', self.DummyUnicode())
        self.assert_format('{black}{0}', '<<black>>ä', self.DummyUnicode())

    def test_bytes_format(self):
        """Test that using `bytes` is not allowed."""
        with self.assertRaises(TypeError):
            formatter.color_format(b'{0}', 'a')
        with self.assertRaises(TypeError):
            formatter.color_format(b'{black}{0}', 'a')

    def test_variant_colors(self):
        """Test variant colors with {color} parameter."""
        self.assert_format('{0}{color}', '42<<black>>', 42, color='black')
        self.assert_format('{ans}{color}', '42<<black>>', ans=42,
                           color='black')
        self.assert_format('{color}', '42', color=42)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
