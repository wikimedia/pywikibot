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


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
