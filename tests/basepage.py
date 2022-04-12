"""BasePage tests subclasses."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot.page import BasePage
from tests.aspects import TestCase


class BasePageTestBase(TestCase):

    """Base of BasePage test classes."""

    _page = None

    def setUp(self):
        """Set up test."""
        super().setUp()
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
    custom_text = 'foobar'

    def setUp(self):
        """Set up test."""
        super().setUp()
        assert self.cached is False, 'Tests do not support caching'

    def _test_page_text(self, get_text=True):
        """Test site.loadrevisions() with .text."""
        page = self._page

        self.assertFalse(hasattr(page, '_revid'))
        self.assertFalse(hasattr(page, '_text'))
        self.assertTrue(hasattr(page, '_revisions'))
        self.assertFalse(page._revisions)

        # verify that initializing the page content
        # does not discard the custom text
        custom_text = self.custom_text
        page.text = custom_text

        page._revisions = {}
        self.site.loadrevisions(page, total=1)

        self.assertTrue(hasattr(page, '_revid'))
        self.assertTrue(hasattr(page, '_revisions'))
        self.assertLength(page._revisions, 1)
        self.assertIn(page._revid, page._revisions)

        self.assertEqual(page._text, custom_text)
        self.assertEqual(page.text, page._text)
        del page.text

        self.assertFalse(hasattr(page, '_text'))
        self.assertIsNone(page._revisions[page._revid].text)
        self.assertIsNone(page._latest_cached_revision())

        page.text = custom_text

        self.site.loadrevisions(page, total=1, content=True)

        self.assertIsNotNone(page._latest_cached_revision())
        self.assertEqual(page._text, custom_text)
        self.assertEqual(page.text, page._text)
        del page.text
        self.assertFalse(hasattr(page, '_text'))

        # Verify that calling .text doesn't call loadrevisions again
        loadrevisions = self.site.loadrevisions
        try:
            self.site.loadrevisions = None
            if get_text:
                loaded_text = page.text
            else:  # T107537
                with self.assertRaises(NotImplementedError):
                    page.text
                loaded_text = ''
            self.assertIsNotNone(loaded_text)
            self.assertFalse(hasattr(page, '_text'))
            page.text = custom_text
            if get_text:
                self.assertEqual(page.get(), loaded_text)
            self.assertEqual(page._text, custom_text)
            self.assertEqual(page.text, page._text)
            del page.text
            self.assertFalse(hasattr(page, '_text'))
            if get_text:
                self.assertEqual(page.text, loaded_text)
        finally:
            self.site.loadrevisions = loadrevisions


class BasePageMethodsTestBase(BasePageTestBase):

    """Test base methods."""

    def _test_invoke(self):
        """Basic invocation of some base methods and properties."""
        self.assertTrue(self._page.exists())
        self.assertIsNotNone(self._page.latest_revision)

        self.assertIsInstance(self._page.latest_revision_id, int)
        self.assertGreaterEqual(self._page.latest_revision_id, 1)

        self.assertIsInstance(self._page.latest_revision.parentid, int)
        self.assertGreaterEqual(self._page.latest_revision.parentid, 0)

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
