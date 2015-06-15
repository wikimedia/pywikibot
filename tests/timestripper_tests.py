# -*- coding: utf-8  -*-
"""Tests for archivebot.py/Timestripper."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import datetime

from pywikibot.textlib import TimeStripper, tzoneFixedOffset
from tests.aspects import unittest, TestCase


class TestTimeStripperWithNoDigitsAsMonths(TestCase):

    """Test cases for TimeStripper methods."""

    family = 'wikipedia'
    code = 'fr'

    cached = True

    def setUp(self):
        """Set up test cases."""
        super(TestTimeStripperWithNoDigitsAsMonths, self).setUp()
        self.ts = TimeStripper(self.get_site())

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

    def test_hour(self):
        """Test that correct hour is matched."""
        txtHourInRange = u'7 février 2010 à 23:00 (CET)'
        txtHourOutOfRange = u'7 février 2010 à 24:00 (CET)'

        self.assertNotEqual(self.ts.timestripper(txtHourInRange), None)
        self.assertEqual(self.ts.timestripper(txtHourOutOfRange), None)


class TestTimeStripperWithDigitsAsMonths(TestCase):

    """Test cases for TimeStripper methods."""

    family = 'wikipedia'
    code = 'cs'

    cached = True

    def setUp(self):
        """Setup a timestripper for the configured site."""
        super(TestTimeStripperWithDigitsAsMonths, self).setUp()
        self.ts = TimeStripper(self.get_site())

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


class TestTimeStripperLanguage(TestCase):

    """Test cases for English language."""

    sites = {
        'cswiki': {
            'family': 'wikipedia',
            'code': 'cs',
            'match': u'3. 2. 2010, 19:48 (UTC) 7. 2. 2010 19:48 (UTC)',
        },
        'enwiki': {
            'family': 'wikipedia',
            'code': 'en',
            'match': u'3 February 2010 19:48 (UTC) 7 February 2010 19:48 (UTC)',
            'nomatch': u'3. 2. 2010, 19:48 (UTC) 7. 2. 2010 19:48 (UTC)',
        },
        'fawiki': {
            'family': 'wikipedia',
            'code': 'fa',
            'match': u'۳ فوریهٔ  ۲۰۱۰، ساعت ۱۹:۴۸ (UTC) ۷ فوریهٔ  ۲۰۱۰، ساعت ۱۹:۴۸ (UTC)',
            'nomatch': u'۳ ۲ ۲۰۱۴ ۱۹:۴۸ (UTC) ۷ ۲ ۲۰۱۰ ۱۹:۴۸ (UTC)',
        },
        'frwiki': {
            'family': 'wikipedia',
            'code': 'fr',
            'match': u'3 février 2010 à 19:48 (CET) 7 février 2010 à 19:48 (CET)',
            'nomatch': u'3 March 2010 19:48 (CET) 7 March 2010 19:48 (CET)',
        },
        'kowiki': {
            'family': 'wikipedia',
            'code': 'ko',
            'match': u'2010년 2월 3일 (수) 19:48 (KST) 2010년 2월 7일 (수) 19:48 (KST)',
        },
        'nowiki': {
            'family': 'wikipedia',
            'code': 'no',
            'match': u'3. feb 2010 kl. 19:48 (CET) 7. feb 2010 kl. 19:48 (UTC)',
        },
        'ptwiki': {
            'family': 'wikipedia',
            'code': 'pt',
            'match': u'19h48min de 3 de fevereiro de 2010‎ (UTC) 19h48min de 7 de fevereiro de 2010‎ (UTC)',
        },
        'viwiki': {
            'family': 'wikipedia',
            'code': 'vi',
            'match': u'19:48, ngày 15 tháng 9 năm 2008 (UTC) 19:48, ngày 7 tháng 2 năm 2010 (UTC)',
            'match2': u'16:41, ngày 15 tháng 9 năm 2008 (UTC) 16:41, ngày 12 tháng 9 năm 2008 (UTC)',
            'match3':  u'21:18, ngày 13 tháng 8 năm 2014 (UTC) 21:18, ngày 14 tháng 8 năm 2014 (UTC)',
            'nomatch1': u'21:18, ngày 13 March 8 năm 2014 (UTC) 21:18, ngày 14 March 8 năm 2014 (UTC)',
        },
    }

    cached = True

    def test_timestripper_match(self, key):
        """Test that correct date is matched."""
        self.ts = TimeStripper(self.get_site(key))

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        txtMatch = self.sites[key]['match']

        res = datetime.datetime(2010, 2, 7, 19, 48, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)

        if 'match2' not in self.sites[key]:
            return

        txtMatch = self.sites[key]['match2']

        res = datetime.datetime(2008, 9, 12, 16, 41, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)

        if 'match3' not in self.sites[key]:
            return

        txtMatch = self.sites[key]['match3']

        res = datetime.datetime(2014, 8, 14, 21, 18, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)

    def test_timestripper_nomatch(self, key):
        """Test that correct date is not matched."""
        self.ts = TimeStripper(self.get_site(key))

        if 'nomatch' in self.sites[key]:
            txtNoMatch = self.sites[key]['nomatch']
        else:
            txtNoMatch = u'3 March 2010 19:48 (UTC) 7 March 2010 19:48 (UTC)'

        self.assertEqual(self.ts.timestripper(txtNoMatch), None)

        if 'nomatch1' not in self.sites[key]:
            return

        txtNoMatch = self.sites[key]['nomatch1']
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)


class TestTimeStripperDoNotArchiveUntil(TestCase):

    """Test cases for Do Not Archive Until templates.

    See https://commons.wikimedia.org/wiki/Template:DNAU and
    https://en.wikipedia.org/wiki/Template:Do_not_archive_until.
    """

    family = 'wikisource'
    code = 'en'

    cached = True

    username = '[[User:DoNotArchiveUntil]]'
    date = '06:57 06 June 2015 (UTC)'
    user_and_date = username + ' ' + date
    tzone = tzoneFixedOffset(0, 'UTC')

    def test_timestripper_match(self):
        """Test that dates in comments  are correctly recognised."""
        ts = TimeStripper(self.get_site())

        txt_match = '<!-- [[User:Do___ArchiveUntil]] ' + self.date + ' -->'
        res = datetime.datetime(2015, 6, 6, 6, 57, tzinfo=self.tzone)
        self.assertEqual(ts.timestripper(txt_match), res)

        txt_match = '<!-- --> <!-- ' + self.user_and_date + ' <!-- -->'
        res = datetime.datetime(2015, 6, 6, 6, 57, tzinfo=self.tzone)
        self.assertEqual(ts.timestripper(txt_match), res)

        txt_match = '<!-- ' + self.user_and_date + ' -->'
        res = datetime.datetime(2015, 6, 6, 6, 57, tzinfo=self.tzone)
        self.assertEqual(ts.timestripper(txt_match), res)

    def test_timestripper_match_only(self):
        """Test that latest date is used instead of other dates."""
        ts = TimeStripper(self.get_site())

        later_date = '10:57 06 June 2015 (UTC)'
        txt_match = '<!-- --> ' + self.user_and_date + ' <!-- -->' + later_date
        res = datetime.datetime(2015, 6, 6, 10, 57, tzinfo=self.tzone)
        self.assertEqual(ts.timestripper(txt_match), res)

        earlier_date = '02:57 06 June 2015 (UTC)'
        txt_match = '<!-- ' + self.user_and_date + ' --> ' + earlier_date
        res = datetime.datetime(2015, 6, 6, 6, 57, tzinfo=self.tzone)
        self.assertEqual(ts.timestripper(txt_match), res)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
