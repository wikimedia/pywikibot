# -*- coding: utf-8 -*-
"""Tests for archivebot.py/Timestripper."""
#
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import datetime
import re

from pywikibot.textlib import TimeStripper, tzoneFixedOffset

from tests.aspects import (
    unittest,
    TestCase,
)

MatchObject = type(re.search('', ''))


class TestTimeStripperCase(TestCase):

    """Basic class to test the TimeStripper class."""

    cached = True

    def setUp(self):
        """Set up test cases."""
        super(TestTimeStripperCase, self).setUp()
        self.ts = TimeStripper(self.get_site())


class TestTimeStripperWithNoDigitsAsMonths(TestTimeStripperCase):

    """Test cases for TimeStripper methods."""

    family = 'wikipedia'
    code = 'fr'

    def test_last_match_and_replace(self):
        """Test that pattern matches and removes items correctly."""
        txtWithOneMatch = u'this string has 3000, 1999 and 3000 in it'
        txtWithTwoMatch = u'this string has 1998, 1999 and 3000 in it'
        txtWithNoMatch = u'this string has no match'
        pat = self.ts.pyearR

        txt, m = self.ts._last_match_and_replace(txtWithOneMatch, pat)
        self.assertEqual('this string has 3000, @@@@ and 3000 in it', txt)
        self.assertIsInstance(m, MatchObject)
        self.assertEqual(m.groupdict(), {'year': '1999'})
        self.assertEqual(m.start(), 22)

        txt, m = self.ts._last_match_and_replace(txtWithTwoMatch, pat)
        self.assertEqual('this string has @@@@, @@@@ and 3000 in it', txt)
        self.assertIsInstance(m, MatchObject)
        self.assertEqual(m.groupdict(), {'year': '1999'})
        self.assertEqual(m.start(), 22)

        self.assertEqual(self.ts._last_match_and_replace(txtWithNoMatch, pat),
                         (txtWithNoMatch,
                          None)
                         )

        txtWithOneMatch = u'this string has XXX, YYY and février in it'
        txtWithTwoMatch = u'this string has XXX, mars and février in it'
        txtWithThreeMatch = u'this string has avr, mars and février in it'
        txtWithNoMatch = u'this string has no match'
        pat = self.ts.pmonthR

        txt, m = self.ts._last_match_and_replace(txtWithOneMatch, pat)
        self.assertEqual('this string has XXX, YYY and @@@@@@@ in it', txt)
        self.assertIsInstance(m, MatchObject)
        self.assertEqual(m.groupdict(), {'month': 'février'})
        self.assertEqual(m.start(), 29)

        txt, m = self.ts._last_match_and_replace(txtWithTwoMatch, pat)
        self.assertEqual('this string has XXX, @@@@ and @@@@@@@ in it', txt)
        self.assertIsInstance(m, MatchObject)
        self.assertEqual(m.groupdict(), {'month': 'février'})
        self.assertEqual(m.start(), 30)

        txt, m = self.ts._last_match_and_replace(txtWithThreeMatch, pat)
        self.assertEqual('this string has @@@, @@@@ and @@@@@@@ in it', txt)
        self.assertIsInstance(m, MatchObject)
        self.assertEqual(m.groupdict(), {'month': 'février'})
        self.assertEqual(m.start(), 30)

        self.assertEqual(self.ts._last_match_and_replace(txtWithNoMatch, pat),
                         (txtWithNoMatch,
                          None)
                         )

    def test_hour(self):
        """Test that correct hour is matched."""
        txtHourInRange = u'7 février 2010 à 23:00 (CET)'
        txtHourOutOfRange = u'7 février 2010 à 24:00 (CET)'

        self.assertNotEqual(self.ts.timestripper(txtHourInRange), None)
        self.assertEqual(self.ts.timestripper(txtHourOutOfRange), None)


class TestTimeStripperWithDigitsAsMonths(TestTimeStripperCase):

    """Test cases for TimeStripper methods."""

    family = 'wikipedia'
    code = 'cs'

    def test_last_match_and_replace(self):
        """Test that pattern matches and removes items correctly."""
        txtWithOneMatch = u'this string has XX. YY. 12. in it'
        txtWithTwoMatch = u'this string has XX. 1. 12. in it'
        txtWithThreeMatch = u'this string has 1. 1. 12. in it'
        txtWithNoMatch = u'this string has no match'
        pat = self.ts.pmonthR

        txt, m = self.ts._last_match_and_replace(txtWithOneMatch, pat)
        self.assertEqual('this string has XX. YY. 12. in it', txt)
        self.assertIsInstance(m, MatchObject)
        self.assertEqual(m.groupdict(), {'month': '12.'})
        self.assertEqual(m.start(), 24)

        txt, m = self.ts._last_match_and_replace(txtWithTwoMatch, pat)
        self.assertEqual('this string has XX. 1. 12. in it', txt)
        self.assertIsInstance(m, MatchObject)
        self.assertEqual(m.groupdict(), {'month': '12.'})
        self.assertEqual(m.start(), 23)

        txt, m = self.ts._last_match_and_replace(txtWithThreeMatch, pat)
        self.assertEqual('this string has @@ 1. 12. in it', txt)
        self.assertIsInstance(m, MatchObject)
        self.assertEqual(m.groupdict(), {'month': '12.'})
        self.assertEqual(m.start(), 22)

        self.assertEqual(self.ts._last_match_and_replace(txtWithNoMatch, pat),
                         (txtWithNoMatch,
                          None)
                         )


class TestTimeStripperNumberAndDate(TestTimeStripperCase):

    """Test cases for lines with (non-year) numbers and timestamps."""

    family = 'wikipedia'
    code = 'en'

    def test_four_digit_is_not_year_with_no_timestamp(self):
        """A 4-digit number should not be mistaken as year (w/o timestamp)."""
        self.assertIsNone(
            self.ts.timestripper(
                '2000 people will meet on 16 December at 22:00 (UTC).'))

    def test_four_digit_is_not_year_with_timestamp(self):
        """A 4-digit number should not be mistaken as year (w/ timestamp)."""
        self.assertEqual(
            self.ts.timestripper(
                '2000 people will attend. --12:12, 14 December 2015 (UTC)'),
            datetime.datetime(
                2015, 12, 14, 12, 12, tzinfo=tzoneFixedOffset(0, 'UTC')))


class TestTimeStripperLanguage(TestCase):

    """Test cases for English language."""

    sites = {
        'cswiki': {
            'family': 'wikipedia',
            'code': 'cs',
            'match': u'3. 2. 2011, 19:48 (UTC) 7. 2. 2010 19:48 (UTC)',
        },
        'enwiki': {
            'family': 'wikipedia',
            'code': 'en',
            'match': u'3 February 2011 19:48 (UTC) 7 February 2010 19:48 (UTC)',
            'nomatch': u'3. 2. 2011, 19:48 (UTC) 7. 2. 2010 19:48 (UTC)',
        },
        'fawiki': {
            'family': 'wikipedia',
            'code': 'fa',
            'match': u'۳ فوریهٔ  ۲۰۱۱، ساعت ۱۹:۴۸ (UTC) ۷ فوریهٔ  ۲۰۱۰، ساعت ۱۹:۴۸ (UTC)',
            'nomatch': u'۳ ۲ ۲۰۱۴ ۱۹:۴۸ (UTC) ۷ ۲ ۲۰۱۰ ۱۹:۴۸ (UTC)',
        },
        'frwiki': {
            'family': 'wikipedia',
            'code': 'fr',
            'match': u'3 février 2011 à 19:48 (CET) 7 février 2010 à 19:48 (CET)',
            'nomatch': u'3 March 2011 19:48 (CET) 7 March 2010 19:48 (CET)',
        },
        'kowiki': {
            'family': 'wikipedia',
            'code': 'ko',
            'match': u'2011년 2월 3일 (수) 19:48 (KST) 2010년 2월 7일 (수) 19:48 (KST)',
        },
        'nowiki': {
            'family': 'wikipedia',
            'code': 'no',
            'match': u'3. feb 2011 kl. 19:48 (CET) 7. feb 2010 kl. 19:48 (UTC)',
        },
        'ptwiki': {
            'family': 'wikipedia',
            'code': 'pt',
            'match': '19h48min de 3 de fevereiro de 2011‎ (UTC) 19h48min '
                     'de 7 de fevereiro de 2010‎ (UTC)',
        },
        'viwiki': {
            'family': 'wikipedia',
            'code': 'vi',
            'match': '19:48, ngày 3 tháng 2 năm 2011 (UTC) 19:48, ngày 7 tháng 2 năm 2010 (UTC)',
            'match2': '16:41, ngày 15 tháng 9 năm 2001 (UTC) 16:41, '
                      'ngày 12 tháng 9 năm 2008 (UTC)',
            'match3': '21:18, ngày 13 tháng 8 năm 2011 (UTC) 21:18, '
                      'ngày 14 tháng 8 năm 2014 (UTC)',
            'nomatch1': '21:18, ngày 13 March 8 năm 2011 (UTC) 21:18, '
                        'ngày 14 March 8 năm 2014 (UTC)',
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
            txtNoMatch = u'3 March 2011 19:48 (UTC) 7 March 2010 19:48 (UTC)'

        self.assertEqual(self.ts.timestripper(txtNoMatch), None)

        if 'nomatch1' not in self.sites[key]:
            return

        txtNoMatch = self.sites[key]['nomatch1']
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)


class TestTimeStripperTreatSpecialText(TestTimeStripperCase):

    """Test special text behaviour (comments, hyperlinks, wikilinks)."""

    family = 'wikisource'
    code = 'en'

    date = '06:57 06 June 2015 (UTC)'
    fake_date = '05:57 06 June 2015 (UTC)'
    tzone = tzoneFixedOffset(0, 'UTC')
    expected_date = datetime.datetime(2015, 6, 6, 6, 57, tzinfo=tzone)

    def test_timestripper_match_comment(self):
        """Test that comments are correctly matched."""
        ts = self.ts

        txt_match = self.date + '<!--a test comment-->'
        exp_match = 'a test comment'
        self.assertEqual(ts._comment_pat.search(txt_match).group(1),
                         exp_match)

    def test_timestripper_match_hyperlink(self):
        """Test that hyperlinks are correctly matched."""
        ts = self.ts

        txt_match = '[http://test.org | a link]'
        exp_match = '[http://test.org | a link]'
        self.assertEqual(ts._hyperlink_pat.search(txt_match).group(),
                         exp_match)

    def test_timestripper_match_wikilink(self):
        """Test that wikilinks are correctly matched."""
        ts = self.ts

        txt_match = '[[wikilink|a wikilink with no date]]'
        exp_match_link = 'wikilink'
        exp_match_anchor = '|a wikilink with no date'
        self.assertEqual(ts._wikilink_pat.search(txt_match).group('link'),
                         exp_match_link)
        self.assertEqual(ts._wikilink_pat.search(txt_match).group('anchor'),
                         exp_match_anchor)

    def test_timestripper_match_comment_with_date(self):
        """Test that dates in comments are correctly matched."""
        ts = self.ts.timestripper

        txt_match = self.date + '<!--' + self.fake_date + '-->'
        self.assertEqual(ts(txt_match), self.expected_date)

        txt_match = '<!--' + self.fake_date + '-->' + self.date
        self.assertEqual(ts(txt_match), self.expected_date)

        txt_match = '<!--' + self.date + '-->' + self.fake_date
        self.assertEqual(ts(txt_match), self.expected_date)

        txt_match = '<!--comment|' + self.date + '-->' + self.fake_date
        self.assertEqual(ts(txt_match), self.expected_date)

    def test_timestripper_skip_hyperlink(self):
        """Test that dates in hyperlinks are correctly skipped."""
        ts = self.ts.timestripper

        txt_match = self.date + '[http://' + self.fake_date + ']'
        self.assertEqual(ts(txt_match), self.expected_date)

        txt_match = '[http://' + self.fake_date + ']' + self.date
        self.assertEqual(ts(txt_match), self.expected_date)

        txt_match = ('%s [http://www.org | link with date %s]'
                     % (self.date, self.fake_date))
        self.assertEqual(ts(txt_match), self.expected_date)

        txt_match = '[http://' + self.fake_date + ']' + self.date
        self.assertEqual(ts(txt_match), self.expected_date)

    def test_timestripper_skip_hyperlink_and_do_not_connect(self):
        """Test that skipping hyperlinks will not make gaps shorter."""
        ts = self.ts.timestripper

        txt_match = ('%s[http://example.com Here is long enough text]%s'
                     % (self.date[:9], self.date[9:]))
        self.assertEqual(ts(txt_match), None)

    def test_timestripper_match_wikilink_with_date(self):
        """Test that dates in wikilinks are correctly matched."""
        ts = self.ts.timestripper

        txt_match = self.date + '[[' + self.fake_date + ']]'
        self.assertEqual(ts(txt_match), self.expected_date)

        txt_match = '[[' + self.fake_date + ']]' + self.date
        self.assertEqual(ts(txt_match), self.expected_date)

        txt_match = '[[' + self.date + ']]' + self.fake_date
        self.assertEqual(ts(txt_match), self.expected_date)

        txt_match = '[[wikilink|' + self.date + ']]' + self.fake_date
        self.assertEqual(ts(txt_match), self.expected_date)

    def test_timestripper_skip_wikilink_and_do_not_connect(self):
        """Test that skipping wikilinks will not make gaps shorter."""
        ts = self.ts.timestripper

        txt_match = ('%s[[Here is long enough text]]%s'
                     % (self.date[:9], self.date[9:]))
        self.assertEqual(ts(txt_match), None)

        txt_match = self.date[:9] + '[[foo]]' + self.date[9:]
        self.assertEqual(ts(txt_match), self.expected_date)


class TestTimeStripperDoNotArchiveUntil(TestTimeStripperCase):

    """Test cases for Do Not Archive Until templates.

    See https://commons.wikimedia.org/wiki/Template:DNAU and
    https://en.wikipedia.org/wiki/Template:Do_not_archive_until.
    """

    family = 'wikisource'
    code = 'en'

    username = '[[User:DoNotArchiveUntil]]'
    date = '06:57 06 June 2015 (UTC)'
    user_and_date = username + ' ' + date
    tzone = tzoneFixedOffset(0, 'UTC')

    def test_timestripper_match(self):
        """Test that dates in comments are correctly recognised."""
        ts = self.ts

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
        ts = self.ts

        later_date = '10:57 06 June 2015 (UTC)'
        txt_match = '<!-- --> ' + self.user_and_date + ' <!-- -->' + later_date
        res = datetime.datetime(2015, 6, 6, 10, 57, tzinfo=self.tzone)
        self.assertEqual(ts.timestripper(txt_match), res)

        earlier_date = '02:57 06 June 2015 (UTC)'
        txt_match = '<!-- ' + self.user_and_date + ' --> ' + earlier_date
        res = datetime.datetime(2015, 6, 6, 6, 57, tzinfo=self.tzone)
        self.assertEqual(ts.timestripper(txt_match), res)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
