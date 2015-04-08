# -*- coding: utf-8  -*-
"""Test cases for the WikiStats dataset."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import sys

from pywikibot.data.wikistats import WikiStats, csv

from tests.aspects import unittest, TestCase

if sys.version_info[0] == 3:
    basestring = (str, )


class WikiStatsTestCase(TestCase):

    """Test WikiStats dump."""

    sites = {
        'wikistats': {
            'hostname': 'wikistats.wmflabs.org',
        },
    }

    def test_sort(self):
        ws = WikiStats()
        data = ws.sorted('wikipedia', 'total')
        top = data[0]
        self.assertIn('prefix', top)
        self.assertIn('total', top)
        self.assertEqual(top['prefix'], 'en')
        self.assertIsInstance(top['total'], basestring)
        self.assertEqual(ws.languages_by_size('wikipedia')[0], 'en')
        self.assertEqual(ws.languages_by_size('wikisource')[0], 'fr')

    def test_csv(self):
        if not csv:
            raise unittest.SkipTest('unicodecsv not installed.')
        ws = WikiStats()
        data = ws.get_dict('wikipedia', 'csv')
        self.assertIsInstance(data, dict)
        self.assertIn('en', data)
        self.assertIn('ht', data)
        self.assertGreater(int(data['en']['total']), 4000000)
        data = ws.get_dict

    def test_xml(self):
        ws = WikiStats()
        data = ws.get_dict('wikisource', 'xml')
        self.assertIsInstance(data, dict)
        self.assertIn('en', data)
        self.assertIn('id', data)
        self.assertGreater(int(data['fr']['total']), 1600000)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
