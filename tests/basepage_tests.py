# -*- coding: utf-8 -*-
"""Tests for BasePage subclasses."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot.page import BasePage

from tests.aspects import (
    unittest, TestCase,
)


class BasePageTestBase(TestCase):

    """Base of BasePage test classes."""

    _page = None

    def setUp(self):
        """Set up test."""
        super(BasePageTestBase, self).setUp()
        assert self._page, 'setUp() must create an empty BasePage in _page'
        assert isinstance(self._page, BasePage)


class BasePageLoadRevisionsCachingTestBase(BasePageTestBase):

    """
    Test site.loadrevisions() caching.

    This test class monkey patches site.loadrevisions, which will cause
    the pickling tests in site_tests and page_tests to fail, if it
    is done on the same site as those tests use (the default site).
    """

    cached = False

    def setUp(self):
        """Set up test."""
        super(BasePageLoadRevisionsCachingTestBase, self).setUp()
        assert self.cached is False, 'Tests do not support caching'

    def _test_page_text(self):
        """Test site.loadrevisions() with .text."""
        page = self._page

        self.assertFalse(hasattr(page, '_revid'))
        self.assertFalse(hasattr(page, '_text'))
        self.assertTrue(hasattr(page, '_revisions'))
        self.assertFalse(page._revisions)

        self.site.loadrevisions(page, total=1)

        self.assertTrue(hasattr(page, '_revid'))
        self.assertTrue(hasattr(page, '_revisions'))
        self.assertEqual(len(page._revisions), 1)
        self.assertIn(page._revid, page._revisions)

        self.assertFalse(hasattr(page, '_text'))
        self.assertIsNone(page._revisions[page._revid].text)
        self.assertFalse(hasattr(page, '_text'))
        self.assertIsNone(page._latest_cached_revision())

        self.site.loadrevisions(page, total=1, getText=True)
        self.assertFalse(hasattr(page, '_text'))
        self.assertIsNotNone(page._latest_cached_revision())

        # Verify that calling .text doesnt call loadrevisions again
        loadrevisions = self.site.loadrevisions
        try:
            self.site.loadrevisions = None
            self.assertIsNotNone(page.text)
        finally:
            self.site.loadrevisions = loadrevisions

        self.assertTrue(hasattr(page, '_text'))


class BasePageMethodsTestBase(BasePageTestBase):

    """Test base methods."""

    def _test_invoke(self):
        """Basic invocation of some base methods and properties."""
        self.assertTrue(self._page.exists())
        self.assertIsNotNone(self._page.latest_revision)

        self.assertIsInstance(self._page.latest_revision_id, int)
        self.assertGreaterEqual(self._page.latest_revision_id, 1)

        self.assertIsInstance(self._page.latest_revision.parent_id, int)
        self.assertGreaterEqual(self._page.latest_revision.parent_id, 0)

        self._page.botMayEdit()

    def _test_return_datatypes(self):
        """Test the base methods have correct datatypes only."""
        self.assertIsInstance(self._page.langlinks(), list)
        self.assertIsInstance(self._page.templates(), list)
        self.assertIsInstance(self._page.isCategoryRedirect(), int)

    def _test_no_wikitext(self):
        """Test the base methods responses simulate no wikitext."""
        self._test_return_datatypes()
        self.assertEqual(self._page.langlinks(), [])
        self.assertEqual(self._page.templates(), [])
        self.assertFalse(self._page.isCategoryRedirect())
        self.assertTrue(self._page.botMayEdit())

if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
