# -*- coding: utf-8  -*-
"""Tests for the Timestamp class."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import calendar
import datetime

from pywikibot import Timestamp as T

from tests.aspects import unittest, TestCase


class TestTimestamp(TestCase):

    """Test Timestamp class comparisons."""

    net = False

    def test_clone(self):
        t1 = T.utcnow()
        t2 = t1.clone()
        self.assertEqual(t1, t2)
        self.assertIsInstance(t2, T)

    def test_instantiate_from_instance(self):
        """Test passing instance to factory methods works."""
        t1 = T.utcnow()
        self.assertIsNot(t1, T.fromISOformat(t1))
        self.assertEqual(t1, T.fromISOformat(t1))
        self.assertIsInstance(T.fromISOformat(t1), T)
        self.assertIsNot(t1, T.fromtimestampformat(t1))
        self.assertEqual(t1, T.fromtimestampformat(t1))
        self.assertIsInstance(T.fromtimestampformat(t1), T)

    def test_iso_format(self):
        t1 = T.utcnow()
        ts1 = t1.toISOformat()
        t2 = T.fromISOformat(ts1)
        ts2 = t2.toISOformat()
        # MediaWiki ISO format doesn't include microseconds
        self.assertNotEqual(t1, t2)
        t1 = t1.replace(microsecond=0)
        self.assertEqual(t1, t2)
        self.assertEqual(ts1, ts2)

    def test_mediawiki_format(self):
        t1 = T.utcnow()
        ts1 = t1.totimestampformat()
        t2 = T.fromtimestampformat(ts1)
        ts2 = t2.totimestampformat()
        # MediaWiki timestamp format doesn't include microseconds
        self.assertNotEqual(t1, t2)
        t1 = t1.replace(microsecond=0)
        self.assertEqual(t1, t2)
        self.assertEqual(ts1, ts2)

    def test_add_timedelta(self):
        t1 = T.utcnow()
        t2 = t1 + datetime.timedelta(days=1)
        if t1.month != t2.month:
            self.assertEqual(1, t2.day)
        else:
            self.assertEqual(t1.day + 1, t2.day)
        self.assertIsInstance(t2, T)

    def test_add_timedate(self):
        """Test unsupported additions raise NotImplemented."""
        t1 = datetime.datetime.utcnow()
        t2 = t1 + datetime.timedelta(days=1)
        t3 = t1.__add__(t2)
        self.assertIs(t3, NotImplemented)

        # Now check that the pywikibot sub-class behaves the same way
        t1 = T.utcnow()
        t2 = t1 + datetime.timedelta(days=1)
        t3 = t1.__add__(t2)
        self.assertIs(t3, NotImplemented)

    def test_sub_timedelta(self):
        t1 = T.utcnow()
        t2 = t1 - datetime.timedelta(days=1)
        if t1.month != t2.month:
            self.assertEqual(calendar.monthrange(t2.year, t2.month)[1], t2.day)
        else:
            self.assertEqual(t1.day - 1, t2.day)
        self.assertIsInstance(t2, T)

    def test_sub_timedate(self):
        t1 = T.utcnow()
        t2 = t1 - datetime.timedelta(days=1)
        td = t1 - t2
        self.assertIsInstance(td, datetime.timedelta)
        self.assertEqual(t2 + td, t1)

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
