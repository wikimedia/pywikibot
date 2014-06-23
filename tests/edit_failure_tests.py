# -*- coding: utf-8  -*-
"""
Tests for edit failures.

These tests should never write to the wiki,
unless something has broken badly.
"""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import pywikibot
from pywikibot import (
    LockedPage,
    SpamfilterError,
    OtherPageSaveError,
)
from tests.utils import SiteTestCase, unittest


class TestSaveFailure(SiteTestCase):
    """Test cases for edits which should fail to save."""

    write = True

    def setUp(self):
        super(TestSaveFailure, self).setUp()
        self.site = pywikibot.Site('test', 'wikipedia')

    def test_protected(self):
        """Test that protected titles raise the appropriate exception."""
        if self.site._username[1]:
            raise unittest.SkipTest('Testing failure of edit protected with a sysop account')
        page = pywikibot.Page(self.site, 'Wikipedia:Create a new page')
        self.assertRaises(LockedPage, page.save)

    def test_spam(self):
        """Test that spam in content raise the appropriate exception."""
        page = pywikibot.Page(self.site, 'Wikipedia:Sandbox')
        page.text = 'http://badsite.com'
        self.assertRaisesRegexp(SpamfilterError, 'badsite.com', page.save)

    def test_nobots(self):
        """Test that {{nobots}} raise the appropriate exception."""
        page = pywikibot.Page(self.site, 'User:John Vandenberg/nobots')
        self.assertRaisesRegexp(OtherPageSaveError, 'nobots', page.save)

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
