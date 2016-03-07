# -*- coding: utf-8  -*-
"""Test cases for the WikiStats dataset."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

from pywikibot.data.wikistats import WikiStats, csv
from pywikibot.tools import UnicodeType

from tests.aspects import unittest, TestCase


class WikiStatsTestCase(TestCase):

    """Test WikiStats dump."""

    hostname = 'https://wikistats.wmflabs.org/api.php'

    def test_sort(self):
        """Test sorted results."""
        ws = WikiStats()
        data = ws.sorted('wikipedia', 'total')
        top = data[0]
        self.assertIn('prefix', top)
        self.assertIn('total', top)
        self.assertEqual(top['prefix'], 'en')
        self.assertTrue(all(isinstance(key, UnicodeType)
                            for key in top.keys()
                            if key is not None))
        self.assertIsInstance(top['total'], UnicodeType)
        self.assertEqual(ws.languages_by_size('wikipedia')[0], 'en')
        self.assertEqual(ws.languages_by_size('wikisource')[0], 'fr')

    def test_csv(self):
        """Test CSV."""
        if not csv:
            raise unittest.SkipTest('unicodecsv not installed.')
        ws = WikiStats()
        data = ws.get_dict('wikipedia', 'csv')
        self.assertIsInstance(data, dict)
        self.assertIn('en', data)
        self.assertIn('ht', data)
        self.assertGreater(int(data['en']['total']), 4000000)
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
        self.assertGreater(int(data['fr']['total']), 1600000)
        data = data['fr']
        self.assertTrue(all(isinstance(key, UnicodeType)
                            for key in data.keys()
                            if key is not None))
        self.assertIsInstance(data['total'], UnicodeType)
        self.assertIn('prefix', data)
        self.assertIn('total', data)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
