# -*- coding: utf-8 -*-
"""Tests for the Timestamp class."""
#
# (C) Pywikibot team, 2014-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import calendar
import datetime

from pywikibot import Timestamp

from tests.aspects import unittest, TestCase


class TestTimestamp(TestCase):

    """Test Timestamp class comparisons."""

    net = False

    def test_clone(self):
        """Test cloning a Timestamp instance."""
        t1 = Timestamp.utcnow()
        t2 = t1.clone()
        self.assertEqual(t1, t2)
        self.assertIsInstance(t2, Timestamp)

    def test_instantiate_from_instance(self):
        """Test passing instance to factory methods works."""
        t1 = Timestamp.utcnow()
        self.assertIsNot(t1, Timestamp.fromISOformat(t1))
        self.assertEqual(t1, Timestamp.fromISOformat(t1))
        self.assertIsInstance(Timestamp.fromISOformat(t1), Timestamp)
        self.assertIsNot(t1, Timestamp.fromtimestampformat(t1))
        self.assertEqual(t1, Timestamp.fromtimestampformat(t1))
        self.assertIsInstance(Timestamp.fromtimestampformat(t1), Timestamp)

    def test_iso_format(self):
        """Test conversion from and to ISO format."""
        t1 = Timestamp.utcnow()
        ts1 = t1.isoformat()
        t2 = Timestamp.fromISOformat(ts1)
        ts2 = t2.isoformat()
        # MediaWiki ISO format doesn't include microseconds
        self.assertNotEqual(t1, t2)
        t1 = t1.replace(microsecond=0)
        self.assertEqual(t1, t2)
        self.assertEqual(ts1, ts2)

    def test_mediawiki_format(self):
        """Test conversion from and to timestamp format."""
        t1 = Timestamp.utcnow()
        ts1 = t1.totimestampformat()
        t2 = Timestamp.fromtimestampformat(ts1)
        ts2 = t2.totimestampformat()
        # MediaWiki timestamp format doesn't include microseconds
        self.assertNotEqual(t1, t2)
        t1 = t1.replace(microsecond=0)
        self.assertEqual(t1, t2)
        self.assertEqual(ts1, ts2)

    def test_add_timedelta(self):
        """Test addin a timedelta to a Timestamp."""
        t1 = Timestamp.utcnow()
        t2 = t1 + datetime.timedelta(days=1)
        if t1.month != t2.month:
            self.assertEqual(1, t2.day)
        else:
            self.assertEqual(t1.day + 1, t2.day)
        self.assertIsInstance(t2, Timestamp)

    def test_add_timedate(self):
        """Test unsupported additions raise NotImplemented."""
        t1 = datetime.datetime.utcnow()
        t2 = t1 + datetime.timedelta(days=1)
        t3 = t1.__add__(t2)
        self.assertIs(t3, NotImplemented)

        # Now check that the pywikibot sub-class behaves the same way
        t1 = Timestamp.utcnow()
        t2 = t1 + datetime.timedelta(days=1)
        t3 = t1.__add__(t2)
        self.assertIs(t3, NotImplemented)

    def test_sub_timedelta(self):
        """Test substracting a timedelta from a Timestamp."""
        t1 = Timestamp.utcnow()
        t2 = t1 - datetime.timedelta(days=1)
        if t1.month != t2.month:
            self.assertEqual(calendar.monthrange(t2.year, t2.month)[1], t2.day)
        else:
            self.assertEqual(t1.day - 1, t2.day)
        self.assertIsInstance(t2, Timestamp)

    def test_sub_timedate(self):
        """Test subtracting two timestamps."""
        t1 = Timestamp.utcnow()
        t2 = t1 - datetime.timedelta(days=1)
        td = t1 - t2
        self.assertIsInstance(td, datetime.timedelta)
        self.assertEqual(t2 + td, t1)

if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
