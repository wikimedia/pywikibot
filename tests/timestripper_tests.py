# -*- coding: utf-8  -*-
"""Tests for archivebot.py/Timestripper."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import datetime

import pywikibot
from tests.utils import PywikibotTestCase, unittest
from pywikibot.textlib import TimeStripper, tzoneFixedOffset


class TestTimeStripperWithNoDigitsAsMonths(PywikibotTestCase):

    """Test cases for TimeStripper methods."""

    def setUp(self):
        site = pywikibot.Site('fr', 'wikipedia')
        self.ts = TimeStripper(site)
        super(TestTimeStripperWithNoDigitsAsMonths, self).setUp()

    def test_findmarker(self):
        """Test that string which is not part of text is found."""
        txt = u'this is a string with a maker is @@@@already present'
        self.assertEqual(self.ts.findmarker(txt, base=u'@@', delta='@@'),
                         '@@@@@@')

    def test_last_match_and_replace(self):
        """Test that pattern matches and removes items correctly."""
        txtWithOneMatch = u'this string has 3000, 1999 and 3000 in it'
        txtWithTwoMatch = u'this string has 1998, 1999 and 3000 in it'
        txtWithNoMatch = u'this string has no match'
        pat = self.ts.pyearR

        self.assertEqual(self.ts.last_match_and_replace(txtWithOneMatch, pat),
                         (u'this string has 3000, @@ and 3000 in it',
                          {'year': u'1999'})
                         )
        self.assertEqual(self.ts.last_match_and_replace(txtWithTwoMatch, pat),
                         (u'this string has @@, @@ and 3000 in it',
                          {'year': u'1999'})
                         )
        self.assertEqual(self.ts.last_match_and_replace(txtWithNoMatch, pat),
                         (txtWithNoMatch,
                          None)
                         )

        txtWithOneMatch = u'this string has XXX, YYY and février in it'
        txtWithTwoMatch = u'this string has XXX, mars and février in it'
        txtWithThreeMatch = u'this string has avr, mars and février in it'
        txtWithNoMatch = u'this string has no match'
        pat = self.ts.pmonthR

        self.assertEqual(self.ts.last_match_and_replace(txtWithOneMatch, pat),
                         (u'this string has XXX, YYY and @@ in it',
                          {'month': u'février'})
                         )
        self.assertEqual(self.ts.last_match_and_replace(txtWithTwoMatch, pat),
                         (u'this string has XXX, @@ and @@ in it',
                          {'month': u'février'})
                         )
        self.assertEqual(self.ts.last_match_and_replace(txtWithThreeMatch, pat),
                         (u'this string has @@, @@ and @@ in it',
                          {'month': u'février'})
                         )
        self.assertEqual(self.ts.last_match_and_replace(txtWithNoMatch, pat),
                         (txtWithNoMatch,
                          None)
                         )

    def test_timestripper(self):
        """Test that correct date is matched."""
        txtMatch = u'3 février 2010 à 19:48 (CET) 7 février 2010 à 19:48 (CET)'
        txtNoMatch = u'3 March 2010 19:48 (CET) 7 March 2010 19:48 (CET)'
        txtHourInRange = u'7 février 2010 à 23:00 (CET)'
        txtHourOutOfRange = u'7 février 2010 à 24:00 (CET)'

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        res = datetime.datetime(2010, 2, 7, 19, 48, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)

        self.assertNotEqual(self.ts.timestripper(txtHourInRange), None)
        self.assertEqual(self.ts.timestripper(txtHourOutOfRange), None)


class TestTimeStripperWithDigitsAsMonths(PywikibotTestCase):

    """Test cases for TimeStripper methods."""

    def setUp(self):
        site = pywikibot.Site('cs', 'wikipedia')
        self.ts = TimeStripper(site)
        super(TestTimeStripperWithDigitsAsMonths, self).setUp()

    def test_last_match_and_replace(self):
        """Test that pattern matches and removes items correctly."""
        txtWithOneMatch = u'this string has XX. YY. 12. in it'
        txtWithTwoMatch = u'this string has XX. 1. 12. in it'
        txtWithThreeMatch = u'this string has 1. 1. 12. in it'
        txtWithNoMatch = u'this string has no match'
        pat = self.ts.pmonthR

        self.assertEqual(self.ts.last_match_and_replace(txtWithOneMatch, pat),
                         (u'this string has XX. YY. 12. in it',
                          {'month': u'12.'})
                         )
        self.assertEqual(self.ts.last_match_and_replace(txtWithTwoMatch, pat),
                         (u'this string has XX. 1. 12. in it',
                          {'month': u'12.'})
                         )
        self.assertEqual(self.ts.last_match_and_replace(txtWithThreeMatch, pat),
                         (u'this string has @@ 1. 12. in it',
                          {'month': u'12.'})
                         )
        self.assertEqual(self.ts.last_match_and_replace(txtWithNoMatch, pat),
                         (txtWithNoMatch,
                          None)
                         )

    def test_timestripper(self):
        txtMatch = u'3. 2. 2010, 19:48 (UTC) 7. 2. 2010 19:48 (UTC)'
        txtNoMatch = u'3 March 2010 19:48 (UTC) 7 March 2010 19:48 (UTC)'

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        res = datetime.datetime(2010, 2, 7, 19, 48, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)


class TestEnglishTimeStripper(PywikibotTestCase):

    """Test cases for English language."""

    def setUp(self):
        site = pywikibot.Site('en', 'wikipedia')
        self.ts = TimeStripper(site)
        super(TestEnglishTimeStripper, self).setUp()

    def test_timestripper(self):
        """Test that correct date is matched."""
        txtMatch = u'3 February 2010 19:48 (UTC) 7 February 2010 19:48 (UTC)'
        txtNoMatch = u'3. 2. 2010, 19:48 (UTC) 7. 2. 2010 19:48 (UTC)'

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        res = datetime.datetime(2010, 2, 7, 19, 48, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)


class TestCzechTimeStripper(PywikibotTestCase):

    """Test cases for Czech language."""

    def setUp(self):
        site = pywikibot.Site('cs', 'wikipedia')
        self.ts = TimeStripper(site)
        super(TestCzechTimeStripper, self).setUp()

    def test_timestripper(self):
        """Test that correct date is matched."""
        txtMatch = u'3. 2. 2010, 19:48 (UTC) 7. 2. 2010 19:48 (UTC)'
        txtNoMatch = u'3 March 2010 19:48 (UTC) 7 March 2010 19:48 (UTC)'

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        res = datetime.datetime(2010, 2, 7, 19, 48, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)


class TestPortugueseTimeStripper(PywikibotTestCase):

    """Test cases for Portuguese language."""

    def setUp(self):
        site = pywikibot.Site('pt', 'wikipedia')
        self.ts = TimeStripper(site)
        super(TestPortugueseTimeStripper, self).setUp()

    def test_timestripper(self):
        """Test that correct date is matched."""
        txtMatch = u'19h48min de 3 de fevereiro de 2010‎ (UTC) 19h48min de 7 de fevereiro de 2010‎ (UTC)'
        txtNoMatch = u'3 March 2010 19:48 (UTC) 7 March 2010 19:48 (UTC)'

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        res = datetime.datetime(2010, 2, 7, 19, 48, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)


class TestNorwegianTimeStripper(PywikibotTestCase):

    """Test cases for Norwegian language."""

    def setUp(self):
        site = pywikibot.Site('no', 'wikipedia')
        self.ts = TimeStripper(site)
        super(TestNorwegianTimeStripper, self).setUp()

    def test_timestripper(self):
        """Test that correct date is matched."""
        txtMatch = u'3. feb 2010 kl. 19:48 (CET) 7. feb 2010 kl. 19:48 (UTC)'
        txtNoMatch = u'3 March 2010 19:48 (UTC) 7 March 2010 19:48 (UTC)'

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        res = datetime.datetime(2010, 2, 7, 19, 48, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)


class TestVietnameseTimeStripper(PywikibotTestCase):

    """Test cases for Vietnamese language."""

    def setUp(self):
        site = pywikibot.Site('vi', 'wikipedia')
        self.ts = TimeStripper(site)
        super(TestVietnameseTimeStripper, self).setUp()

    def test_timestripper_01(self):
        """Test that correct date is matched."""
        txtMatch = u'16:41, ngày 15 tháng 9 năm 2008 (UTC) 16:41, ngày 12 tháng 9 năm 2008 (UTC)'
        txtNoMatch = u'16:41, ngày 15 March 9 năm 2008 (UTC) 16:41, ngày 12 March 9 năm 2008 (UTC)'

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        res = datetime.datetime(2008, 9, 12, 16, 41, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)

    def test_timestripper_02(self):
        """Test that correct date is matched."""
        txtMatch = u'21:18, ngày 13 tháng 8 năm 2014 (UTC) 21:18, ngày 14 tháng 8 năm 2014 (UTC)'
        txtNoMatch = u'21:18, ngày 13 March 8 năm 2014 (UTC) 21:18, ngày 14 March 8 năm 2014 (UTC)'

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        res = datetime.datetime(2014, 8, 14, 21, 18, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
