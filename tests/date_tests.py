#!/usr/bin/env python3
"""Tests for the date module."""
#
# (C) Pywikibot team, 2012-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress
from datetime import datetime

from pywikibot import date
from tests.aspects import MetaTestCaseClass, TestCase


class DateTestMeta(MetaTestCaseClass):

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

                for code, convert in date.formats[formatname].items():
                    for value in range(start, stop, step):
                        self.assertTrue(
                            predicate(value),
                            "date.formats['{}']['{}']:\ninvalid value {}"
                            .format(formatname, code, value))

                        new_value = convert(convert(value))
                        self.assertEqual(
                            new_value, value,
                            "date.formats['{}']['{}']:\n"
                            'value {} does not match {}'
                            .format(formatname, code, new_value, value))
            return testMapEntry

        for formatname in date.formats:
            cls.add_method(dct, 'test_' + formatname, test_method(formatname),
                           doc_suffix=f'using {formatname} format')

        return super().__new__(cls, name, bases, dct)


class TestDate(TestCase, metaclass=DateTestMeta):

    """Test cases for date library processed by unittest."""

    net = False


class TestMonthName(TestCase):

    """Test MonthName format."""

    net = True

    def test_month_name_formats(self):
        """Test MonthName format for codes retrieved via MediaWiki message."""
        formatname = 'MonthName'
        for code in date.formats['Cat_BirthsAD']:
            convert = date.formats[formatname][code]
            predicate, start, stop = date.formatLimits[formatname]
            for value in range(start, stop):
                with self.subTest(code=code, month=value):
                    self.assertTrue(
                        predicate(value),
                        "date.formats['{}']['{}']:\ninvalid value {}"
                        .format(formatname, code, value))

                    new_value = convert(convert(value))
                    self.assertEqual(
                        new_value, value,
                        "date.formats['{}']['{}']:\n"
                        'value {} does not match {}'
                        .format(formatname, code, new_value, value))

    def test_month_name(self):
        """Test some MonthName results."""
        # T273573
        self.assertEqual(date.formats['MonthName']['hu']('január'), 1)
        self.assertEqual(date.formats['MonthName']['hu'](5), 'május')


class TestMonthDelta(TestCase):

    """Tests for adding months to a date and getting the months between two."""

    net = False

    def test_apply_positive_delta(self):
        """Test adding months to a date."""
        self.assertEqual(datetime(2012, 3, 10),
                         date.apply_month_delta(datetime(2012, 1, 10), 2))
        self.assertEqual(datetime(2012, 3, 31),
                         date.apply_month_delta(datetime(2012, 1, 31), 2))
        self.assertEqual(datetime(2012, 2, 29),
                         date.apply_month_delta(datetime(2012, 1, 31)))
        self.assertEqual(datetime(2012, 3, 2),
                         date.apply_month_delta(datetime(2012, 1, 31),
                         add_overlap=True))

    def test_apply_negative_delta(self):
        """Test adding months to a date."""
        self.assertEqual(datetime(2012, 1, 10),
                         date.apply_month_delta(datetime(2012, 3, 10), -2))
        self.assertEqual(datetime(2012, 1, 31),
                         date.apply_month_delta(datetime(2012, 3, 31), -2))
        self.assertEqual(datetime(2012, 2, 29),
                         date.apply_month_delta(datetime(2012, 3, 31), -1))
        self.assertEqual(datetime(2012, 3, 2),
                         date.apply_month_delta(datetime(2012, 3, 31), -1,
                         add_overlap=True))

    def test_get_delta(self):
        """Test that the delta is calculated correctly."""
        self.assertEqual(date.get_month_delta(datetime(2012, 1, 31),
                         datetime(2012, 3, 31)), 2)
        self.assertEqual(date.get_month_delta(datetime(2012, 3, 31),
                         datetime(2012, 1, 31)), -2)
        self.assertEqual(date.get_month_delta(datetime(2012, 3, 31),
                         datetime(2013, 1, 31)), 10)
        self.assertEqual(date.get_month_delta(datetime(2014, 3, 31),
                         datetime(2013, 3, 31)), -12)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
