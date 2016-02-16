# -*- coding: utf-8  -*-
"""Tests for the Wikidata parts of the page module."""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import copy
import json

from decimal import Decimal

import pywikibot

from pywikibot import pagegenerators
from pywikibot.page import WikibasePage, ItemPage
from pywikibot.site import Namespace, NamespacesDict

from tests import join_pages_path
from tests.aspects import (
    unittest, TestCase,
    WikidataTestCase,
    DeprecationTestCase,
    DefaultWikibaseClientTestCase,
)

from tests.basepage_tests import (
    BasePageMethodsTestBase,
    BasePageLoadRevisionsCachingTestBase,
)


# fetch a page which is very likely to be unconnected, which doesnt have
# a generator, and unit tests may be used to test old versions of pywikibot
def _get_test_unconnected_page(site):
    """Get unconnected page from site for tests."""
    gen = pagegenerators.NewpagesPageGenerator(site=site, total=10,
                                               namespaces=[1, ])
    for page in gen:
        if not page.properties().get('wikibase_item'):
            return page


class TestLoadRevisionsCaching(BasePageLoadRevisionsCachingTestBase,
                               WikidataTestCase):

    """Test site.loadrevisions() caching."""

    def setUp(self):
        self._page = ItemPage(self.get_repo(), 'Q60')
        super(TestLoadRevisionsCaching, self).setUp()

    def test_page_text(self):
        """Test site.loadrevisions() with Page.text."""
        self._test_page_text()


class TestDeprecatedAttributes(WikidataTestCase, DeprecationTestCase):

    """Test deprecated lastrevid."""

    def test_lastrevid(self):
        """Test deprecated lastrevid."""
        item = ItemPage(self.get_repo(), 'Q60')
        self.assertFalse(hasattr(item, 'lastrevid'))
        item.get()
        self.assertTrue(hasattr(item, 'lastrevid'))
        self.assertIsInstance(item.lastrevid, int)
        self.assertDeprecation()
        self._reset_messages()

        item.lastrevid = 1
        self.assertTrue(hasattr(item, 'lastrevid'))
        self.assertTrue(hasattr(item, '_revid'))
        self.assertEqual(item.lastrevid, 1)
        self.assertEqual(item._revid, 1)
        self.assertDeprecation()

    def test_lastrevid_del(self):
        """Test del with deprecated lastrevid."""
        item = ItemPage(self.get_repo(), 'Q60')
        item.get()
        self.assertTrue(hasattr(item, 'lastrevid'))
        self.assertTrue(hasattr(item, '_revid'))

        del item.lastrevid
        self.assertFalse(hasattr(item, 'lastrevid'))
        self.assertFalse(hasattr(item, '_revid'))
        self.assertDeprecation()


class TestGeneral(WikidataTestCase):

    """General Wikibase tests."""

    @classmethod
    def setUpClass(cls):
        super(TestGeneral, cls).setUpClass()
        enwiki = pywikibot.Site('en', 'wikipedia')
        cls.mainpage = pywikibot.Page(pywikibot.page.Link("Main Page", enwiki))

    def testWikibase(self):
        repo = self.get_repo()
        item_namespace = repo.namespaces[0]
        self.assertEqual(item_namespace.defaultcontentmodel, 'wikibase-item')
        item = pywikibot.ItemPage.fromPage(self.mainpage)
        self.assertIsInstance(item, pywikibot.ItemPage)
        self.assertEqual(item.getID(), 'Q5296')
        self.assertEqual(item.title(), 'Q5296')
        self.assertIn('en', item.labels)
        self.assertTrue(item.labels['en'].lower().endswith('main page'))
        self.assertIn('en', item.aliases)
        self.assertIn('Home page', item.aliases['en'])
        self.assertEqual(item.namespace(), 0)
        item2 = pywikibot.ItemPage(repo, 'q5296')
        self.assertEqual(item2.getID(), 'Q5296')
        item2.get()
        self.assertTrue(item2.labels['en'].lower().endswith('main page'))
        prop = pywikibot.PropertyPage(repo, 'Property:P21')
        self.assertEqual(prop.type, 'wikibase-item')
        self.assertEqual(prop.namespace(), 120)
        claim = pywikibot.Claim(repo, 'p21')
        self.assertRaises(ValueError, claim.setTarget, value="test")
        claim.setTarget(pywikibot.ItemPage(repo, 'q1'))
        self.assertEqual(claim._formatValue(), {'entity-type': 'item', 'numeric-id': 1})

    def test_cmp(self):
        """Test WikibasePage.__cmp__."""
        self.assertEqual(pywikibot.ItemPage.fromPage(self.mainpage),
                         pywikibot.ItemPage(self.get_repo(), 'q5296'))


class TestWikibaseTypes(WikidataTestCase):

    """Test Wikibase data types."""

    dry = True

    def test_WbTime(self):
        repo = self.get_repo()
        t = pywikibot.WbTime(site=repo, year=2010, hour=12, minute=43)
        self.assertEqual(t.toTimestr(), '+00000002010-01-01T12:43:00Z')
        self.assertRaises(ValueError, pywikibot.WbTime, site=repo, precision=15)
        self.assertRaises(ValueError, pywikibot.WbTime, site=repo, precision='invalid_precision')

    def test_WbQuantity_integer(self):
        q = pywikibot.WbQuantity(amount=1234, error=1)
        self.assertEqual(q.toWikibase(),
                         {'amount': '+1234', 'lowerBound': '+1233',
                          'upperBound': '+1235', 'unit': '1', })
        q = pywikibot.WbQuantity(amount=5, error=(2, 3))
        self.assertEqual(q.toWikibase(),
                         {'amount': '+5', 'lowerBound': '+2',
                          'upperBound': '+7', 'unit': '1', })
        q = pywikibot.WbQuantity(amount=0, error=(0, 0))
        self.assertEqual(q.toWikibase(),
                         {'amount': '+0', 'lowerBound': '+0',
                          'upperBound': '+0', 'unit': '1', })
        q = pywikibot.WbQuantity(amount=-5, error=(2, 3))
        self.assertEqual(q.toWikibase(),
                         {'amount': '-5', 'lowerBound': '-8',
                          'upperBound': '-3', 'unit': '1', })

    def test_WbQuantity_float_27(self):
        q = pywikibot.WbQuantity(amount=0.044405586)
        q_dict = {'amount': '+0.044405586', 'lowerBound': '+0.044405586',
                  'upperBound': '+0.044405586', 'unit': '1', }
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbQuantity_scientific(self):
        q = pywikibot.WbQuantity(amount='1.3e-13', error='1e-14')
        q_dict = {'amount': '+1.3e-13', 'lowerBound': '+1.2e-13',
                  'upperBound': '+1.4e-13', 'unit': '1', }
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbQuantity_decimal(self):
        q = pywikibot.WbQuantity(amount=Decimal('0.044405586'))
        q_dict = {'amount': '+0.044405586', 'lowerBound': '+0.044405586',
                  'upperBound': '+0.044405586', 'unit': '1', }
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbQuantity_string(self):
        q = pywikibot.WbQuantity(amount='0.044405586')
        q_dict = {'amount': '+0.044405586', 'lowerBound': '+0.044405586',
                  'upperBound': '+0.044405586', 'unit': '1', }
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbQuantity_formatting(self):
        # test other WbQuantity methods
        q = pywikibot.WbQuantity(amount='0.044405586')
        self.assertEqual("%s" % q,
                         '{\n'
                         '    "amount": "+%(val)s",\n'
                         '    "lowerBound": "+%(val)s",\n'
                         '    "unit": "1",\n'
                         '    "upperBound": "+%(val)s"\n'
                         '}' % {'val': '0.044405586'})
        self.assertEqual("%r" % q,
                         "WbQuantity(amount=%(val)s, "
                         "upperBound=%(val)s, lowerBound=%(val)s, "
                         "unit=1)" % {'val': '0.044405586'})

    def test_WbQuantity_equality(self):
        q = pywikibot.WbQuantity(amount='0.044405586')
        self.assertEqual(q, q)

    def test_WbQuantity_fromWikibase(self):
        # test WbQuantity.fromWikibase() instantiating
        q = pywikibot.WbQuantity.fromWikibase({u'amount': u'+0.0229',
                                               u'lowerBound': u'0',
                                               u'upperBound': u'1',
                                               u'unit': u'1'})
        # note that the bounds are inputted as INT but are returned as FLOAT
        self.assertEqual(q.toWikibase(),
                         {'amount': '+0.0229', 'lowerBound': '+0.0000',
                          'upperBound': '+1.0000', 'unit': '1', })

    def test_WbQuantity_errors(self):
        # test WbQuantity error handling
        self.assertRaises(ValueError, pywikibot.WbQuantity, amount=None,
                          error=1)

    def test_WbMonolingualText_string(self):
        q = pywikibot.WbMonolingualText(text='Test that basics work', language='en')
        q_dict = {'text': 'Test that basics work', 'language': 'en'}
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbMonolingualText_unicode(self):
        q = pywikibot.WbMonolingualText(text='Testa det här', language='sv')
        q_dict = {'text': 'Testa det här', 'language': 'sv'}
        self.assertEqual(q.toWikibase(), q_dict)

    def test_WbMonolingualText_equality(self):
        q = pywikibot.WbMonolingualText(text='Thou shall test this!', language='en-gb')
        self.assertEqual(q, q)

    def test_WbMonolingualText_fromWikibase(self):
        # test WbMonolingualText.fromWikibase() instantiating
        q = pywikibot.WbMonolingualText.fromWikibase({'text': 'Test this!',
                                                      'language': u'en'})
        self.assertEqual(q.toWikibase(),
                         {'text': 'Test this!', 'language': 'en'})

    def test_WbMonolingualText_errors(self):
        # test WbMonolingualText error handling
        self.assertRaises(ValueError, pywikibot.WbMonolingualText,
                          text='', language='sv')
        self.assertRaises(ValueError, pywikibot.WbMonolingualText,
                          text='Test this!', language='')
        self.assertRaises(ValueError, pywikibot.WbMonolingualText,
                          text=None, language='sv')


class TestItemPageExtensibility(TestCase):

    """Test ItemPage extensibility."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def test_ItemPage_extensibility(self):
        class MyItemPage(pywikibot.ItemPage):
            pass
        page = pywikibot.Page(self.site, 'foo')
        self.assertIsInstance(MyItemPage.fromPage(page, lazy_load=True),
                              MyItemPage)


class TestItemLoad(WikidataTestCase):

    """
    Test item creation.

    Tests for item creation include:
    1. by Q id
    2. ItemPage.fromPage(page)
    3. ItemPage.fromPage(page_with_props_loaded)

    Test various invalid scenarios:
    1. invalid Q ids
    2. invalid pages to fromPage
    3. missing pages to fromPage
    4. unconnected pages to fromPage
    """

    sites = {
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata',
        },
        'enwiki': {
            'family': 'wikipedia',
            'code': 'en',
        }
    }

    @classmethod
    def setUpClass(cls):
        super(TestItemLoad, cls).setUpClass()
        cls.site = cls.get_site('enwiki')
        cls.nyc = pywikibot.Page(pywikibot.page.Link("New York City", cls.site))

    def test_item_normal(self):
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata, 'Q60')
        self.assertEqual(item._link._title, 'Q60')
        self.assertEqual(item._defined_by(), {u'ids': u'Q60'})
        self.assertEqual(item.id, 'Q60')
        self.assertFalse(hasattr(item, '_title'))
        self.assertFalse(hasattr(item, '_site'))
        self.assertEqual(item.title(), 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        self.assertFalse(hasattr(item, '_content'))
        item.get()
        self.assertTrue(hasattr(item, '_content'))

    def test_load_item_set_id(self):
        """Test setting item.id attribute on empty item."""
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata, '-1')
        self.assertEqual(item._link._title, '-1')
        item.id = 'Q60'
        self.assertFalse(hasattr(item, '_content'))
        self.assertEqual(item.getID(), 'Q60')
        self.assertFalse(hasattr(item, '_content'))
        item.get()
        self.assertTrue(hasattr(item, '_content'))
        self.assertIn('en', item.labels)
        self.assertEqual(item.labels['en'], 'New York City')
        self.assertEqual(item.title(), 'Q60')

    def test_reuse_item_set_id(self):
        """
        Test modifying item.id attribute.

        Some scripts are using item.id = 'Q60' semantics, which does work
        but modifying item.id does not currently work, and this test
        highlights that it breaks silently.
        """
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata, 'Q60')
        item.get()
        self.assertEqual(item.labels['en'], 'New York City')

        # When the id attribute is modified, the ItemPage goes into
        # an inconsistent state.
        item.id = 'Q5296'
        # The title is updated correctly
        self.assertEqual(item.title(), 'Q5296')

        # This del has no effect on the test; it is here to demonstrate that
        # it doesnt help to clear this piece of saved state.
        del item._content
        # The labels are not updated; assertion showing undesirable behaviour:
        self.assertEqual(item.labels['en'], 'New York City')
        # TODO: This is the assertion that this test should be using:
        # self.assertTrue(item.labels['en'].lower().endswith('main page'))

    def test_empty_item(self):
        # should not raise an error as the constructor only requires
        # the site parameter, with the title parameter defaulted to None
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata)
        self.assertEqual(item._link._title, '-1')

    def test_item_invalid_titles(self):
        wikidata = self.get_repo()
        for title in ['null', 'NULL', 'None', '',
                      '-2', '1', '0', '+1',
                      'Q0', 'Q0.5', 'Q', 'Q-1', 'Q+1']:
            self.assertRaises(pywikibot.InvalidTitle,
                              pywikibot.ItemPage, wikidata, title)

    def test_item_untrimmed_title(self):
        wikidata = self.get_repo()
        # spaces in the title should not cause an error
        item = pywikibot.ItemPage(wikidata, ' Q60 ')
        self.assertEqual(item._link._title, 'Q60')
        self.assertEqual(item.title(), 'Q60')
        item.get()

    def test_item_missing(self):
        wikidata = self.get_repo()
        # this item has never existed
        item = pywikibot.ItemPage(wikidata, 'Q7')
        self.assertEqual(item._link._title, 'Q7')
        self.assertEqual(item.title(), 'Q7')
        self.assertFalse(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q7')
        self.assertEqual(item.getID(), 'Q7')
        numeric_id = item.getID(numeric=True)
        self.assertIsInstance(numeric_id, int)
        self.assertEqual(numeric_id, 7)
        self.assertFalse(hasattr(item, '_content'))
        self.assertRaises(pywikibot.NoPage, item.get)
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q7')
        self.assertEqual(item.getID(), 'Q7')
        self.assertEqual(item._link._title, 'Q7')
        self.assertEqual(item.title(), 'Q7')
        self.assertRaises(pywikibot.NoPage, item.get)
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item._link._title, 'Q7')
        self.assertEqual(item.getID(), 'Q7')
        self.assertEqual(item.title(), 'Q7')

    def test_item_never_existed(self):
        wikidata = self.get_repo()
        # this item has not been created
        item = pywikibot.ItemPage(wikidata, 'Q9999999999999999999')
        self.assertFalse(item.exists())
        self.assertEqual(item.getID(), 'Q9999999999999999999')
        self.assertRaises(pywikibot.NoPage, item.get)

    def test_fromPage_noprops(self):
        page = self.nyc
        item = pywikibot.ItemPage.fromPage(page)
        self.assertEqual(item._link._title, '-1')
        self.assertTrue(hasattr(item, 'id'))
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.title(), 'Q60')
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        item.get()
        self.assertTrue(item.exists())

    def test_fromPage_noprops_with_section(self):
        page = pywikibot.Page(self.nyc.site, self.nyc.title() + '#foo')
        item = pywikibot.ItemPage.fromPage(page)
        self.assertEqual(item._link._title, '-1')
        self.assertTrue(hasattr(item, 'id'))
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.title(), 'Q60')
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        item.get()
        self.assertTrue(item.exists())

    def test_fromPage_props(self):
        page = self.nyc
        # fetch page properties
        page.properties()
        item = pywikibot.ItemPage.fromPage(page)
        self.assertEqual(item._link._title, 'Q60')
        self.assertEqual(item.id, 'Q60')
        self.assertFalse(hasattr(item, '_content'))
        self.assertEqual(item.title(), 'Q60')
        self.assertFalse(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        self.assertFalse(hasattr(item, '_content'))
        item.get()
        self.assertTrue(hasattr(item, '_content'))
        self.assertTrue(item.exists())

    def test_fromPage_lazy(self):
        page = pywikibot.Page(pywikibot.page.Link("New York City", self.site))
        item = pywikibot.ItemPage.fromPage(page, lazy_load=True)
        self.assertEqual(item._defined_by(),
                         {'sites': u'enwiki', 'titles': u'New York City'})
        self.assertEqual(item._link._title, '-1')
        self.assertFalse(hasattr(item, 'id'))
        self.assertFalse(hasattr(item, '_content'))
        self.assertEqual(item.title(), 'Q60')
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        item.get()
        self.assertTrue(item.exists())

    def test_fromPage_invalid_title(self):
        page = pywikibot.Page(pywikibot.page.Link("[]", self.site))
        self.assertRaises(pywikibot.InvalidTitle, pywikibot.ItemPage.fromPage, page)

    def _test_fromPage_noitem(self, link):
        """Helper function to test a page without an associated item.

        It tests two of the ways to fetch an item:
        1. the Page already has props, which should contain a item id if
           present, and that item id is used to instantiate the item, and
        2. the page doesnt have props, in which case the site&titles is
           used to lookup the item id, but that lookup occurs after
           instantiation, during the first attempt to use the data item.
        """
        for props in [True, False]:
            for method in ['title', 'get', 'getID', 'exists']:
                page = pywikibot.Page(link)
                if props:
                    page.properties()

                item = pywikibot.ItemPage.fromPage(page, lazy_load=True)

                self.assertFalse(hasattr(item, 'id'))
                self.assertTrue(hasattr(item, '_title'))
                self.assertTrue(hasattr(item, '_site'))
                self.assertFalse(hasattr(item, '_content'))

                self.assertEqual(item._link._title, '-1')
                # the method 'exists' does not raise an exception
                if method == 'exists':
                    self.assertFalse(item.exists())
                else:
                    self.assertRaises(pywikibot.NoPage, getattr(item, method))

                # The invocation above of a fetching method shouldnt change
                # the local item, but it does!  The title changes to '-1'.
                #
                # However when identifying the item for 'en:Test page'
                # (a deleted page), the exception handling is smarter, and no
                # local data is modified in this scenario.  This case is
                # separately tested in test_fromPage_missing_lazy.
                if link.title != 'Test page':
                    self.assertEqual(item._link._title, '-1')

                self.assertTrue(hasattr(item, '_content'))

                self.assertFalse(item.exists())

                page = pywikibot.Page(link)
                if props:
                    page.properties()

                # by default, fromPage should always raise the same exception
                self.assertRaises(pywikibot.NoPage,
                                  pywikibot.ItemPage.fromPage, page)

    def test_fromPage_redirect(self):
        # this is a redirect, and should not have a wikidata item
        link = pywikibot.page.Link("Main page", self.site)
        self._test_fromPage_noitem(link)

    def test_fromPage_missing(self):
        # this is a deleted page, and should not have a wikidata item
        link = pywikibot.page.Link("Test page", self.site)
        self._test_fromPage_noitem(link)

    def test_fromPage_noitem(self):
        # this is a new page, and should not have a wikidata item yet
        page = _get_test_unconnected_page(self.site)
        link = page._link
        self._test_fromPage_noitem(link)

    def test_fromPage_missing_lazy(self):
        """Test lazy loading of item from nonexistent source page."""
        # this is a deleted page, and should not have a wikidata item
        link = pywikibot.page.Link("Test page", self.site)
        page = pywikibot.Page(link)
        # ItemPage.fromPage should raise an exception when not lazy loading
        # and that exception should refer to the source title 'Test page'
        # not the Item being created.
        self.assertRaisesRegex(pywikibot.NoPage, 'Test page',
                               pywikibot.ItemPage.fromPage,
                               page, lazy_load=False)

        item = pywikibot.ItemPage.fromPage(page, lazy_load=True)

        # Now verify that delay loading will result in the desired semantics.
        # It should not raise NoPage on the wikibase item which has a title
        # like '-1' or 'Null', as that is useless to determine the cause
        # without a full debug log.
        # It should raise NoPage on the source page, with title 'Test page'
        # as that is what the bot operator needs to see in the log output.
        self.assertRaisesRegex(pywikibot.NoPage, 'Test page', item.get)


class TestRedirects(WikidataTestCase):

    """Test redirect and non-redirect items."""

    def test_normal_item(self):
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata, 'Q1')
        self.assertFalse(item.isRedirectPage())
        self.assertRaises(pywikibot.IsNotRedirectPage, item.getRedirectTarget)

    def test_redirect_item(self):
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata, 'Q10008448')
        item.get(get_redirect=True)
        target = pywikibot.ItemPage(wikidata, 'Q8422626')
        self.assertTrue(item.isRedirectPage())
        self.assertEqual(item.getRedirectTarget(), target)
        self.assertIsInstance(item.getRedirectTarget(), pywikibot.ItemPage)
        self.assertRaises(pywikibot.IsRedirectPage, item.get)


class TestPropertyPage(WikidataTestCase):

    """Test PropertyPage."""

    def test_property_empty_property(self):
        """Test creating a PropertyPage without a title."""
        wikidata = self.get_repo()
        self.assertRaises(pywikibot.Error, pywikibot.PropertyPage, wikidata)

    def test_globe_coordinate(self):
        """Test a coordinate PropertyPage has the correct type."""
        wikidata = self.get_repo()
        property_page = pywikibot.PropertyPage(wikidata, 'P625')
        self.assertEqual(property_page.type, 'globe-coordinate')
        self.assertEqual(property_page.getType(), 'globecoordinate')

        claim = pywikibot.Claim(wikidata, 'P625')
        self.assertEqual(claim.type, 'globe-coordinate')
        self.assertEqual(claim.getType(), 'globecoordinate')

    def test_get(self):
        wikidata = self.get_repo()
        property_page = pywikibot.PropertyPage(wikidata, 'P625')
        property_page.get()
        self.assertEqual(property_page.type, 'globe-coordinate')

    def test_new_claim(self):
        """Test that PropertyPage.newClaim uses cached datatype."""
        wikidata = self.get_repo()
        property_page = pywikibot.PropertyPage(wikidata, 'P625')
        property_page.get()
        claim = property_page.newClaim()
        self.assertEqual(claim.type, 'globe-coordinate')

        # Now verify that it isnt fetching the type from the property
        # data in the repo by setting the cache to the incorrect type
        # and checking that it is the cached value that is used.
        property_page._type = 'wikibase-item'
        claim = property_page.newClaim()
        self.assertEqual(claim.type, 'wikibase-item')


class TestClaimSetValue(WikidataTestCase):

    """Test setting claim values."""

    def test_set_website(self):
        """Test setting claim of url type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P856')
        self.assertEqual(claim.type, 'url')
        claim.setTarget('https://en.wikipedia.org/')
        self.assertEqual(claim.target, 'https://en.wikipedia.org/')

    def test_set_WbMonolingualText(self):
        """Test setting claim of monolingualtext type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P1450')
        self.assertEqual(claim.type, 'monolingualtext')
        target = pywikibot.WbMonolingualText(text='Test this!', language='en')
        claim.setTarget(target)
        self.assertEqual(claim.target, target)

    def test_set_math(self):
        """Test setting claim of math type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P2535')
        self.assertEqual(claim.type, 'math')
        claim.setTarget('a^2 + b^2 = c^2')
        self.assertEqual(claim.target, 'a^2 + b^2 = c^2')

    def test_set_date(self):
        """Test setting claim of time type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P569')
        self.assertEqual(claim.type, 'time')
        claim.setTarget(pywikibot.WbTime(year=2001, month=1, day=1, site=wikidata))
        self.assertEqual(claim.target.year, 2001)
        self.assertEqual(claim.target.month, 1)
        self.assertEqual(claim.target.day, 1)

    def test_set_incorrect_target_value(self):
        """Test setting claim of the incorrect value."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P569')
        self.assertRaises(ValueError, claim.setTarget, 'foo')
        claim = pywikibot.Claim(wikidata, 'P856')
        self.assertRaises(ValueError, claim.setTarget, pywikibot.WbTime(2001, site=wikidata))
        claim = pywikibot.Claim(wikidata, 'P1450')
        self.assertRaises(ValueError, claim.setTarget, 'foo')


class TestItemBasePageMethods(WikidataTestCase, BasePageMethodsTestBase):

    """Test behavior of ItemPage methods inherited from BasePage."""

    def setUp(self):
        self._page = ItemPage(self.get_repo(), 'Q60')
        super(TestItemBasePageMethods, self).setUp()

    def test_basepage_methods(self):
        """Test ItemPage methods inherited from superclass BasePage."""
        self._test_invoke()
        self._test_no_wikitext()


class TestPageMethodsWithItemTitle(WikidataTestCase, BasePageMethodsTestBase):

    """Test behavior of Page methods for wikibase item."""

    def setUp(self):
        self._page = pywikibot.Page(self.site, 'Q60')
        super(TestPageMethodsWithItemTitle, self).setUp()

    def test_basepage_methods(self):
        """Test Page methods inherited from superclass BasePage with Q60."""
        self._test_invoke()
        self._test_no_wikitext()


class TestDryPageGetNotImplemented(DefaultWikibaseClientTestCase,
                                   DeprecationTestCase):

    """Test not implement get arguments of WikibasePage classes."""

    dry = True

    def test_base_get_args(self):
        """Test WikibasePage.get() with sysop argument."""
        item = WikibasePage(self.repo, 'Q1')
        # avoid loading anything
        item._content = {}
        self.assertRaises(NotImplementedError,
                          item.get, force=True, sysop=True)
        self.assertRaises(NotImplementedError,
                          item.get, force=False, sysop=True)
        self.assertRaises(NotImplementedError,
                          item.get, force=False, sysop=False)
        self.assertRaises(NotImplementedError,
                          item.get, sysop=True)

    def test_item_get_args(self):
        """Test ItemPage.get() with sysop argument."""
        item = pywikibot.ItemPage(self.repo, 'Q1')
        item._content = {}
        self.assertRaises(NotImplementedError, item.get, sysop=True)

    def test_property_get_args(self):
        """Test PropertyPage.get() with sysop argument."""
        pp = pywikibot.PropertyPage(self.repo, 'P1')
        pp._content = {}
        self.assertRaises(NotImplementedError, pp.get, sysop=True)


class TestLinks(WikidataTestCase):

    """Test cases to test links stored in Wikidata.

    Uses a stored data file for the wikibase item.
    However wikibase creates site objects for each sitelink, and the unit test
    directly creates a Site for 'wikipedia:af' to use in a comparison.
    """

    sites = {
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata',
        },
        'afwiki': {
            'family': 'wikipedia',
            'code': 'af',
        }
    }

    def setUp(self):
        super(TestLinks, self).setUp()
        self.wdp = pywikibot.ItemPage(self.get_repo(), 'Q60')
        self.wdp.id = 'Q60'
        with open(join_pages_path('Q60_only_sitelinks.wd')) as f:
            self.wdp._content = json.load(f)
        self.wdp.get()

    def test_iterlinks_page_object(self):
        page = [pg for pg in self.wdp.iterlinks() if pg.site.code == 'af'][0]
        self.assertEqual(page, pywikibot.Page(self.get_site('afwiki'), u'New York Stad'))

    def test_iterlinks_filtering(self):
        wikilinks = list(self.wdp.iterlinks('wikipedia'))
        wvlinks = list(self.wdp.iterlinks('wikivoyage'))

        self.assertEqual(len(wikilinks), 3)
        self.assertEqual(len(wvlinks), 2)


class TestWriteNormalizeLang(TestCase):

    """Test cases for routines that normalize languages in a dict.

    Exercises WikibasePage._normalizeLanguages with data that is
    not normalized and data which is already normalized.
    """

    family = 'wikipedia'
    code = 'en'

    dry = True

    def setUp(self):
        super(TestWriteNormalizeLang, self).setUp()
        self.site = self.get_site()
        self.lang_out = {'en': 'foo'}

    def test_normalize_lang(self):
        lang_in = {self.site: 'foo'}

        response = WikibasePage._normalizeLanguages(lang_in)
        self.assertEqual(response, self.lang_out)

    def test_normalized_lang(self):
        response = WikibasePage._normalizeData(
            copy.deepcopy(self.lang_out))
        self.assertEqual(response, self.lang_out)


class TestWriteNormalizeData(TestCase):

    """Test cases for routines that normalize data for writing to Wikidata.

    Exercises WikibasePage._normalizeData with data that is not normalized
    and data which is already normalized.
    """

    net = False

    def setUp(self):
        super(TestWriteNormalizeData, self).setUp()
        self.data_out = {
            'aliases': {'en': [{'language': 'en', 'value': 'Bah'}]},
            'labels': {'en': {'language': 'en', 'value': 'Foo'}},
        }

    def test_normalize_data(self):
        data_in = {
            'aliases': {'en': ['Bah']},
            'labels': {'en': 'Foo'},
        }

        response = WikibasePage._normalizeData(data_in)
        self.assertEqual(response, self.data_out)

    def test_normalized_data(self):
        response = WikibasePage._normalizeData(
            copy.deepcopy(self.data_out))
        self.assertEqual(response, self.data_out)


class TestPreloadingItemGenerator(TestCase):

    """Test preloading item generator."""

    family = 'wikidata'
    code = 'wikidata'

    def test_non_item_gen(self):
        """Test TestPreloadingItemGenerator with ReferringPageGenerator."""
        site = self.get_site()
        instance_of_page = pywikibot.Page(site, 'Property:P31')
        ref_gen = pagegenerators.ReferringPageGenerator(instance_of_page, total=5)
        gen = pagegenerators.PreloadingItemGenerator(ref_gen)
        self.assertTrue(all(isinstance(item, pywikibot.ItemPage) for item in gen))


class TestNamespaces(WikidataTestCase):

    """Test cases to test namespaces of Wikibase entities."""

    def test_empty_wikibase_page(self):
        # As a base class it should be able to instantiate
        # it with minimal arguments
        wikidata = self.get_repo()
        page = pywikibot.page.WikibasePage(wikidata)
        self.assertRaises(AttributeError, page.namespace)
        page = pywikibot.page.WikibasePage(wikidata, title='')
        self.assertRaises(AttributeError, page.namespace)

        page = pywikibot.page.WikibasePage(wikidata, ns=0)
        self.assertEqual(page.namespace(), 0)
        page = pywikibot.page.WikibasePage(wikidata, entity_type='item')
        self.assertEqual(page.namespace(), 0)

        page = pywikibot.page.WikibasePage(wikidata, ns=120)
        self.assertEqual(page.namespace(), 120)
        page = pywikibot.page.WikibasePage(wikidata, title='', ns=120)
        self.assertEqual(page.namespace(), 120)
        page = pywikibot.page.WikibasePage(wikidata, entity_type='property')
        self.assertEqual(page.namespace(), 120)

        # mismatch in namespaces
        self.assertRaises(ValueError, pywikibot.page.WikibasePage, wikidata,
                          ns=0, entity_type='property')
        self.assertRaises(ValueError, pywikibot.page.WikibasePage, wikidata,
                          ns=120, entity_type='item')

    def test_wikibase_link_namespace(self):
        """Test the title resolved to a namespace correctly."""
        wikidata = self.get_repo()
        # title without any namespace clues (ns or entity_type)
        # should verify the Link namespace is appropriate
        page = pywikibot.page.WikibasePage(wikidata, title='Q6')
        self.assertEqual(page.namespace(), 0)
        page = pywikibot.page.WikibasePage(wikidata, title='Property:P60')
        self.assertEqual(page.namespace(), 120)

    def test_wikibase_namespace_selection(self):
        """Test various ways to correctly specify the namespace."""
        wikidata = self.get_repo()

        page = pywikibot.page.ItemPage(wikidata, 'Q60')
        self.assertEqual(page.namespace(), 0)
        page.get()

        page = pywikibot.page.ItemPage(wikidata, title='Q60')
        self.assertEqual(page.namespace(), 0)
        page.get()

        page = pywikibot.page.WikibasePage(wikidata, title='Q60', ns=0)
        self.assertEqual(page.namespace(), 0)
        page.get()

        page = pywikibot.page.WikibasePage(wikidata, title='Q60',
                                           entity_type='item')
        self.assertEqual(page.namespace(), 0)
        page.get()

        page = pywikibot.page.PropertyPage(wikidata, 'Property:P6')
        self.assertEqual(page.namespace(), 120)
        page.get()

        page = pywikibot.page.PropertyPage(wikidata, 'P6')
        self.assertEqual(page.namespace(), 120)
        page.get()

        page = pywikibot.page.WikibasePage(wikidata, title='Property:P6')
        self.assertEqual(page.namespace(), 120)
        page.get()

        page = pywikibot.page.WikibasePage(wikidata, title='P6', ns=120)
        self.assertEqual(page.namespace(), 120)
        page.get()

        page = pywikibot.page.WikibasePage(wikidata, title='P6',
                                           entity_type='property')
        self.assertEqual(page.namespace(), 120)
        page.get()

    def test_wrong_namespaces(self):
        """Test incorrect namespaces for Wikibase entities."""
        wikidata = self.get_repo()
        # All subclasses of WikibasePage raise a ValueError
        # if the namespace for the page title is not correct
        self.assertRaises(ValueError, pywikibot.page.WikibasePage, wikidata,
                          title='Wikidata:Main Page')
        self.assertRaises(ValueError, pywikibot.ItemPage, wikidata, 'File:Q1')
        self.assertRaises(ValueError, pywikibot.PropertyPage, wikidata, 'File:P60')

    def test_item_unknown_namespace(self):
        """Test unknown namespaces for Wikibase entities."""
        # The 'Invalid:' is not a known namespace, so is parsed to be
        # part of the title in namespace 0
        # TODO: These items have inappropriate titles, which should
        #       raise an error.
        wikidata = self.get_repo()
        self.assertRaises(pywikibot.InvalidTitle,
                          pywikibot.ItemPage,
                          wikidata,
                          'Invalid:Q1')


class TestAlternateNamespaces(WikidataTestCase):

    """Test cases to test namespaces of Wikibase entities."""

    cached = False
    dry = True

    @classmethod
    def setUpClass(cls):
        super(TestAlternateNamespaces, cls).setUpClass()

        cls.get_repo()._namespaces = NamespacesDict({
            90: Namespace(id=90,
                          case='first-letter',
                          canonical_name='Item',
                          defaultcontentmodel='wikibase-item'),
            92: Namespace(id=92,
                          case='first-letter',
                          canonical_name='Prop',
                          defaultcontentmodel='wikibase-property')
        })

    def test_alternate_item_namespace(self):
        item = pywikibot.ItemPage(self.repo, 'Q60')
        self.assertEqual(item.namespace(), 90)
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.title(), 'Item:Q60')
        self.assertEqual(item._defined_by(), {'ids': 'Q60'})

        item = pywikibot.ItemPage(self.repo, 'Item:Q60')
        self.assertEqual(item.namespace(), 90)
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.title(), 'Item:Q60')
        self.assertEqual(item._defined_by(), {'ids': 'Q60'})

    def test_alternate_property_namespace(self):
        prop = pywikibot.PropertyPage(self.repo, 'P21')
        self.assertEqual(prop.namespace(), 92)
        self.assertEqual(prop.id, 'P21')
        self.assertEqual(prop.title(), 'Prop:P21')
        self.assertEqual(prop._defined_by(), {'ids': 'P21'})

        prop = pywikibot.PropertyPage(self.repo, 'Prop:P21')
        self.assertEqual(prop.namespace(), 92)
        self.assertEqual(prop.id, 'P21')
        self.assertEqual(prop.title(), 'Prop:P21')
        self.assertEqual(prop._defined_by(), {'ids': 'P21'})


class TestOwnClient(TestCase):

    """Test that a data repository family can be its own client."""

    sites = {
        # The main Wikidata is its own client.
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata',
        },
        # test.wikidata is also
        'wikidatatest': {
            'family': 'wikidata',
            'code': 'test',
        },
    }

    def test_own_client(self, key):
        """Test that a data repository family can be its own client."""
        site = self.get_site(key)

        page = pywikibot.Page(site, 'Wikidata:Main Page')
        item = pywikibot.ItemPage.fromPage(page)
        self.assertEqual(item.site, site)


class TestUnconnectedClient(TestCase):

    """Test clients not connected to a data repository."""

    sites = {
        # Wikispecies is not supported by Wikidata yet.
        'species': {
            'family': 'species',
            'code': 'species',
            'page_title': 'Main Page',
        },
        # fr.wiktionary is not supported by Wikidata yet.
        'frwikt': {
            'family': 'wiktionary',
            'code': 'fr',
            'page_title': 'and',
        },
    }

    dry = True

    def test_not_supported_family(self, key):
        """Test that family without a data repository causes error."""
        site = self.get_site(key)

        self.wdp = pywikibot.Page(site, self.sites[key]['page_title'])
        self.assertRaises(pywikibot.WikiBaseError,
                          pywikibot.ItemPage.fromPage, self.wdp)
        self.assertRaisesRegex(pywikibot.WikiBaseError,
                               'no transcluded data',
                               self.wdp.data_item)


class TestJSON(WikidataTestCase):

    """Test cases to test toJSON() functions."""

    dry = True

    def setUp(self):
        super(TestJSON, self).setUp()
        wikidata = self.get_repo()
        self.wdp = pywikibot.ItemPage(wikidata, 'Q60')
        self.wdp.id = 'Q60'
        with open(join_pages_path('Q60.wd')) as f:
            self.wdp._content = json.load(f)
        self.wdp.get()
        del self.wdp._content['id']
        del self.wdp._content['type']
        del self.wdp._content['lastrevid']

    def test_itempage_json(self):
        old = json.dumps(self.wdp._content, indent=2, sort_keys=True)
        new = json.dumps(self.wdp.toJSON(), indent=2, sort_keys=True)

        self.assertEqual(old, new)

    def test_json_diff(self):
        del self.wdp.labels['en']
        del self.wdp.claims['P213']
        expected = {
            'labels': {
                'en': {
                    'language': 'en',
                    'value': ''
                }
            },
            'claims': {
                'P213': [
                    {
                        'id': 'Q60$0427a236-4120-7d00-fa3e-e23548d4c02d',
                        'remove': ''
                    }
                ]
            }
        }
        diff = self.wdp.toJSON(diffto=self.wdp._content)
        self.assertEqual(diff, expected)


class TestDeprecatedDataSiteMethods(WikidataTestCase, DeprecationTestCase):

    """Test deprecated DataSite get_* methods."""

    cached = True

    def test_get_info(self):
        """Test get_info."""
        data = self.repo.get_info(60)
        self.assertOneDeprecation()
        self.assertIsInstance(data, dict)
        self.assertIn('title', data)
        self.assertEqual(data['title'], 'Q60')

    def test_get_labels(self):
        """Test get_labels."""
        data = self.repo.get_labels(60)
        self.assertOneDeprecation()
        self.assertIsInstance(data, dict)
        self.assertIn('en', data)

    def test_get_aliases(self):
        """Test get_aliases."""
        data = self.repo.get_aliases(60)
        self.assertOneDeprecation()
        self.assertIsInstance(data, dict)
        self.assertIn('en', data)

    def test_get_descriptions(self):
        """Test get_descriptions."""
        data = self.repo.get_descriptions(60)
        self.assertOneDeprecation()
        self.assertIsInstance(data, dict)
        self.assertIn('en', data)

    def test_get_sitelinks(self):
        """Test get_sitelinks."""
        data = self.repo.get_sitelinks(60)
        self.assertOneDeprecation()
        self.assertIsInstance(data, dict)
        self.assertIn('enwiki', data)

    def test_get_urls(self):
        """Test get_urls."""
        data = self.repo.get_urls(60)
        self.assertOneDeprecation()
        self.assertIsInstance(data, dict)
        self.assertIn('enwiki', data)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
