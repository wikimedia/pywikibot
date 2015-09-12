# -*- coding: utf-8  -*-
"""Tests for the date module."""
#
# (C) Pywikibot team, 2012-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from datetime import datetime

from pywikibot import date

from tests.aspects import unittest, MetaTestCaseClass, TestCase
from tests.utils import add_metaclass


class TestDateMeta(MetaTestCaseClass):

    """Date test meta class."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def test_method(formatname):

            def testMapEntry(self):
                """The test ported from date.py."""
                step = 1
                if formatname in date.decadeFormats:
                    step = 10
                try:
                    predicate, start, stop = date.formatLimits[formatname]
                except KeyError:
                    return

                for code, convFunc in date.formats[formatname].items():
                    for value in range(start, stop, step):
                        self.assertTrue(
                            predicate(value),
                            "date.formats['%s']['%s']:\ninvalid value %d"
                            % (formatname, code, value))

                        newValue = convFunc(convFunc(value))
                        self.assertEqual(
                            newValue, value,
                            "date.formats['%s']['%s']:\n"
                            "value %d does not match %s"
                            % (formatname, code, newValue, value))
            return testMapEntry

        for formatname in date.formats:
            cls.add_method(dct, 'test_' + formatname, test_method(formatname),
                           doc_suffix='using {0} format'.format(formatname))

        return super(TestDateMeta, cls).__new__(cls, name, bases, dct)


@add_metaclass
class TestDate(TestCase):

    """Test cases for date library processed by unittest."""

    __metaclass__ = TestDateMeta

    net = False


class TestMonthDelta(TestCase):

    """Tests for adding months to a date and getting the months between two."""

    net = False

    def test_apply_positive_delta(self):
        """Test adding months to a date."""
        self.assertEqual(datetime(2012, 3, 10), date.apply_month_delta(datetime(2012, 1, 10), 2))
        self.assertEqual(datetime(2012, 3, 31), date.apply_month_delta(datetime(2012, 1, 31), 2))
        self.assertEqual(datetime(2012, 2, 29), date.apply_month_delta(datetime(2012, 1, 31)))
        self.assertEqual(datetime(2012, 3, 2), date.apply_month_delta(datetime(2012, 1, 31),
                         add_overlap=True))

    def test_apply_negative_delta(self):
        """Test adding months to a date."""
        self.assertEqual(datetime(2012, 1, 10), date.apply_month_delta(datetime(2012, 3, 10), -2))
        self.assertEqual(datetime(2012, 1, 31), date.apply_month_delta(datetime(2012, 3, 31), -2))
        self.assertEqual(datetime(2012, 2, 29), date.apply_month_delta(datetime(2012, 3, 31), -1))
        self.assertEqual(datetime(2012, 3, 2), date.apply_month_delta(datetime(2012, 3, 31), -1,
                         add_overlap=True))

    def test_get_delta(self):
        """Test that the delta is calculated correctly."""
        self.assertEqual(date.get_month_delta(datetime(2012, 1, 31), datetime(2012, 3, 31)), 2)
        self.assertEqual(date.get_month_delta(datetime(2012, 3, 31), datetime(2012, 1, 31)), -2)
        self.assertEqual(date.get_month_delta(datetime(2012, 3, 31), datetime(2013, 1, 31)), 10)
        self.assertEqual(date.get_month_delta(datetime(2014, 3, 31), datetime(2013, 3, 31)), -12)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
