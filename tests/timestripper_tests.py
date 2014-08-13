# -*- coding: utf-8  -*-
"""
Tests for archivebot.py/Timestripper.
"""
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


class TestTimeStripper(PywikibotTestCase):
    """Test cases for Link objects"""

    def setUp(self):
        site = pywikibot.Site('fr', 'wikipedia')
        self.ts = TimeStripper(site)
        super(TestTimeStripper, self).setUp()

    def test_findmarker(self):
        """Test that string which is not part of text is found"""

        txt = u'this is a string with a maker is @@@@already present'
        self.assertEqual(self.ts.findmarker(txt, base=u'@@', delta='@@'),
                         '@@@@@@')

    def test_last_match_and_replace(self):
        """Test that pattern matches the righmost item"""

        txtWithMatch = u'this string has one 1998, 1999 and 3000 in it'
        txtWithNoMatch = u'this string has no match'
        pat = self.ts.pyearR

        self.assertEqual(self.ts.last_match_and_replace(txtWithMatch, pat),
                         (u'this string has one @@, @@ and 3000 in it',
                          {'year': u'1999'})
                         )
        self.assertEqual(self.ts.last_match_and_replace(txtWithNoMatch, pat),
                         (txtWithNoMatch,
                          None)
                         )

    def test_timestripper(self):
        """Test that correct date is matched"""

        txtMatch = u'3 février 2010 à 19:48 (CET) 7 février 2010 à 19:48 (CET)'
        txtNoMatch = u'3 March 2010 19:48 (CET) 7 March 2010 19:48 (CET)'

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        res = datetime.datetime(2010, 2, 7, 19, 48, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)


class TestEnglishTimeStripper(PywikibotTestCase):
    """Test cases for Link objects"""

    def setUp(self):
        site = pywikibot.Site('en', 'wikipedia')
        self.ts = TimeStripper(site)
        super(TestEnglishTimeStripper, self).setUp()

    def test_timestripper(self):
        """Test that correct date is matched"""

        txtMatch = u'3 February 2010 19:48 (UTC) 7 February 2010 19:48 (UTC)'
        txtNoMatch = u'3. 2. 2010, 19:48 (UTC) 7. 2. 2010 19:48 (UTC)'

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        res = datetime.datetime(2010, 2, 7, 19, 48, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)


class TestCzechTimeStripper(PywikibotTestCase):
    """Test cases for Link objects"""

    def setUp(self):
        site = pywikibot.Site('cs', 'wikipedia')
        self.ts = TimeStripper(site)
        super(TestCzechTimeStripper, self).setUp()

    def test_timestripper(self):
        """Test that correct date is matched"""

        txtMatch = u'3. 2. 2010, 19:48 (UTC) 7. 2. 2010 19:48 (UTC)'
        txtNoMatch = u'3 March 2010 19:48 (UTC) 7 March 2010 19:48 (UTC)'

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        res = datetime.datetime(2010, 2, 7, 19, 48, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)


class TestPortugueseTimeStripper(PywikibotTestCase):
    """Test cases for Link objects"""

    def setUp(self):
        site = pywikibot.Site('pt', 'wikipedia')
        self.ts = TimeStripper(site)
        super(TestPortugueseTimeStripper, self).setUp()

    def test_timestripper(self):
        """Test that correct date is matched"""

        txtMatch = u'19h48min de 3 de fevereiro de 2010‎ (UTC) 19h48min de 7 de fevereiro de 2010‎ (UTC)'
        txtNoMatch = u'3 March 2010 19:48 (UTC) 7 March 2010 19:48 (UTC)'

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        res = datetime.datetime(2010, 2, 7, 19, 48, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)


class TestNorwegianTimeStripper(PywikibotTestCase):
    """Test cases for Link objects"""

    def setUp(self):
        site = pywikibot.Site('no', 'wikipedia')
        self.ts = TimeStripper(site)
        super(TestNorwegianTimeStripper, self).setUp()

    def test_timestripper(self):
        """Test that correct date is matched"""

        txtMatch = u'3. feb 2010 kl. 19:48 (CET) 7. feb 2010 kl. 19:48 (UTC)'
        txtNoMatch = u'3 March 2010 19:48 (UTC) 7 March 2010 19:48 (UTC)'

        tzone = tzoneFixedOffset(self.ts.site.siteinfo['timeoffset'],
                                 self.ts.site.siteinfo['timezone'])

        res = datetime.datetime(2010, 2, 7, 19, 48, tzinfo=tzone)

        self.assertEqual(self.ts.timestripper(txtMatch), res)
        self.assertEqual(self.ts.timestripper(txtNoMatch), None)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
