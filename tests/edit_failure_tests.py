# -*- coding: utf-8 -*-
"""
Tests for edit failures.

These tests should never write to the wiki,
unless something has broken badly.

These tests use special code 'write = -1' for edit failures.
"""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import pywikibot
from pywikibot import (
    Error,
    NoPage,
    LockedPage,
    SpamfilterError,
    OtherPageSaveError,
    NoCreateError,
    PageCreatedConflict,
)
from tests.aspects import unittest, TestCase, WikibaseTestCase


class TestSaveFailure(TestCase):

    """Test cases for edits which should fail to save."""

    user = True
    write = -1

    family = 'wikipedia'
    code = 'test'

    def test_protected(self):
        """Test that protected titles raise the appropriate exception."""
        if self.site.has_group('sysop'):
            raise unittest.SkipTest('Testing failure of edit protected with a sysop account')
        page = pywikibot.Page(self.site, 'Wikipedia:Create a new page')
        self.assertRaises(LockedPage, page.save)

    def test_spam(self):
        """Test that spam in content raise the appropriate exception."""
        page = pywikibot.Page(self.site, 'Wikipedia:Sandbox')
        page.text = 'http://badsite.com'
        self.assertRaisesRegex(SpamfilterError, 'badsite.com', page.save)

    def test_nobots(self):
        """Test that {{nobots}} raise the appropriate exception."""
        page = pywikibot.Page(self.site, 'User:John Vandenberg/nobots')
        self.assertRaisesRegex(OtherPageSaveError, 'nobots', page.save)

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
        self.assertRaises(PageCreatedConflict, page.save, createonly=True)

    def test_nocreate(self):
        """Test that Page.save with nocreate fails if page does not exist."""
        page = pywikibot.Page(self.site, 'User:John_Vandenberg/no_recreate')
        self.assertRaises(NoCreateError, page.save, nocreate=True)

    def test_no_recreate(self):
        """Test that Page.save with recreate disabled fails if page existed."""
        page = pywikibot.Page(self.site, 'User:John_Vandenberg/no_recreate')
        self.assertRaisesRegex(OtherPageSaveError, 'Page .* doesn\'t exist',
                               page.save, recreate=False)


class TestActionFailure(TestCase):

    """Test cases for actions which should fail to save."""

    user = True
    write = -1

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

    user = True
    write = -1

    def test_itempage_save(self):
        """Test ItemPage save method inherited from superclass Page."""
        repo = self.get_repo()
        item = pywikibot.ItemPage(repo, 'Q6')
        self.assertRaises(pywikibot.PageNotSaved, item.save)

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
        self.assertAPIError('modification-failed', 'Illegal value: foo',
                            item.addClaim, claim)

    def test_WbMonolingualText_invalid_text(self):
        """Attempt adding a monolingual text with an invalid non-string text."""
        repo = self.get_repo()
        item = pywikibot.ItemPage(repo, 'Q68')
        claim = self._make_WbMonolingualText_claim(repo, text=123456, language='en')
        self.assertAPIError('invalid-snak',
                            'Invalid snak. (Can only construct a '
                            'MonolingualTextValue with a string value.)',
                            item.addClaim, claim)

    def test_math_invalid_function(self):
        """Attempt adding invalid latex to a math claim."""
        repo = self.get_repo()
        item = pywikibot.ItemPage(repo, 'Q68')
        claim = pywikibot.page.Claim(repo, 'P717', datatype='math')
        claim.setTarget('\foo')
        self.assertAPIError('modification-failed', None, item.addClaim, claim)

    def test_url_malformed_url(self):
        """Attempt adding a malformed URL to a url claim."""
        repo = self.get_repo()
        item = pywikibot.ItemPage(repo, 'Q68')
        claim = pywikibot.page.Claim(repo, 'P506', datatype='url')
        claim.setTarget('Not a URL at all')
        self.assertAPIError('modification-failed',
                            'Malformed URL: Not a URL at all',
                            item.addClaim, claim)

    def test_url_invalid_protocol(self):
        """Attempt adding a URL with an invalid protocol to a url claim."""
        repo = self.get_repo()
        item = pywikibot.ItemPage(repo, 'Q68')
        claim = pywikibot.page.Claim(repo, 'P506', datatype='url')
        claim.setTarget('wtf://wikiba.se')
        self.assertAPIError('modification-failed',
                            'Unsupported URL scheme: wtf',
                            item.addClaim, claim)

if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
