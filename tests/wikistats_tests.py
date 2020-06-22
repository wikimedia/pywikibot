# -*- coding: utf-8 -*-
"""Test cases for the WikiStats dataset."""
#
# (C) Pywikibot team, 2014-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import sys

from pywikibot.data.wikistats import WikiStats, csv
from pywikibot.tools import UnicodeType

from tests.aspects import unittest, TestCase


class WikiStatsTestCase(TestCase):

    """Test WikiStats dump."""

    hostname = 'https://wikistats.wmflabs.org/api.php'

    def test_sort(self):
        """Test sorted results."""
        keys = ('good', 'prefix', 'total')

        ws = WikiStats()
        data = ws.sorted('wikipedia', 'total')
        top = data[0]
        bottom = data[-1]

        for key in keys:
            with self.subTest(key=key):
                self.assertIn(key, top)
                self.assertIn(key, bottom)

        self.assertTrue(all(isinstance(key, UnicodeType)
                            for key in top.keys()
                            if key is not None))
        self.assertIsInstance(top['good'], UnicodeType)
        self.assertIsInstance(top['total'], UnicodeType)
        self.assertIsInstance(bottom['good'], UnicodeType)
        self.assertIsInstance(bottom['total'], UnicodeType)

        self.assertGreater(int(top['total']), int(bottom['good']))
        self.assertGreater(int(top['good']), int(bottom['good']))
        self.assertGreater(int(top['total']), int(bottom['total']))

    def test_sorting_order(self):
        """Test sorting order of languages_by_size."""
        family = 'wikipedia'
        ws = WikiStats()
        data = ws.get_dict(family)
        last = sys.maxsize
        last_code = ''
        for code in ws.languages_by_size(family):
            curr = int(data[code]['good'])
            self.assertGreaterEqual(
                last, curr,
                '{} ({}) is greater than {} ({}).'
                .format(code, curr, last_code, last))
            last = curr
            last_code = code

    def test_csv(self):
        """Test CSV."""
        if not csv:
            self.skipTest('unicodecsv not installed.')
        ws = WikiStats()
        data = ws.get_dict('wikipedia', 'csv')
        self.assertIsInstance(data, dict)
        self.assertIn('en', data)
        self.assertIn('ht', data)
        self.assertGreater(int(data['en']['total']), int(data['en']['good']))
        data = data['en']
        self.assertTrue(all(isinstance(key, UnicodeType)
                            for key in data.keys()
                            if key is not None))
        self.assertIsInstance(data['total'], UnicodeType)
        self.assertIn('prefix', data)
        self.assertIn('total', data)

    def test_xml(self):
        """Test XML."""
        ws = WikiStats()
        data = ws.get_dict('wikisource', 'xml')
        self.assertIsInstance(data, dict)
        self.assertIn('en', data)
        self.assertIn('id', data)
        self.assertGreater(int(data['fr']['total']), int(data['fr']['good']))
        data = data['fr']
        self.assertTrue(all(isinstance(key, UnicodeType)
                            for key in data.keys()
                            if key is not None))
        self.assertIsInstance(data['total'], UnicodeType)
        self.assertIn('prefix', data)
        self.assertIn('total', data)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
