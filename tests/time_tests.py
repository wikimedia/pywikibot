#!/usr/bin/env python3
"""Tests for the Timestamp class."""
#
# (C) Pywikibot team, 2014-2023
#
# Distributed under the terms of the MIT license.
#
import calendar
import re
import unittest
from contextlib import suppress
from datetime import datetime, timedelta

from pywikibot.time import Timestamp, parse_duration, str2timedelta
from tests.aspects import TestCase


class TestTimestamp(TestCase):

    """Test Timestamp class comparisons."""

    net = False

    test_results = {
        'MW': [
            ['20090213233130', '1234567890.000000'],
        ],
        'ISO8601': [
            ['2009-02-13T23:31:30Z', '1234567890.000000'],
            ['2009-02-13T23:31:30', '1234567890.000000'],
            ['2009-02-13T23:31:30.123Z', '1234567890.123000'],
            ['2009-02-13T23:31:30.123', '1234567890.123000'],
            ['2009-02-13T23:31:30.123456Z', '1234567890.123456'],
            ['2009-02-13T23:31:30.123456', '1234567890.123456'],
            ['2009-02-13T23:31:30,123456Z', '1234567890.123456'],
            ['2009-02-13T23:31:30,123456', '1234567890.123456'],
            ['2009-02-14T00:31:30+0100', '1234567890.000000'],
            ['2009-02-13T22:31:30-0100', '1234567890.000000'],
            ['2009-02-14T00:31:30+01:00', '1234567890.000000'],
            ['2009-02-13T22:31:30-01:00', '1234567890.000000'],
            ['2009-02-13T23:41:30+00:10', '1234567890.000000'],
            ['2009-02-13T23:21:30-00:10', '1234567890.000000'],
            ['2009-02-14T00:31:30.123456+01', '1234567890.123456'],
            ['2009-02-13T22:31:30.123456-01', '1234567890.123456'],
            ['2009-02-14 00:31:30.123456+01', '1234567890.123456'],
            ['2009-02-13 22:31:30.123456-01', '1234567890.123456'],
        ],
        'POSIX': [
            ['1234567890', '1234567890.000000'],
            ['-1234567890', '-1234567890.000000'],
            ['1234567890.123', '1234567890.123000'],
            ['-1234567890.123', '-1234567890.123000'],
            ['1234567890.123456', '1234567890.123456'],
            ['-1234567890.123456', '-1234567890.123456'],
            ['1234567890.000001', '1234567890.000001'],
            ['-1234567890.000001', '-1234567890.000001'],
        ],
        'INVALID': [
            ['200902132331309999', None],
            ['2009-99-99 22:31:30.123456-01', None],
            ['1234567890.1234569999', None],
        ],
    }

    def test_set_from_timestamp(self):
        """Test creating instance from Timestamp string."""
        t1 = Timestamp.utcnow()
        t2 = Timestamp.set_timestamp(t1)
        self.assertEqual(t1, t2)
        self.assertIsInstance(t2, Timestamp)

    def test_set_from_datetime(self):
        """Test creating instance from datetime.datetime string."""
        t1 = datetime.utcnow()
        t2 = Timestamp.set_timestamp(t1)
        self.assertEqual(t1, t2)
        self.assertIsInstance(t2, datetime)

    @staticmethod
    def _compute_posix(timestr):
        """Compute POSIX timestamp with independent method."""
        sec, usec = map(int, timestr.split('.'))

        if sec < 0 < usec:
            sec -= 1
            usec = 1000000 - usec

        return datetime(1970, 1, 1) + timedelta(seconds=sec, microseconds=usec)

    def _test_set_from_string_fmt(self, fmt):
        """Test creating instance from <FMT> string."""
        for timestr, posix in self.test_results[fmt]:
            with self.subTest(timestr):
                ts = Timestamp.set_timestamp(timestr)
                self.assertEqual(ts, self._compute_posix(posix))
                self.assertEqual(ts.posix_timestamp_format(), posix)

    def test_set_from_string_mw(self):
        """Test creating instance from MW string."""
        self._test_set_from_string_fmt('MW')

    def test_set_from_string_iso8601(self):
        """Test creating instance from ISO8601 string."""
        self._test_set_from_string_fmt('ISO8601')

    def test_set_from_string_posix(self):
        """Test creating instance from POSIX string."""
        self._test_set_from_string_fmt('POSIX')

    def test_set_from_string_invalid(self):
        """Test failure creating instance from invalid string."""
        for timestr, _posix in self.test_results['INVALID']:
            regex = "time data \'[^\']*?\' does not match"
            with self.subTest(timestr), \
                 self.assertRaisesRegex(ValueError, regex):
                Timestamp.set_timestamp(timestr)

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
        sep = 'T'
        t1 = Timestamp.utcnow()
        if not t1.microsecond:  # T199179: ensure microsecond is not 0
            t1 = t1.replace(microsecond=1)
        ts1 = t1.isoformat()
        t2 = Timestamp.fromISOformat(ts1)
        ts2 = t2.isoformat()
        # MediaWiki ISO format doesn't include microseconds
        self.assertNotEqual(t1, t2)
        t1 = t1.replace(microsecond=0)
        self.assertEqual(t1, t2)
        self.assertEqual(ts1, ts2)
        date, sep, time = ts1.partition(sep)
        time = time.rstrip('Z')
        self.assertEqual(date, str(t1.date()))
        self.assertEqual(time, str(t1.time()))

    @unittest.expectedFailure
    def test_iso_format_with_sep(self):
        """Test conversion from and to ISO format with separator."""
        sep = '*'
        t1 = Timestamp.utcnow().replace(microsecond=0)
        ts1 = t1.isoformat(sep=sep)
        t2 = Timestamp.fromISOformat(ts1, sep=sep)
        ts2 = t2.isoformat(sep=sep)
        self.assertEqual(t1, t2)
        self.assertEqual(t1, t2)
        self.assertEqual(ts1, ts2)
        date, sep, time = ts1.partition(sep)
        time = time.rstrip('Z')
        self.assertEqual(date, str(t1.date()))
        self.assertEqual(time, str(t1.time()))

    def test_iso_format_property(self):
        """Test iso format properties."""
        self.assertEqual(Timestamp.ISO8601Format, Timestamp._ISO8601Format())
        self.assertEqual(re.sub(r'[\-:TZ]', '', Timestamp.ISO8601Format),
                         Timestamp.mediawikiTSFormat)

    def test_mediawiki_format(self):
        """Test conversion from and to Timestamp format."""
        t1 = Timestamp.utcnow()
        if not t1.microsecond:  # T191827: ensure microsecond is not 0
            t1 = t1.replace(microsecond=1000)
        ts1 = t1.totimestampformat()
        t2 = Timestamp.fromtimestampformat(ts1)
        ts2 = t2.totimestampformat()
        # MediaWiki timestamp format doesn't include microseconds
        self.assertNotEqual(t1, t2)
        t1 = t1.replace(microsecond=0)
        self.assertEqual(t1, t2)
        self.assertEqual(ts1, ts2)

    def test_short_mediawiki_format(self):
        """Test short mw timestamp conversion from and to Timestamp format."""
        t1 = Timestamp(2018, 12, 17)
        t2 = Timestamp.fromtimestampformat('20181217')  # short timestamp
        ts1 = t1.totimestampformat()
        ts2 = t2.totimestampformat()
        self.assertEqual(t1, t2)
        self.assertEqual(ts1, ts2)

        tests = [
            ('202211', None),
            ('2022112', None),
            ('20221127', (2022, 11, 27)),
            ('202211271', None),
            ('2022112712', None),
            ('20221127123', None),
            ('202211271234', None),
            ('2022112712345', None),
            ('20221127123456', (2022, 11, 27, 12, 34, 56)),
        ]
        for mw_ts, ts in tests:
            with self.subTest(timestamp=mw_ts):
                if ts is None:
                    with self.assertRaisesRegex(
                        ValueError,
                            f'time data {mw_ts!r} does not match MW format'):
                        Timestamp.fromtimestampformat(mw_ts)
                else:
                    self.assertEqual(Timestamp.fromtimestampformat(mw_ts),
                                     Timestamp(*ts))

        for mw_ts, ts in tests[1:-1]:
            with self.subTest(timestamp=mw_ts), self.assertRaisesRegex(
                    ValueError, f'time data {mw_ts!r} does not match MW'):
                Timestamp.fromtimestampformat(mw_ts, strict=True)

    def test_add_timedelta(self):
        """Test addin a timedelta to a Timestamp."""
        t1 = Timestamp.utcnow()
        t2 = t1 + timedelta(days=1)
        if t1.month != t2.month:
            self.assertEqual(1, t2.day)
        else:
            self.assertEqual(t1.day + 1, t2.day)
        self.assertIsInstance(t2, Timestamp)

    def test_add_timedate(self):
        """Test unsupported additions raise NotImplemented."""
        t1 = datetime.utcnow()
        t2 = t1 + timedelta(days=1)
        t3 = t1.__add__(t2)
        self.assertIs(t3, NotImplemented)

        # Now check that the pywikibot sub-class behaves the same way
        t1 = Timestamp.utcnow()
        t2 = t1 + timedelta(days=1)
        t3 = t1.__add__(t2)
        self.assertIs(t3, NotImplemented)

    def test_sub_timedelta(self):
        """Test subtracting a timedelta from a Timestamp."""
        t1 = Timestamp.utcnow()
        t2 = t1 - timedelta(days=1)
        if t1.month != t2.month:
            self.assertEqual(calendar.monthrange(t2.year, t2.month)[1], t2.day)
        else:
            self.assertEqual(t1.day - 1, t2.day)
        self.assertIsInstance(t2, Timestamp)

    def test_sub_timedate(self):
        """Test subtracting two timestamps."""
        t1 = Timestamp.utcnow()
        t2 = t1 - timedelta(days=1)
        td = t1 - t2
        self.assertIsInstance(td, timedelta)
        self.assertEqual(t2 + td, t1)


class TestTimeFunctions(TestCase):

    """Test functions in time module."""

    net = False

    def test_str2timedelta(self):
        """Test for parsing the shorthand notation of durations."""
        date = datetime(2017, 1, 1)  # non leap year
        self.assertEqual(str2timedelta('0d'), timedelta(0))
        self.assertEqual(str2timedelta('4000s'), timedelta(seconds=4000))
        self.assertEqual(str2timedelta('4000h'), timedelta(hours=4000))
        self.assertEqual(str2timedelta('7d'), str2timedelta('1w'))
        self.assertEqual(str2timedelta('3y'), timedelta(1096))
        self.assertEqual(str2timedelta('3y', date), timedelta(1095))
        with self.assertRaises(ValueError):
            str2timedelta('4000@')
        with self.assertRaises(ValueError):
            str2timedelta('$1')

    def test_parse_duration(self):
        """Test for extracting key and duration from shorthand notation."""
        self.assertEqual(parse_duration('400s'), ('s', 400))
        self.assertEqual(parse_duration('7d'), ('d', 7))
        self.assertEqual(parse_duration('3y'), ('y', 3))

        for invalid_value in ('', '3000', '4000@'):
            with self.subTest(value=invalid_value), \
                 self.assertRaises(ValueError):
                parse_duration(invalid_value)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
