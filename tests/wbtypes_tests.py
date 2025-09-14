#!/usr/bin/env python3
"""Tests for the Wikidata parts of the page module."""
#
# (C) Pywikibot team, 2008-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import datetime
import operator
import unittest
from contextlib import suppress
from decimal import Decimal

import pywikibot
from pywikibot.page import ItemPage, Page
from tests.aspects import WikidataTestCase


class WbRepresentationTestCase(WikidataTestCase):

    """Test methods inherited or extended from _WbRepresentation."""

    def _test_hashable(self, representation) -> None:
        """Test that the representation is hashable."""
        list_of_dupes = [representation, representation]
        self.assertLength(set(list_of_dupes), 1)


class TestWikibaseCoordinate(WbRepresentationTestCase):

    """Test Wikibase Coordinate data type."""

    dry = True

    def test_Coordinate_WbRepresentation_methods(self) -> None:
        """Test inherited or extended methods from _WbRepresentation."""
        repo = self.get_repo()
        coord = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe='moon')
        self._test_hashable(coord)

    def test_Coordinate_dim(self) -> None:
        """Test Coordinate dimension."""
        repo = self.get_repo()
        x = pywikibot.Coordinate(site=repo, lat=12.0, lon=13.0, precision=5.0)
        self.assertEqual(x.precisionToDim(), 544434)
        self.assertIsInstance(x.precisionToDim(), int)
        y = pywikibot.Coordinate(site=repo, lat=12.0, lon=13.0, dim=54444)
        self.assertEqual(y.precision, 0.500005084017101)
        self.assertIsInstance(y.precision, float)
        z = pywikibot.Coordinate(site=repo, lat=12.0, lon=13.0)
        regex = r'^No values set for dim or precision$'
        with self.assertRaisesRegex(ValueError, regex):
            z.precisionToDim()

    def test_Coordinate_plain_globe(self) -> None:
        """Test setting Coordinate globe from a plain-text value."""
        repo = self.get_repo()
        coord = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe='moon')
        self.assertEqual(coord.toWikibase(),
                         {'latitude': 12.0, 'longitude': 13.0,
                          'altitude': None, 'precision': 0,
                          'globe': 'http://www.wikidata.org/entity/Q405'})

    def test_Coordinate_entity_uri_globe(self) -> None:
        """Test setting Coordinate globe from an entity uri."""
        repo = self.get_repo()
        coord = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe_item='http://www.wikidata.org/entity/Q123')
        self.assertEqual(coord.toWikibase(),
                         {'latitude': 12.0, 'longitude': 13.0,
                          'altitude': None, 'precision': 0,
                          'globe': 'http://www.wikidata.org/entity/Q123'})


class TestWikibaseCoordinateNonDry(WbRepresentationTestCase):

    """Test Wikibase Coordinate data type (non-dry).

    These can be moved to TestWikibaseCoordinate once DrySite has been
    bumped to the appropriate version.
    """

    def test_Coordinate_item_globe(self) -> None:
        """Test setting Coordinate globe from an ItemPage."""
        repo = self.get_repo()
        coord = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe_item=ItemPage(repo, 'Q123'))
        self.assertEqual(coord.toWikibase(),
                         {'latitude': 12.0, 'longitude': 13.0,
                          'altitude': None, 'precision': 0,
                          'globe': 'http://www.wikidata.org/entity/Q123'})

    def test_Coordinate_get_globe_item_from_uri(self) -> None:
        """Test getting globe item from Coordinate with entity uri globe."""
        repo = self.get_repo()
        q = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe_item='http://www.wikidata.org/entity/Q123')
        self.assertEqual(q.get_globe_item(), ItemPage(repo, 'Q123'))

    def test_Coordinate_get_globe_item_from_itempage(self) -> None:
        """Test getting globe item from Coordinate with ItemPage globe."""
        repo = self.get_repo()
        globe = ItemPage(repo, 'Q123')
        q = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0, globe_item=globe)
        self.assertEqual(q.get_globe_item(), ItemPage(repo, 'Q123'))

    def test_Coordinate_get_globe_item_from_plain_globe(self) -> None:
        """Test getting globe item from Coordinate with plain text globe."""
        repo = self.get_repo()
        q = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0, globe='moon')
        self.assertEqual(q.get_globe_item(), ItemPage(repo, 'Q405'))

    def test_Coordinate_get_globe_item_provide_repo(self) -> None:
        """Test getting globe item from Coordinate, providing repo."""
        repo = self.get_repo()
        q = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe_item='http://www.wikidata.org/entity/Q123')
        self.assertEqual(q.get_globe_item(repo), ItemPage(repo, 'Q123'))

    def test_Coordinate_get_globe_item_different_repo(self) -> None:
        """Test getting globe item in different repo from Coordinate."""
        repo = self.get_repo()
        test_repo = pywikibot.Site('test', 'wikidata')
        q = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0,
            globe_item='http://test.wikidata.org/entity/Q123')
        self.assertEqual(q.get_globe_item(test_repo),
                         ItemPage(test_repo, 'Q123'))

    def test_Coordinate_equality(self) -> None:
        """Test Coordinate equality with different globe representations."""
        repo = self.get_repo()
        a = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0.1,
            globe='moon')
        b = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0.1,
            globe_item='http://www.wikidata.org/entity/Q405')
        c = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0.1,
            globe_item=ItemPage(repo, 'Q405'))
        d = pywikibot.Coordinate(
            site=repo, lat=12.0, lon=13.0, precision=0.1,
            globe_item='http://test.wikidata.org/entity/Q405')
        self.assertEqual(a, b)
        self.assertEqual(b, c)
        self.assertEqual(c, a)
        self.assertNotEqual(a, d)
        self.assertNotEqual(b, d)
        self.assertNotEqual(c, d)


class TestWbTime(WbRepresentationTestCase):

    """Test Wikibase WbTime data type."""

    dry = True

    def test_WbTime_WbRepresentation_methods(self) -> None:
        """Test inherited or extended methods from _WbRepresentation."""
        repo = self.get_repo()
        t = pywikibot.WbTime(site=repo, year=2010, month=0, day=0, hour=12,
                             minute=43)
        self._test_hashable(t)

    def test_WbTime_timestr(self) -> None:
        """Test timestr functions of WbTime."""
        repo = self.get_repo()
        t = pywikibot.WbTime(site=repo, year=2010, month=0, day=0, hour=12,
                             minute=43)
        self.assertEqual(t.toTimestr(), '+00000002010-00-00T12:43:00Z')
        self.assertEqual(t.toTimestr(force_iso=True), '+2010-01-01T12:43:00Z')

        t = pywikibot.WbTime(site=repo, year=2010, hour=12, minute=43)
        self.assertEqual(t.toTimestr(), '+00000002010-01-01T12:43:00Z')
        self.assertEqual(t.toTimestr(force_iso=True), '+2010-01-01T12:43:00Z')

        t = pywikibot.WbTime(site=repo, year=-2010, hour=12, minute=43)
        self.assertEqual(t.toTimestr(), '-00000002010-01-01T12:43:00Z')
        self.assertEqual(t.toTimestr(force_iso=True), '-2010-01-01T12:43:00Z')

    def test_WbTime_fromTimestr(self) -> None:
        """Test WbTime creation from UTC date/time string."""
        repo = self.get_repo()
        t = pywikibot.WbTime.fromTimestr('+00000002010-01-01T12:43:00Z',
                                         site=repo)
        self.assertEqual(t, pywikibot.WbTime(site=repo, year=2010, hour=12,
                                             minute=43, precision=14))

    def test_WbTime_zero_month(self) -> None:
        """Test WbTime creation from date/time string with zero month."""
        # ensures we support formats in T123888 / T107870
        repo = self.get_repo()
        t = pywikibot.WbTime.fromTimestr('+00000002010-00-00T12:43:00Z',
                                         site=repo)
        self.assertEqual(t, pywikibot.WbTime(site=repo, year=2010, month=0,
                                             day=0, hour=12, minute=43,
                                             precision=14))

    def test_WbTime_skip_params_precision(self) -> None:
        """Test skipping units (such as day, month) when creating WbTimes."""
        repo = self.get_repo()
        t = pywikibot.WbTime(year=2020, day=2, site=repo)
        self.assertEqual(t, pywikibot.WbTime(year=2020, month=1, day=2,
                                             site=repo))
        self.assertEqual(t.precision, pywikibot.WbTime.PRECISION['day'])
        t2 = pywikibot.WbTime(year=2020, hour=5, site=repo)
        self.assertEqual(t2, pywikibot.WbTime(year=2020, month=1, day=1,
                                              hour=5, site=repo))
        self.assertEqual(t2.precision, pywikibot.WbTime.PRECISION['hour'])
        t3 = pywikibot.WbTime(year=2020, minute=5, site=repo)
        self.assertEqual(t3, pywikibot.WbTime(year=2020, month=1, day=1,
                                              hour=0, minute=5, site=repo))
        self.assertEqual(t3.precision, pywikibot.WbTime.PRECISION['minute'])
        t4 = pywikibot.WbTime(year=2020, second=5, site=repo)
        self.assertEqual(t4, pywikibot.WbTime(year=2020, month=1, day=1,
                                              hour=0, minute=0, second=5,
                                              site=repo))
        self.assertEqual(t4.precision, pywikibot.WbTime.PRECISION['second'])
        t5 = pywikibot.WbTime(year=2020, month=2, hour=5, site=repo)
        self.assertEqual(t5, pywikibot.WbTime(year=2020, month=2, day=1,
                                              hour=5, site=repo))
        self.assertEqual(t5.precision, pywikibot.WbTime.PRECISION['hour'])
        t6 = pywikibot.WbTime(year=2020, month=2, minute=5, site=repo)
        self.assertEqual(t6, pywikibot.WbTime(year=2020, month=2, day=1,
                                              hour=0, minute=5, site=repo))
        self.assertEqual(t6.precision, pywikibot.WbTime.PRECISION['minute'])
        t7 = pywikibot.WbTime(year=2020, month=2, second=5, site=repo)
        self.assertEqual(t7, pywikibot.WbTime(year=2020, month=2, day=1,
                                              hour=0, minute=0, second=5,
                                              site=repo))
        self.assertEqual(t7.precision, pywikibot.WbTime.PRECISION['second'])
        t8 = pywikibot.WbTime(year=2020, day=2, hour=5, site=repo)
        self.assertEqual(t8, pywikibot.WbTime(year=2020, month=1, day=2,
                                              hour=5, site=repo))
        self.assertEqual(t8.precision, pywikibot.WbTime.PRECISION['hour'])
        t9 = pywikibot.WbTime(year=2020, month=3, day=2, minute=5, site=repo)
        self.assertEqual(t9, pywikibot.WbTime(year=2020, month=3, day=2,
                                              hour=0, minute=5, site=repo))
        self.assertEqual(t9.precision, pywikibot.WbTime.PRECISION['minute'])

    def test_WbTime_normalization(self) -> None:
        """Test WbTime normalization."""
        repo = self.get_repo()
        # flake8 is being annoying, so to reduce line length, I'll make
        # some aliases here
        decade = pywikibot.WbTime.PRECISION['decade']
        century = pywikibot.WbTime.PRECISION['century']
        millennium = pywikibot.WbTime.PRECISION['millennium']
        t = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                             minute=43, second=12)
        t2 = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                              minute=43, second=12,
                              precision=pywikibot.WbTime.PRECISION['second'])
        t3 = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                              minute=43, second=12,
                              precision=pywikibot.WbTime.PRECISION['minute'])
        t4 = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                              minute=43, second=12,
                              precision=pywikibot.WbTime.PRECISION['hour'])
        t5 = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                              minute=43, second=12,
                              precision=pywikibot.WbTime.PRECISION['day'])
        t6 = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                              minute=43, second=12,
                              precision=pywikibot.WbTime.PRECISION['month'])
        t7 = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                              minute=43, second=12,
                              precision=pywikibot.WbTime.PRECISION['year'])
        t8 = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                              minute=43, second=12,
                              precision=decade)
        t9 = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                              minute=43, second=12,
                              precision=century)
        t10 = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                               minute=43, second=12,
                               precision=millennium)
        t11 = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                               minute=43, second=12, timezone=-300,
                               precision=pywikibot.WbTime.PRECISION['day'])
        t12 = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                               minute=43, second=12, timezone=300,
                               precision=pywikibot.WbTime.PRECISION['day'])
        t13 = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                               minute=43, second=12, timezone=-300,
                               precision=pywikibot.WbTime.PRECISION['hour'])
        self.assertEqual(t.normalize(), t)
        self.assertEqual(t2.normalize(), t.normalize())
        self.assertEqual(t3.normalize(),
                         pywikibot.WbTime(site=repo, year=2010, month=1,
                                          day=1, hour=12, minute=43))
        self.assertEqual(t4.normalize(),
                         pywikibot.WbTime(site=repo, year=2010,
                                          month=1, day=1, hour=12))
        self.assertEqual(t5.normalize(),
                         pywikibot.WbTime(site=repo, year=2010,
                                          month=1, day=1))
        self.assertEqual(t6.normalize(),
                         pywikibot.WbTime(site=repo, year=2010,
                                          month=1))
        self.assertEqual(
            t7.normalize(), pywikibot.WbTime(site=repo, year=2010))
        self.assertEqual(t8.normalize(),
                         pywikibot.WbTime(site=repo, year=2010,
                         precision=decade))
        self.assertEqual(t9.normalize(),
                         pywikibot.WbTime(site=repo, year=2100,
                         precision=century))
        self.assertEqual(t9.normalize(),
                         pywikibot.WbTime(site=repo, year=2010,
                                          precision=century).normalize())
        self.assertEqual(t10.normalize(),
                         pywikibot.WbTime(site=repo, year=3000,
                                          precision=millennium))
        self.assertEqual(t10.normalize(),
                         pywikibot.WbTime(site=repo, year=2010,
                                          precision=millennium).normalize())
        t11_normalized = t11.normalize()
        t12_normalized = t12.normalize()
        self.assertEqual(t11_normalized.timezone, 0)
        self.assertEqual(t12_normalized.timezone, 0)
        self.assertNotEqual(t11, t12)
        self.assertEqual(t11_normalized, t12_normalized)
        self.assertEqual(t13.normalize().timezone, -300)
        # test _normalize handler functions
        self.assertEqual(pywikibot.WbTime._normalize_millennium(1301), 2000)
        self.assertEqual(pywikibot.WbTime._normalize_millennium(-1301), -2000)
        self.assertEqual(pywikibot.WbTime._normalize_century(1301), 1400)
        self.assertEqual(pywikibot.WbTime._normalize_century(-1301), -1400)
        self.assertEqual(pywikibot.WbTime._normalize_decade(1301), 1300)
        self.assertEqual(pywikibot.WbTime._normalize_decade(-1301), -1300)
        self.assertEqual(
            pywikibot.WbTime._normalize_power_of_ten(123456, 7), 123500)
        self.assertEqual(
            pywikibot.WbTime._normalize_power_of_ten(-987654, 3), -1000000)

    def test_WbTime_normalization_very_low_precision(self) -> None:
        """Test WbTime normalization with very low precision."""
        repo = self.get_repo()
        year_10000 = pywikibot.WbTime.PRECISION['10000']
        year_100000 = pywikibot.WbTime.PRECISION['100000']
        year_1000000 = pywikibot.WbTime.PRECISION['1000000']
        year_10000000 = pywikibot.WbTime.PRECISION['10000000']
        year_100000000 = pywikibot.WbTime.PRECISION['100000000']
        year_1000000000 = pywikibot.WbTime.PRECISION['1000000000']
        t = pywikibot.WbTime(site=repo, year=-3124684989,
                             precision=year_10000)
        t2 = pywikibot.WbTime(site=repo, year=-3124684989,
                              precision=year_100000)
        t3 = pywikibot.WbTime(site=repo, year=-3124684989,
                              precision=year_1000000)
        t4 = pywikibot.WbTime(site=repo, year=-3124684989,
                              precision=year_10000000)
        t5 = pywikibot.WbTime(site=repo, year=-3124684989,
                              precision=year_100000000)
        t6 = pywikibot.WbTime(site=repo, year=-3124684989,
                              precision=year_1000000000)
        self.assertEqual(t.normalize(),
                         pywikibot.WbTime(site=repo, year=-3124680000,
                         precision=year_10000))
        self.assertEqual(t2.normalize(),
                         pywikibot.WbTime(site=repo, year=-3124700000,
                                          precision=year_100000))
        self.assertEqual(t3.normalize(),
                         pywikibot.WbTime(site=repo, year=-3125000000,
                                          precision=year_1000000))
        self.assertEqual(t4.normalize(),
                         pywikibot.WbTime(site=repo, year=-3120000000,
                                          precision=year_10000000))
        self.assertEqual(t5.normalize(),
                         pywikibot.WbTime(site=repo, year=-3100000000,
                                          precision=year_100000000))
        self.assertEqual(t6.normalize(),
                         pywikibot.WbTime(site=repo, year=-3000000000,
                                          precision=year_1000000000))

    def test_WbTime_timestamp(self) -> None:
        """Test timestamp functions of WbTime."""
        repo = self.get_repo()
        timestamp = pywikibot.Timestamp.fromISOformat('2010-01-01T12:43:00Z')
        t = pywikibot.WbTime(site=repo, year=2010, month=0, day=0, hour=12,
                             minute=43)
        self.assertEqual(t.toTimestamp(), timestamp)

        # Roundtrip fails as Timestamp and WbTime interpret month=0 differently
        self.assertNotEqual(
            t, pywikibot.WbTime.fromTimestamp(timestamp, site=repo))

        t = pywikibot.WbTime(site=repo, year=2010, hour=12, minute=43)
        self.assertEqual(t.toTimestamp(), timestamp)

        t = pywikibot.WbTime(site=repo, year=-2010, hour=12, minute=43)
        regex = r'^You cannot turn BC dates into a Timestamp$'
        with self.assertRaisesRegex(ValueError, regex):
            t.toTimestamp()

        t = pywikibot.WbTime(site=repo, year=2010, month=1, day=1, hour=12,
                             minute=43, second=0)
        self.assertEqual(t.toTimestamp(), timestamp)
        self.assertEqual(
            t, pywikibot.WbTime.fromTimestamp(timestamp, site=repo))
        timezone = datetime.timezone(datetime.timedelta(hours=-5))
        ts = pywikibot.Timestamp(2020, 1, 1, 12, 43, 0, tzinfo=timezone)
        t = pywikibot.WbTime.fromTimestamp(ts, site=repo, copy_timezone=True)
        self.assertEqual(t.timezone, -5 * 60)
        t = pywikibot.WbTime.fromTimestamp(ts, site=repo, copy_timezone=True,
                                           timezone=60)
        self.assertEqual(t.timezone, 60)

        ts1 = pywikibot.Timestamp(
            year=2022, month=12, day=21, hour=13,
            tzinfo=datetime.timezone(datetime.timedelta(hours=-5)))
        t1 = pywikibot.WbTime.fromTimestamp(ts1, timezone=-300, site=repo)
        self.assertIsNotNone(t1.toTimestamp(timezone_aware=True).tzinfo)
        self.assertIsNone(t1.toTimestamp(timezone_aware=False).tzinfo)
        self.assertEqual(t1.toTimestamp(timezone_aware=True), ts1)
        self.assertNotEqual(t1.toTimestamp(timezone_aware=False), ts1)

    def test_WbTime_errors(self) -> None:
        """Test WbTime precision errors."""
        repo = self.get_repo()
        regex = '^year must be an int, not NoneType$'
        with self.assertRaisesRegex(TypeError, regex):
            pywikibot.WbTime(None, site=repo, precision=15)
        regex = "missing 1 required positional argument: 'year'"
        with self.assertRaisesRegex(TypeError, regex):
            pywikibot.WbTime(site=repo, precision=15)
        with self.assertRaisesRegex(TypeError, regex):
            pywikibot.WbTime(site=repo, precision='invalid_precision')
        regex = '^Invalid precision: "15"$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTime(site=repo, year=2020, precision=15)
        regex = '^Invalid precision: "invalid_precision"$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTime(site=repo, year=2020,
                             precision='invalid_precision')

    def test_comparison(self) -> None:
        """Test WbTime comparison."""
        repo = self.get_repo()
        t1 = pywikibot.WbTime(site=repo, year=2010, hour=12, minute=43)
        t2 = pywikibot.WbTime(site=repo, year=-2005, hour=16, minute=45)
        self.assertEqual(t1.precision, pywikibot.WbTime.PRECISION['minute'])
        self.assertEqual(t1, t1)
        self.assertGreaterEqual(t1, t1)
        self.assertGreaterEqual(t1, t2)
        self.assertGreater(t1, t2)
        self.assertEqual(t1.year, 2010)
        self.assertEqual(t2.year, -2005)
        self.assertEqual(t1.month, 1)
        self.assertEqual(t2.month, 1)
        self.assertEqual(t1.day, 1)
        self.assertEqual(t2.day, 1)
        self.assertEqual(t1.hour, 12)
        self.assertEqual(t2.hour, 16)
        self.assertEqual(t1.minute, 43)
        self.assertEqual(t2.minute, 45)
        self.assertEqual(t1.second, 0)
        self.assertEqual(t2.second, 0)
        self.assertEqual(t1.toTimestr(), '+00000002010-01-01T12:43:00Z')
        self.assertEqual(t2.toTimestr(), '-00000002005-01-01T16:45:00Z')
        with self.assertRaisesRegex(ValueError, 'Invalid precision: "15"'):
            pywikibot.WbTime(0, site=repo, precision=15)
        with self.assertRaisesRegex(ValueError,
                                    'Invalid precision: "invalid_precision"'):
            pywikibot.WbTime(0, site=repo, precision='invalid_precision')
        self.assertIsInstance(t1.toTimestamp(), pywikibot.Timestamp)
        with self.assertRaisesRegex(ValueError, 'BC dates.*Timestamp'):
            t2.toTimestamp()

    def test_comparison_types(self) -> None:
        """Test WbTime comparison with different types."""
        repo = self.get_repo()
        t1 = pywikibot.WbTime(site=repo, year=2010, hour=12, minute=43)
        t2 = pywikibot.WbTime(site=repo, year=-2005, hour=16, minute=45)
        self.assertGreater(t1, t2)
        with self.assertRaisesRegex(TypeError, 'not supported'):
            operator.lt(t1, 5)
        with self.assertRaisesRegex(TypeError, 'not supported'):
            operator.gt(t1, 5)
        with self.assertRaisesRegex(TypeError, 'not supported'):
            operator.le(t1, 5)
        with self.assertRaisesRegex(TypeError, 'not supported'):
            operator.ge(t1, 5)

    def test_comparison_timezones(self) -> None:
        """Test comparisons with timezones."""
        repo = self.get_repo()
        ts1 = pywikibot.Timestamp(
            year=2022, month=12, day=21, hour=13,
            tzinfo=datetime.timezone(datetime.timedelta(hours=-5)))
        ts2 = pywikibot.Timestamp(
            year=2022, month=12, day=21, hour=17,
            tzinfo=datetime.timezone.utc)
        self.assertGreater(ts1.timestamp(), ts2.timestamp())

        t1 = pywikibot.WbTime.fromTimestamp(ts1, timezone=-300, site=repo)
        t2 = pywikibot.WbTime.fromTimestamp(ts2, timezone=0, site=repo)
        self.assertGreater(t1, t2)

    def test_comparison_timezones_equal(self) -> None:
        """Test when two WbTime's have equal instants but not the same tz."""
        repo = self.get_repo()
        ts1 = pywikibot.Timestamp(
            year=2023, month=12, day=21, hour=13,
            tzinfo=datetime.timezone(datetime.timedelta(hours=-5)))
        ts2 = pywikibot.Timestamp(
            year=2023, month=12, day=21, hour=18,
            tzinfo=datetime.timezone.utc)
        self.assertEqual(ts1.timestamp(), ts2.timestamp())

        t1 = pywikibot.WbTime.fromTimestamp(ts1, timezone=-300, site=repo)
        t2 = pywikibot.WbTime.fromTimestamp(ts2, timezone=0, site=repo)
        self.assertGreaterEqual(t1, t2)
        self.assertGreaterEqual(t2, t1)
        self.assertNotEqual(t1, t2)
        self.assertNotEqual(t2, t1)
        # We specifically want to test the operator
        self.assertFalse(t1 > t2)
        self.assertFalse(t2 > t1)
        self.assertFalse(t1 < t2)
        self.assertFalse(t2 < t1)

    def test_comparison_equal_instant(self) -> None:
        """Test the equal_instant method."""
        repo = self.get_repo()

        ts1 = pywikibot.Timestamp(
            year=2023, month=12, day=21, hour=13,
            tzinfo=datetime.timezone(datetime.timedelta(hours=-5)))
        ts2 = pywikibot.Timestamp(
            year=2023, month=12, day=21, hour=18,
            tzinfo=datetime.timezone.utc)
        ts3 = pywikibot.Timestamp(
            year=2023, month=12, day=21, hour=19,
            tzinfo=datetime.timezone(datetime.timedelta(hours=1)))
        ts4 = pywikibot.Timestamp(
            year=2023, month=12, day=21, hour=13,
            tzinfo=datetime.timezone(datetime.timedelta(hours=-6)))

        self.assertEqual(ts1.timestamp(), ts2.timestamp())
        self.assertEqual(ts1.timestamp(), ts3.timestamp())
        self.assertEqual(ts2.timestamp(), ts3.timestamp())
        self.assertNotEqual(ts1.timestamp(), ts4.timestamp())
        self.assertNotEqual(ts2.timestamp(), ts4.timestamp())
        self.assertNotEqual(ts3.timestamp(), ts4.timestamp())

        t1 = pywikibot.WbTime.fromTimestamp(ts1, timezone=-300, site=repo)
        t2 = pywikibot.WbTime.fromTimestamp(ts2, timezone=0, site=repo)
        t3 = pywikibot.WbTime.fromTimestamp(ts3, timezone=60, site=repo)
        t4 = pywikibot.WbTime.fromTimestamp(ts4, timezone=-360, site=repo)

        self.assertTrue(t1.equal_instant(t2))
        self.assertTrue(t1.equal_instant(t3))
        self.assertTrue(t2.equal_instant(t3))
        self.assertFalse(t1.equal_instant(t4))
        self.assertFalse(t2.equal_instant(t4))
        self.assertFalse(t3.equal_instant(t4))


class TestWbQuantity(WbRepresentationTestCase):

    """Test Wikibase WbQuantity data type."""

    dry = True

    def test_WbQuantity_WbRepresentation_methods(self) -> None:
        """Test inherited or extended methods from _WbRepresentation."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=1234, error=1, site=repo)
        self._test_hashable(q)

    def test_WbQuantity_integer(self) -> None:
        """Test WbQuantity for integer value."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=1234, error=1, site=repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '+1234', 'lowerBound': '+1233',
                          'upperBound': '+1235', 'unit': '1'})
        q = pywikibot.WbQuantity(amount=5, error=(2, 3), site=repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '+5', 'lowerBound': '+2',
                          'upperBound': '+7', 'unit': '1'})
        q = pywikibot.WbQuantity(amount=0, error=(0, 0), site=repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '+0', 'lowerBound': '+0',
                          'upperBound': '+0', 'unit': '1'})
        q = pywikibot.WbQuantity(amount=-5, error=(2, 3), site=repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '-5', 'lowerBound': '-8',
                          'upperBound': '-3', 'unit': '1'})

    def test_WbQuantity_float_27(self) -> None:
        """Test WbQuantity for float value."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=0.044405586, error=0.0, site=repo)
        q_dict = {'amount': '+0.044405586', 'lowerBound': '+0.044405586',
                  'upperBound': '+0.044405586', 'unit': '1'}
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbQuantity_scientific(self) -> None:
        """Test WbQuantity for scientific notation."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount='1.3e-13', error='1e-14', site=repo)
        q_dict = {'amount': '+1.3e-13', 'lowerBound': '+1.2e-13',
                  'upperBound': '+1.4e-13', 'unit': '1'}
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbQuantity_decimal(self) -> None:
        """Test WbQuantity for decimal value."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=Decimal('0.044405586'),
                                 error=Decimal('0.0'), site=repo)
        q_dict = {'amount': '+0.044405586', 'lowerBound': '+0.044405586',
                  'upperBound': '+0.044405586', 'unit': '1'}
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbQuantity_string(self) -> None:
        """Test WbQuantity for decimal notation."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount='0.044405586', error='0', site=repo)
        q_dict = {'amount': '+0.044405586', 'lowerBound': '+0.044405586',
                  'upperBound': '+0.044405586', 'unit': '1'}
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbQuantity_formatting_bound(self) -> None:
        """Test WbQuantity formatting with bounds."""
        repo = self.get_repo()
        amount = '0.044405586'
        repr_amount = repr(Decimal(amount))
        q = pywikibot.WbQuantity(amount=amount, error='0', site=repo)
        self.assertEqual(str(q),
                         f'{{\n'
                         f'    "amount": "+{amount}",\n'
                         f'    "lowerBound": "+{amount}",\n'
                         f'    "unit": "1",\n'
                         f'    "upperBound": "+{amount}"\n'
                         f'}}')
        self.assertEqual(repr(q),
                         f'WbQuantity(amount={repr_amount}, '
                         f'upperBound={repr_amount}, '
                         f"lowerBound={repr_amount}, unit='1')")

    def test_WbQuantity_self_equality(self) -> None:
        """Test WbQuantity equality."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount='0.044405586', error='0', site=repo)
        self.assertEqual(q, q)

    def test_WbQuantity_fromWikibase(self) -> None:
        """Test WbQuantity.fromWikibase() instantiating."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity.fromWikibase({'amount': '+0.0229',
                                               'lowerBound': '0',
                                               'upperBound': '1',
                                               'unit': '1'},
                                              site=repo)
        # note that the bounds are inputted as INT but are returned as FLOAT
        self.assertEqual(q.toWikibase(),
                         {'amount': '+0.0229', 'lowerBound': '+0.0000',
                          'upperBound': '+1.0000', 'unit': '1'})

    def test_WbQuantity_errors(self) -> None:
        """Test WbQuantity error handling."""
        regex = r'^no amount given$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbQuantity(amount=None, error=1)

    def test_WbQuantity_entity_unit(self) -> None:
        """Test WbQuantity with entity uri unit."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=1234, error=1, site=repo,
                                 unit='http://www.wikidata.org/entity/Q712226')
        self.assertEqual(q.toWikibase(),
                         {'amount': '+1234', 'lowerBound': '+1233',
                          'upperBound': '+1235',
                          'unit': 'http://www.wikidata.org/entity/Q712226'})

    def test_WbQuantity_unit_fromWikibase(self) -> None:
        """Test WbQuantity recognising unit from Wikibase output."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity.fromWikibase({
            'amount': '+1234', 'lowerBound': '+1233', 'upperBound': '+1235',
            'unit': 'http://www.wikidata.org/entity/Q712226'},
            site=repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '+1234', 'lowerBound': '+1233',
                          'upperBound': '+1235',
                          'unit': 'http://www.wikidata.org/entity/Q712226'})


class TestWbQuantityNonDry(WbRepresentationTestCase):

    """Test Wikibase WbQuantity data type (non-dry).

    These can be moved to TestWbQuantity once DrySite has been bumped to
    the appropriate version.
    """

    def setUp(self) -> None:
        """Override setup to store repo and it's version."""
        super().setUp()
        self.repo = self.get_repo()

    def test_WbQuantity_unbound(self) -> None:
        """Test WbQuantity for value without bounds."""
        q = pywikibot.WbQuantity(amount=1234.5, site=self.repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '+1234.5', 'unit': '1',
                          'upperBound': None, 'lowerBound': None})

    def test_WbQuantity_formatting_unbound(self) -> None:
        """Test WbQuantity formatting without bounds."""
        amount = '0.044405586'
        q = pywikibot.WbQuantity(amount=amount, site=self.repo)
        self.assertEqual(str(q),
                         f'{{\n'
                         f'    "amount": "+{amount}",\n'
                         f'    "lowerBound": null,\n'
                         f'    "unit": "1",\n'
                         f'    "upperBound": null\n'
                         f'}}')
        self.assertEqual(repr(q),
                         f'WbQuantity(amount={Decimal(amount)!r}, '
                         f'upperBound=None, lowerBound=None, '
                         f"unit='1')")

    def test_WbQuantity_fromWikibase_unbound(self) -> None:
        """Test WbQuantity.fromWikibase() instantiating without bounds."""
        q = pywikibot.WbQuantity.fromWikibase({'amount': '+0.0229',
                                               'unit': '1'},
                                              site=self.repo)
        self.assertEqual(q.toWikibase(),
                         {'amount': '+0.0229', 'lowerBound': None,
                          'upperBound': None, 'unit': '1'})

    def test_WbQuantity_ItemPage_unit(self) -> None:
        """Test WbQuantity with ItemPage unit."""
        q = pywikibot.WbQuantity(amount=1234, error=1,
                                 unit=pywikibot.ItemPage(self.repo, 'Q712226'))
        self.assertEqual(q.toWikibase(),
                         {'amount': '+1234', 'lowerBound': '+1233',
                          'upperBound': '+1235',
                          'unit': 'http://www.wikidata.org/entity/Q712226'})

    def test_WbQuantity_equality(self) -> None:
        """Test WbQuantity equality with different unit representations."""
        a = pywikibot.WbQuantity(
            amount=1234, error=1,
            unit=pywikibot.ItemPage(self.repo, 'Q712226'))
        b = pywikibot.WbQuantity(
            amount=1234, error=1,
            unit='http://www.wikidata.org/entity/Q712226')
        c = pywikibot.WbQuantity(
            amount=1234, error=1,
            unit='http://test.wikidata.org/entity/Q712226')
        d = pywikibot.WbQuantity(
            amount=1234, error=2,
            unit='http://www.wikidata.org/entity/Q712226')
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)
        self.assertNotEqual(b, c)
        self.assertNotEqual(b, d)

    def test_WbQuantity_get_unit_item(self) -> None:
        """Test getting unit item from WbQuantity."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=1234, error=1, site=repo,
                                 unit='http://www.wikidata.org/entity/Q123')
        self.assertEqual(q.get_unit_item(),
                         ItemPage(repo, 'Q123'))

    def test_WbQuantity_get_unit_item_provide_repo(self) -> None:
        """Test getting unit item from WbQuantity, providing repo."""
        repo = self.get_repo()
        q = pywikibot.WbQuantity(amount=1234, error=1,
                                 unit='http://www.wikidata.org/entity/Q123')
        self.assertEqual(q.get_unit_item(repo),
                         ItemPage(repo, 'Q123'))

    def test_WbQuantity_get_unit_item_different_repo(self) -> None:
        """Test getting unit item in different repo from WbQuantity."""
        repo = self.get_repo()
        test_repo = pywikibot.Site('test', 'wikidata')
        q = pywikibot.WbQuantity(amount=1234, error=1, site=repo,
                                 unit='http://test.wikidata.org/entity/Q123')
        self.assertEqual(q.get_unit_item(test_repo),
                         ItemPage(test_repo, 'Q123'))


class TestWbMonolingualText(WbRepresentationTestCase):

    """Test Wikibase WbMonolingualText data type."""

    dry = True

    def test_WbMonolingualText_WbRepresentation_methods(self) -> None:
        """Test inherited or extended methods from _WbRepresentation."""
        q = pywikibot.WbMonolingualText(
            text='Test that basics work', language='en')
        self._test_hashable(q)

    def test_WbMonolingualText_string(self) -> None:
        """Test WbMonolingualText string."""
        q = pywikibot.WbMonolingualText(text='Test that basics work',
                                        language='en')
        q_dict = {'text': 'Test that basics work', 'language': 'en'}
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbMonolingualText_unicode(self) -> None:
        """Test WbMonolingualText unicode."""
        q = pywikibot.WbMonolingualText(text='Testa det här', language='sv')
        q_dict = {'text': 'Testa det här', 'language': 'sv'}
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbMonolingualText_equality(self) -> None:
        """Test WbMonolingualText equality."""
        q = pywikibot.WbMonolingualText(text='Thou shall test this!',
                                        language='en-gb')
        self.assertEqual(q, q)

    def test_WbMonolingualText_fromWikibase(self) -> None:
        """Test WbMonolingualText.fromWikibase() instantiating."""
        q = pywikibot.WbMonolingualText.fromWikibase({'text': 'Test this!',
                                                      'language': 'en'})
        self.assertEqual(q.toWikibase(),
                         {'text': 'Test this!', 'language': 'en'})

    def test_WbMonolingualText_errors(self) -> None:
        """Test WbMonolingualText error handling."""
        regex = r'^text and language cannot be empty$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbMonolingualText(text='', language='sv')
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbMonolingualText(text='Test this!', language='')
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbMonolingualText(text=None, language='sv')


class TestWbGeoShapeNonDry(WbRepresentationTestCase):

    """Test Wikibase WbGeoShape data type (non-dry).

    These require non dry tests due to the page.exists() call.
    """

    def setUp(self) -> None:
        """Set up tests."""
        self.commons = pywikibot.Site('commons')
        self.page = Page(self.commons, 'Data:Lyngby Hovedgade.map')
        super().setUp()

    def test_WbGeoShape_WbRepresentation_methods(self) -> None:
        """Test inherited or extended methods from _WbRepresentation."""
        q = pywikibot.WbGeoShape(self.page)
        self._test_hashable(q)

    def test_WbGeoShape_page(self) -> None:
        """Test WbGeoShape page."""
        q = pywikibot.WbGeoShape(self.page)
        q_val = 'Data:Lyngby Hovedgade.map'
        self.assertEqual(q.toWikibase(), q_val)

    def test_WbGeoShape_page_and_site(self) -> None:
        """Test WbGeoShape from page and site."""
        q = pywikibot.WbGeoShape(self.page, self.get_repo())
        q_val = 'Data:Lyngby Hovedgade.map'
        self.assertEqual(q.toWikibase(), q_val)

    def test_WbGeoShape_equality(self) -> None:
        """Test WbGeoShape equality."""
        q = pywikibot.WbGeoShape(self.page, self.get_repo())
        self.assertEqual(q, q)

    def test_WbGeoShape_fromWikibase(self) -> None:
        """Test WbGeoShape.fromWikibase() instantiating."""
        repo = self.get_repo()
        q = pywikibot.WbGeoShape.fromWikibase(
            'Data:Lyngby Hovedgade.map', repo)
        self.assertEqual(q.toWikibase(), 'Data:Lyngby Hovedgade.map')

    def test_WbGeoShape_error_on_non_page(self) -> None:
        """Test WbGeoShape error handling when given a non-page."""
        regex = r'^Page .+? must be a pywikibot\.Page object not a'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbGeoShape('A string', self.get_repo())

    def test_WbGeoShape_error_on_non_exitant_page(self) -> None:
        """Test WbGeoShape error handling of a non-existent page."""
        page = Page(self.commons, 'Non-existent page... really')
        regex = r'^Page \[\[.+?\]\] must exist\.$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbGeoShape(page, self.get_repo())

    def test_WbGeoShape_error_on_wrong_site(self) -> None:
        """Test WbGeoShape error handling of a page on non-filerepo site."""
        repo = self.get_repo()
        page = Page(repo, 'Q123')
        regex = r'^Page must be on the geo-shape repository site\.$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbGeoShape(page, self.get_repo())

    def test_WbGeoShape_error_on_wrong_page_type(self) -> None:
        """Test WbGeoShape error handling of a non-map page."""
        non_data_page = Page(self.commons, 'File:Foo.jpg')
        non_map_page = Page(self.commons, 'Data:TemplateData/TemplateData.tab')
        regex = (r"^Page must be in 'Data:' namespace and end in '\.map' "
                 r'for geo-shape\.$')
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbGeoShape(non_data_page, self.get_repo())
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbGeoShape(non_map_page, self.get_repo())


class TestWbTabularDataNonDry(WbRepresentationTestCase):

    """Test Wikibase WbTabularData data type (non-dry).

    These require non dry tests due to the page.exists() call.
    """

    def setUp(self) -> None:
        """Set up tests."""
        self.commons = pywikibot.Site('commons')
        self.page = Page(self.commons, 'Data:Bea.gov/GDP by state.tab')
        super().setUp()

    def test_WbTabularData_WbRepresentation_methods(self) -> None:
        """Test inherited or extended methods from _WbRepresentation."""
        q = pywikibot.WbTabularData(self.page)
        self._test_hashable(q)

    def test_WbTabularData_page(self) -> None:
        """Test WbTabularData page."""
        q = pywikibot.WbTabularData(self.page)
        q_val = 'Data:Bea.gov/GDP by state.tab'
        self.assertEqual(q.toWikibase(), q_val)

    def test_WbTabularData_page_and_site(self) -> None:
        """Test WbTabularData from page and site."""
        q = pywikibot.WbTabularData(self.page, self.get_repo())
        q_val = 'Data:Bea.gov/GDP by state.tab'
        self.assertEqual(q.toWikibase(), q_val)

    def test_WbTabularData_equality(self) -> None:
        """Test WbTabularData equality."""
        q = pywikibot.WbTabularData(self.page, self.get_repo())
        self.assertEqual(q, q)

    def test_WbTabularData_fromWikibase(self) -> None:
        """Test WbTabularData.fromWikibase() instantiating."""
        repo = self.get_repo()
        q = pywikibot.WbTabularData.fromWikibase(
            'Data:Bea.gov/GDP by state.tab', repo)
        self.assertEqual(q.toWikibase(), 'Data:Bea.gov/GDP by state.tab')

    def test_WbTabularData_error_on_non_page(self) -> None:
        """Test WbTabularData error handling when given a non-page."""
        regex = r'^Page .+? must be a pywikibot\.Page object not a'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTabularData('A string', self.get_repo())

    def test_WbTabularData_error_on_non_exitant_page(self) -> None:
        """Test WbTabularData error handling of a non-existent page."""
        page = Page(self.commons, 'Non-existent page... really')
        regex = r'^Page \[\[.+?\]\] must exist\.$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTabularData(page, self.get_repo())

    def test_WbTabularData_error_on_wrong_site(self) -> None:
        """Test WbTabularData error handling of a page on non-filerepo site."""
        repo = self.get_repo()
        page = Page(repo, 'Q123')
        regex = r'^Page must be on the tabular-data repository site\.$'
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTabularData(page, self.get_repo())

    def test_WbTabularData_error_on_wrong_page_type(self) -> None:
        """Test WbTabularData error handling of a non-map page."""
        non_data_page = Page(self.commons, 'File:Foo.jpg')
        non_map_page = Page(self.commons, 'Data:Lyngby Hovedgade.map')
        regex = (r"^Page must be in 'Data:' namespace and end in '\.tab' "
                 r'for tabular-data\.$')
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTabularData(non_data_page, self.get_repo())
        with self.assertRaisesRegex(ValueError, regex):
            pywikibot.WbTabularData(non_map_page, self.get_repo())


class TestWbUnknown(WbRepresentationTestCase):

    """Test Wikibase WbUnknown data type."""

    dry = True

    def test_WbUnknown_WbRepresentation_methods(self) -> None:
        """Test inherited or extended methods from _WbRepresentation."""
        q_dict = {'text': 'Test that basics work', 'language': 'en'}
        q = pywikibot.WbUnknown(q_dict)
        self._test_hashable(q)

    def test_WbUnknown_string(self) -> None:
        """Test WbUnknown string."""
        q_dict = {'text': 'Test that basics work', 'language': 'en'}
        q = pywikibot.WbUnknown(q_dict)
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbUnknown_equality(self) -> None:
        """Test WbUnknown equality."""
        q_dict = {'text': 'Thou shall test this!', 'language': 'unknown'}
        q = pywikibot.WbUnknown(q_dict)
        self.assertEqual(q, q)

    def test_WbUnknown_fromWikibase(self) -> None:
        """Test WbUnknown.fromWikibase() instantiating."""
        q = pywikibot.WbUnknown.fromWikibase({'text': 'Test this!',
                                              'language': 'en'})
        self.assertEqual(q.toWikibase(),
                         {'text': 'Test this!', 'language': 'en'})


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
