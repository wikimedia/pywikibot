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
    Error,
    NoPage,
    LockedPage,
    SpamfilterError,
    OtherPageSaveError,
)
from tests.aspects import unittest, TestCase, WikibaseTestCase


class TestSaveFailure(TestCase):

    """Test cases for edits which should fail to save."""

    write = True

    family = 'wikipedia'
    code = 'test'

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


class TestActionFailure(TestCase):

    """Test cases for actions which should fail to save."""

    write = True

    family = 'wikipedia'
    code = 'test'

    def test_movepage(self):
        """Test that site.movepage raises the appropriate exceptions."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        try:
            mysite.tokens['move']
        except KeyError:
            raise unittest.SkipTest(
                "movepage test requires 'move' token not given to user on %s"
                % self.site)

        self.assertRaises(Error, mysite.movepage,
                          mainpage, mainpage.title(), 'test')

        page_from = self.get_missing_article()
        if not page_from.exists():
            self.assertRaises(NoPage, mysite.movepage,
                              page_from, 'Main Page', 'test')


class TestWikibaseSaveTest(WikibaseTestCase):

    """Test case for WikibasePage.save on Wikidata test site."""

    family = 'wikidata'
    code = 'test'

    write = True

    def test_itempage_save(self):
        """Test ItemPage save method inherited from superclass Page."""
        repo = self.get_repo()
        item = pywikibot.ItemPage(repo, 'Q6')
        self.assertRaises(pywikibot.PageNotSaved, item.save)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
