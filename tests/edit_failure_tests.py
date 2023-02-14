#!/usr/bin/env python3
"""
Tests for edit failures.

These tests should never write to the wiki,
unless something has broken badly.

These tests use special code 'write = -1' for edit failures.
"""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress
from unittest.mock import patch

import pywikibot
from pywikibot import config
from pywikibot.exceptions import (
    Error,
    LockedPageError,
    NoCreateError,
    NoPageError,
    OtherPageSaveError,
    PageCreatedConflictError,
    PageSaveRelatedError,
    SpamblacklistError,
    TitleblacklistError,
)
from tests.aspects import TestCase, WikibaseTestCase
from tests.utils import skipping


class TestSaveFailure(TestCase):

    """Test cases for edits which should fail to save."""

    login = True
    write = -1

    family = 'wikipedia'
    code = 'test'

    def test_protected(self):
        """Test that protected titles raise the appropriate exception."""
        if self.site.has_group('sysop'):
            self.skipTest(
                'Testing failure of edit protected with a sysop account')
        page = pywikibot.Page(self.site, 'Wikipedia:Create a new page')
        with self.assertRaises(LockedPageError):
            page.save()

    def test_spam(self):
        """Test that spam in content raise the appropriate exception."""
        page = pywikibot.Page(self.site, 'Wikipedia:Sandbox')
        page.text = 'http://badsite.com'
        with skipping(OtherPageSaveError), self.assertRaisesRegex(
                SpamblacklistError, 'badsite.com'):
            page.save()

    def test_titleblacklist(self):
        """Test that title blacklist raise the appropriate exception."""
        page = pywikibot.Page(self.site, 'User:UpsandDowns1234/Blacklisttest')
        with self.assertRaises(TitleblacklistError):
            page.save()

    def test_nobots(self):
        """Test that {{nobots}} raise the appropriate exception."""
        page = pywikibot.Page(self.site, 'User:John Vandenberg/nobots')
        with patch.object(config, 'ignore_bot_templates', False), \
             self.assertRaisesRegex(OtherPageSaveError, 'nobots'):
            page.save()

    def test_touch(self):
        """Test that Page.touch() does not do a real edit."""
        page = pywikibot.Page(self.site, 'User:Xqt/sandbox')
        old_text = page.text
        page.text += '\n*Add a new line to page'
        page.touch()
        new_text = page.get(force=True)
        self.assertEqual(old_text, new_text)

    def test_createonly(self):
        """Test that Page.save with createonly fails if page exists."""
        page = pywikibot.Page(self.site, 'User:Xqt/sandbox')
        with self.assertRaises(PageCreatedConflictError):
            page.save(createonly=True)

    def test_nocreate(self):
        """Test that Page.save with nocreate fails if page does not exist."""
        page = pywikibot.Page(self.site, 'User:John_Vandenberg/no_recreate')
        with self.assertRaises(NoCreateError):
            page.save(nocreate=True)

    def test_no_recreate(self):
        """Test that Page.save with recreate disabled fails if page existed."""
        page = pywikibot.Page(self.site, 'User:John_Vandenberg/no_recreate')
        with self.assertRaisesRegex(
                OtherPageSaveError,
                "Page .* doesn't exist"):
            page.save(recreate=False)


class TestActionFailure(TestCase):

    """Test cases for actions which should fail to save."""

    login = True
    write = -1

    family = 'wikipedia'
    code = 'test'

    def test_movepage(self):
        """Test that site.movepage raises the appropriate exceptions."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        if 'move' not in mysite.tokens:
            self.skipTest(
                "movepage test requires 'move' token not given to user on {}"
                .format(self.site))

        with self.assertRaises(Error):
            mysite.movepage(mainpage, mainpage.title(), 'test')

        page_from = self.get_missing_article()
        if not page_from.exists():
            with self.assertRaises(NoPageError):
                mysite.movepage(page_from, 'Main Page', 'test')


class TestWikibaseSaveTest(WikibaseTestCase):

    """Test case for WikibasePage.save on Wikidata test site."""

    family = 'wikidata'
    code = 'test'

    login = True
    write = -1

    def test_itempage_save(self):
        """Test ItemPage save method inherited from superclass Page."""
        repo = self.get_repo()
        item = pywikibot.ItemPage(repo, 'Q6')
        with self.assertRaises(PageSaveRelatedError):
            item.save()

    def _make_WbMonolingualText_claim(self, repo, text, language):
        """Make a WbMonolingualText and set its value."""
        claim = pywikibot.page.Claim(repo, 'P271', datatype='monolingualtext')
        target = pywikibot.WbMonolingualText(text=text, language=language)
        claim.setTarget(target)
        return claim

    def test_WbMonolingualText_invalid_language(self):
        """Attempt adding a monolingual text with an invalid language."""
        repo = self.get_repo()
        item = pywikibot.ItemPage(repo, 'Q68')
        claim = self._make_WbMonolingualText_claim(repo, text='Test this!',
                                                   language='foo')
        with self.assertRaisesRegex(
                OtherPageSaveError,
                r'Edit to page \[\[(wikidata:test:)?Q68]] failed:\n'
                r'modification-failed: "foo" is not a known language code.'):
            item.addClaim(claim)

    def test_WbMonolingualText_invalid_text(self):
        """Attempt adding a monolingual text with invalid non-string text."""
        repo = self.get_repo()
        item = pywikibot.ItemPage(repo, 'Q68')
        claim = self._make_WbMonolingualText_claim(repo, text=123456,
                                                   language='en')
        with self.assertRaisesRegex(
                OtherPageSaveError,
                r'Edit to page \[\[(wikidata:test:)?Q68]] failed:'):
            item.addClaim(claim)

    def test_math_invalid_function(self):
        """Attempt adding invalid latex to a math claim."""
        repo = self.get_repo()
        item = pywikibot.ItemPage(repo, 'Q68')
        claim = pywikibot.page.Claim(repo, 'P717', datatype='math')
        claim.setTarget('\foo')
        with self.assertRaisesRegex(
                OtherPageSaveError,
                r'Edit to page \[\[(wikidata:test:)?Q68]] failed:\n'
                r'modification-failed: Malformed input:'):
            item.addClaim(claim)

    def test_url_malformed_url(self):
        """Attempt adding a malformed URL to a url claim."""
        repo = self.get_repo()
        item = pywikibot.ItemPage(repo, 'Q68')
        claim = pywikibot.page.Claim(repo, 'P506', datatype='url')
        claim.setTarget('Not a URL at all')
        with self.assertRaisesRegex(
                OtherPageSaveError,
                r'Edit to page \[\[(wikidata:test:)?Q68]] failed:\n'
                r'modification-failed: This URL misses a scheme like '
                r'"https://": '
                r'Not a URL at all'):
            item.addClaim(claim)

    def test_url_invalid_protocol(self):
        """Attempt adding a URL with an invalid protocol to a url claim."""
        repo = self.get_repo()
        item = pywikibot.ItemPage(repo, 'Q68')
        claim = pywikibot.page.Claim(repo, 'P506', datatype='url')
        claim.setTarget('wtf://wikiba.se')
        with self.assertRaisesRegex(
                OtherPageSaveError,
                r'Edit to page \[\[(wikidata:test:)?Q68]] failed:\n'
                r'modification-failed: An URL scheme "wtf" is not supported.'):
            item.addClaim(claim)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
