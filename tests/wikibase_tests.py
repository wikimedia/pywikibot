#!/usr/bin/env python3
"""Tests for the Wikidata parts of the page module."""
#
# (C) Pywikibot team, 2008-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import copy
import json
import unittest
from contextlib import suppress

import pywikibot
from pywikibot import pagegenerators
from pywikibot.exceptions import (
    InvalidTitleError,
    IsNotRedirectPageError,
    IsRedirectPageError,
    NoPageError,
    UnknownExtensionError,
    WikiBaseError,
)
from pywikibot.page import ItemPage, PropertyPage, WikibasePage
from pywikibot.site import Namespace, NamespacesDict
from pywikibot.tools import suppress_warnings
from tests import WARN_SITE_CODE, join_pages_path
from tests.aspects import TestCase, WikidataTestCase
from tests.basepage import (
    BasePageLoadRevisionsCachingTestBase,
    BasePageMethodsTestBase,
)


# fetch a page which is very likely to be unconnected, which doesn't have
# a generator, and unit tests may be used to test old versions of pywikibot
def _get_test_unconnected_page(site):
    """Get unconnected page from site for tests."""
    gen = pagegenerators.NewpagesPageGenerator(site=site, total=10,
                                               namespaces=[1])
    for page in gen:
        if not page.properties().get('wikibase_item'):
            return page
    return None  # pragma: no cover


class TestLoadRevisionsCaching(BasePageLoadRevisionsCachingTestBase,
                               WikidataTestCase):

    """Test site.loadrevisions() caching."""

    def setup_page(self) -> None:
        """Set up test page."""
        self._page = ItemPage(self.get_repo(), 'Q15169668')

    def test_page_text(self) -> None:
        """Test site.loadrevisions() with Page.text."""
        with suppress_warnings(WARN_SITE_CODE, category=UserWarning):
            self._test_page_text()


class TestGeneral(WikidataTestCase):

    """General Wikibase tests."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test class."""
        super().setUpClass()
        enwiki = pywikibot.Site('en', 'wikipedia')
        cls.mainpage = pywikibot.Page(pywikibot.page.Link('Main Page', enwiki))

    def testWikibase(self) -> None:
        """Wikibase tests."""
        repo = self.get_repo()
        item_namespace = repo.namespaces[0]
        self.assertEqual(item_namespace.defaultcontentmodel, 'wikibase-item')
        item = ItemPage.fromPage(self.mainpage)
        self.assertIsInstance(item, ItemPage)
        self.assertEqual(item.getID(), 'Q5296')
        self.assertEqual(item.title(), 'Q5296')
        self.assertIn('en', item.labels)
        self.assertTrue(
            item.labels['en'].lower().endswith('main page'),
            msg=f"\nitem.labels['en'] of item Q5296 is {item.labels['en']!r}")
        self.assertIn('en', item.aliases)
        self.assertIn('home page', (a.lower() for a in item.aliases['en']))
        self.assertEqual(item.namespace(), 0)
        item2 = ItemPage(repo, 'q5296')
        self.assertEqual(item2.getID(), 'Q5296')
        item2.get()
        self.assertEndsWith(item2.labels['en'].lower(), 'main page')
        prop = PropertyPage(repo, 'Property:P21')
        self.assertEqual(prop.type, 'wikibase-item')
        self.assertEqual(prop.namespace(), 120)
        claim = pywikibot.Claim(repo, 'p21')
        regex = r' is not type .+\.$'
        with self.assertRaisesRegex(ValueError, regex):
            claim.setTarget(value='test')
        claim.setTarget(ItemPage(repo, 'q1'))
        self.assertEqual(claim._formatValue(), {'entity-type': 'item',
                                                'numeric-id': 1})

    def test_cmp(self) -> None:
        """Test WikibasePage comparison."""
        self.assertEqual(ItemPage.fromPage(self.mainpage),
                         ItemPage(self.get_repo(), 'q5296'))


class TestWikibaseParser(WikidataTestCase):

    """Test passing various datatypes to wikibase parser."""

    def test_wbparse_strings(self) -> None:
        """Test that strings return unchanged."""
        test_list = ['test string', 'second test']
        parsed_strings = self.site.parsevalue('string', test_list)
        self.assertEqual(parsed_strings, test_list)

    def test_wbparse_time(self) -> None:
        """Test parsing of a time value."""
        parsed_date = self.site.parsevalue(
            'time', ['1994-02-08'], {'precision': 9})[0]
        self.assertEqual(parsed_date['time'], '+1994-02-08T00:00:00Z')
        self.assertEqual(parsed_date['precision'], 9)

    def test_wbparse_quantity(self) -> None:
        """Test parsing of quantity values."""
        parsed_quantities = self.site.parsevalue(
            'quantity',
            ['1.90e-9+-0.20e-9', '1000000.00000000054321+-0', '-123+-1',
             '2.70e34+-1e32'])
        self.assertEqual(parsed_quantities[0]['amount'], '+0.00000000190')
        self.assertEqual(parsed_quantities[0]['upperBound'], '+0.00000000210')
        self.assertEqual(parsed_quantities[0]['lowerBound'], '+0.00000000170')
        self.assertEqual(parsed_quantities[1]['amount'],
                         '+1000000.00000000054321')
        self.assertEqual(parsed_quantities[1]['upperBound'],
                         '+1000000.00000000054321')
        self.assertEqual(parsed_quantities[1]['lowerBound'],
                         '+1000000.00000000054321')
        self.assertEqual(parsed_quantities[2]['amount'], '-123')
        self.assertEqual(parsed_quantities[2]['upperBound'], '-122')
        self.assertEqual(parsed_quantities[2]['lowerBound'], '-124')
        self.assertEqual(parsed_quantities[3]['amount'],
                         '+27000000000000000000000000000000000')
        self.assertEqual(parsed_quantities[3]['upperBound'],
                         '+27100000000000000000000000000000000')
        self.assertEqual(parsed_quantities[3]['lowerBound'],
                         '+26900000000000000000000000000000000')

    def test_wbparse_raises_valueerror(self) -> None:
        """Test invalid value condition."""
        with self.assertRaises(ValueError):
            self.site.parsevalue('quantity', ['Not a quantity'])


class TestLoadUnknownType(WikidataTestCase):

    """Test unknown datatypes being loaded as WbUnknown."""

    dry = True

    def setUp(self) -> None:
        """Set up test."""
        super().setUp()
        wikidata = self.get_repo()
        self.wdp = ItemPage(wikidata, 'Q60')
        self.wdp.id = 'Q60'
        with open(join_pages_path('Q60_unknown_datatype.wd')) as f:
            self.wdp._content = json.load(f)

    def test_load_unknown(self) -> None:
        """Ensure unknown value is loaded but raises a warning."""
        self.wdp.get()
        unknown_value = self.wdp.claims['P99999'][0].getTarget()
        self.assertIsInstance(unknown_value, pywikibot.WbUnknown)
        self.assertEqual(unknown_value.warning,
                         'foo-unknown-bar datatype is not supported yet.')


class TestItemPageExtensibility(TestCase):

    """Test ItemPage extensibility."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def test_ItemPage_extensibility(self) -> None:
        """Test ItemPage extensibility."""
        class MyItemPage(ItemPage):

            """Dummy ItemPage subclass."""

        page = pywikibot.Page(self.site, 'foo')
        self.assertIsInstance(MyItemPage.fromPage(page, lazy_load=True),
                              MyItemPage)


class TestItemLoad(WikidataTestCase):

    """Test item creation.

    Tests for item creation include:
    1. by Q id
    2. ItemPage.fromPage(page)
    3. ItemPage.fromPage(page_with_props_loaded)
    4. ItemPage.from_entity_uri(site, uri)

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

    keys = 'en', 'mul'  # either en or mul may missing
    labels = 'New York', 'New York City'  # label could change

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test class."""
        super().setUpClass()
        cls.site = cls.get_site('enwiki')

    def setUp(self) -> None:
        """Set up test."""
        super().setUp()
        self.nyc = pywikibot.Page(pywikibot.page.Link(self.labels[1],
                                                      self.site))

    def test_item_normal(self) -> None:
        """Test normal wikibase item."""
        wikidata = self.get_repo()
        item = ItemPage(wikidata, 'Q60')
        self.assertEqual(item._link._title, 'Q60')
        self.assertEqual(item._defined_by(), {'ids': 'Q60'})
        self.assertEqual(item.id, 'Q60')
        self.assertNotHasAttr(item, '_title')
        self.assertNotHasAttr(item, '_site')
        self.assertEqual(item.title(), 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        self.assertNotHasAttr(item, '_content')
        item.get()
        self.assertHasAttr(item, '_content')

    def test_item_lazy_initialization(self) -> None:
        """Test that Wikibase items are properly initialized lazily."""
        wikidata = self.get_repo()
        item = ItemPage(wikidata, 'Q60')
        attrs = ['_content', 'labels', 'descriptions', 'aliases',
                 'claims', 'sitelinks']
        for attr in attrs:
            with self.subTest(attr=attr, note='before loading'):
                # hasattr() loads the attributes; use item.__dict__ for tests
                self.assertNotIn(attr, item.__dict__)

        item.labels  # trigger loading
        for attr in attrs:
            with self.subTest(attr=attr, note='after loading'):
                self.assertIn(attr, item.__dict__)

    def test_load_item_set_id(self) -> None:
        """Test setting item.id attribute on empty item."""
        wikidata = self.get_repo()
        item = ItemPage(wikidata, '-1')
        self.assertEqual(item._link._title, '-1')
        item.id = 'Q60'
        self.assertNotHasAttr(item, '_content')
        self.assertEqual(item.getID(), 'Q60')
        self.assertNotHasAttr(item, '_content')
        item.get()
        self.assertHasAttr(item, '_content')
        key = next((k for k in self.keys if k in item.labels), None)
        self.assertIsNotNone(key,
                             f'Expected one of {self.keys} in item.labels')
        # label could change
        self.assertIn(item.labels[key], self.labels)
        self.assertEqual(item.title(), 'Q60')

    def test_reuse_item_set_id(self) -> None:
        """Test modifying item.id attribute.

        Some scripts are using item.id = 'Q60' semantics, which does
        work but modifying item.id does not currently work, and this
        test highlights that it breaks silently.
        """
        wikidata = self.get_repo()
        item = ItemPage(wikidata, 'Q60')
        item.get()
        key = next((k for k in self.keys if k in item.labels), None)
        self.assertIsNotNone(key,
                             f'Expected one of {self.keys} in item.labels')
        old_label = item.labels[key]

        # When the id attribute is modified, the ItemPage goes into
        # an inconsistent state.
        item.id = 'Q5296'
        # The title is updated correctly
        self.assertEqual(item.title(), 'Q5296')

        # This del has no effect on the test; it is here to demonstrate that
        # it doesn't help to clear this piece of saved state.
        del item._content
        # The labels are not updated; assertion showing undesirable behaviour:
        self.assertEqual(item.labels[key], old_label)
        self.assertIn(item.labels[key], self.labels)

    def test_empty_item(self) -> None:
        """Test empty wikibase item.

        should not raise an error as the constructor only requires the
        site parameter, with the title parameter defaulted to None.
        """
        wikidata = self.get_repo()
        item = ItemPage(wikidata)
        self.assertEqual(item._link._title, '-1')
        self.assertLength(item.labels, 0)
        self.assertEqual(str(item.labels), 'LanguageDict({})')
        self.assertEqual(repr(item.labels), 'LanguageDict({})')
        self.assertLength(item.descriptions, 0)
        self.assertLength(item.aliases, 0)
        self.assertEqual(str(item.aliases), 'AliasesDict({})')
        self.assertEqual(repr(item.aliases), 'AliasesDict({})')
        self.assertLength(item.claims, 0)
        self.assertLength(item.sitelinks, 0)

    def test_item_invalid_titles(self) -> None:
        """Test invalid titles of wikibase items."""
        wikidata = self.get_repo()

        regex = r"^'.+' is not a valid .+ page title$"
        for title in ['null', 'NULL', 'None',
                      '-2', '1', '0', '+1', 'Q0',
                      'Q0.5', 'Q', 'Q-1', 'Q+1']:
            with self.assertRaisesRegex(InvalidTitleError, regex):
                ItemPage(wikidata, title)

        regex = r"^Item's title cannot be empty$"
        with self.assertRaisesRegex(InvalidTitleError, regex):
            ItemPage(wikidata, '')

    def test_item_untrimmed_title(self) -> None:
        """Test intrimmed titles of wikibase items.

        Spaces in the title should not cause an error.
        """
        wikidata = self.get_repo()
        item = ItemPage(wikidata, ' Q60 ')
        self.assertEqual(item._link._title, 'Q60')
        self.assertEqual(item.title(), 'Q60')
        item.get()

    def test_item_missing(self) -> None:
        """Test nmissing item."""
        wikidata = self.get_repo()
        # this item has never existed
        item = ItemPage(wikidata, 'Q7')
        self.assertEqual(item._link._title, 'Q7')
        self.assertEqual(item.title(), 'Q7')
        self.assertNotHasAttr(item, '_content')
        self.assertEqual(item.id, 'Q7')
        self.assertEqual(item.getID(), 'Q7')
        numeric_id = item.getID(numeric=True)
        self.assertIsInstance(numeric_id, int)
        self.assertEqual(numeric_id, 7)
        self.assertNotHasAttr(item, '_content')
        regex = r"^Page .+ doesn't exist\.$"
        with self.assertRaisesRegex(NoPageError, regex):
            item.get()
        self.assertHasAttr(item, '_content')
        self.assertEqual(item.id, 'Q7')
        self.assertEqual(item.getID(), 'Q7')
        self.assertEqual(item._link._title, 'Q7')
        self.assertEqual(item.title(), 'Q7')
        with self.assertRaisesRegex(NoPageError, regex):
            item.get()
        self.assertHasAttr(item, '_content')
        self.assertEqual(item._link._title, 'Q7')
        self.assertEqual(item.getID(), 'Q7')
        self.assertEqual(item.title(), 'Q7')

    def test_item_never_existed(self) -> None:
        """Test non-existent item."""
        wikidata = self.get_repo()
        # this item has not been created
        item = ItemPage(wikidata, 'Q9999999999999999999')
        self.assertFalse(item.exists())
        self.assertEqual(item.getID(), 'Q9999999999999999999')
        regex = r"^Page .+ doesn't exist\.$"
        with self.assertRaisesRegex(NoPageError, regex):
            item.get()

    def test_fromPage_noprops(self) -> None:
        """Test item from page without properties."""
        page = self.nyc
        item = ItemPage.fromPage(page)
        self.assertEqual(item._link._title, '-1')
        self.assertHasAttr(item, 'id')
        self.assertHasAttr(item, '_content')
        self.assertEqual(item.title(), 'Q60')
        self.assertHasAttr(item, '_content')
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        item.get()
        self.assertTrue(item.exists())

    def test_fromPage_noprops_with_section(self) -> None:
        """Test item from page with section."""
        page = pywikibot.Page(self.nyc.site, self.nyc.title() + '#foo')
        item = ItemPage.fromPage(page)
        self.assertEqual(item._link._title, '-1')
        self.assertHasAttr(item, 'id')
        self.assertHasAttr(item, '_content')
        self.assertEqual(item.title(), 'Q60')
        self.assertHasAttr(item, '_content')
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        item.get()
        self.assertTrue(item.exists())

    def test_fromPage_props(self) -> None:
        """Test item from page with properties."""
        page = self.nyc
        # fetch page properties
        page.properties()
        item = ItemPage.fromPage(page)
        self.assertEqual(item._link._title, 'Q60')
        self.assertEqual(item.id, 'Q60')
        self.assertNotHasAttr(item, '_content')
        self.assertEqual(item.title(), 'Q60')
        self.assertNotHasAttr(item, '_content')
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        self.assertNotHasAttr(item, '_content')
        item.get()
        self.assertHasAttr(item, '_content')
        self.assertTrue(item.exists())
        item2 = ItemPage.fromPage(page)
        self.assertIs(item, item2)

    def test_fromPage_lazy(self) -> None:
        """Test item from page with lazy_load."""
        title = self.labels[1]
        page = pywikibot.Page(pywikibot.page.Link(title, self.site))
        item = ItemPage.fromPage(page, lazy_load=True)
        self.assertEqual(item._defined_by(),
                         {'sites': 'enwiki', 'titles': title})
        self.assertEqual(item._link._title, '-1')
        self.assertNotHasAttr(item, 'id')
        self.assertNotHasAttr(item, '_content')
        self.assertEqual(item.title(), 'Q60')
        self.assertHasAttr(item, '_content')
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        item.get()
        self.assertTrue(item.exists())

    def _test_fromPage_noitem(self, link) -> None:
        """Helper function to test a page without an associated item.

        It tests two of the ways to fetch an item:
        1. the Page already has props, which should contain an item id if
           present, and that item id is used to instantiate the item, and
        2. the page doesn't have props, in which case the site&titles is
           used to lookup the item id, but that lookup occurs after
           instantiation, during the first attempt to use the data item.
        """
        for props in [True, False]:
            for method in ['title', 'get', 'getID', 'exists']:
                page = pywikibot.Page(link)
                if props:
                    page.properties()

                item = ItemPage.fromPage(page, lazy_load=True)

                self.assertNotHasAttr(item, 'id')
                self.assertHasAttr(item, '_title')
                self.assertHasAttr(item, '_site')
                self.assertNotHasAttr(item, '_content')

                self.assertEqual(item._link._title, '-1')
                # the method 'exists' does not raise an exception
                if method == 'exists':
                    self.assertFalse(item.exists())
                else:
                    regex = r"^Page .+ doesn't exist\.$"
                    with self.assertRaisesRegex(NoPageError, regex):
                        getattr(item, method)()

                # The invocation above of a fetching method shouldn't change
                # the local item, but it does! The title changes to '-1'.
                #
                # However when identifying the item for 'en:Test page'
                # (a deleted page), the exception handling is smarter, and no
                # local data is modified in this scenario. This case is
                # separately tested in test_fromPage_missing_lazy.
                if link.title != 'Test page':
                    self.assertEqual(item._link._title, '-1')

                self.assertTrue(hasattr(item, '_content'))

                self.assertFalse(item.exists())

                page = pywikibot.Page(link)
                if props:
                    page.properties()

                # by default, fromPage should always raise the same exception
                regex = r"^Page .+ doesn't exist\.$"
                with self.assertRaisesRegex(NoPageError, regex):
                    ItemPage.fromPage(page)

    def test_fromPage_redirect(self) -> None:
        """Test item from redirect page.

        A redirect should not have a wikidata item.
        """
        link = pywikibot.page.Link('Main page', self.site)
        self._test_fromPage_noitem(link)

    def test_fromPage_missing(self) -> None:
        """Test item from deleted page.

        A deleted page should not have a wikidata item.
        """
        link = pywikibot.page.Link('Test page', self.site)
        self._test_fromPage_noitem(link)

    def test_fromPage_noitem(self) -> None:
        """Test item from new page.

        A new created page should not have a wikidata item yet.
        """
        page = _get_test_unconnected_page(self.site)
        link = page._link
        self._test_fromPage_noitem(link)

    def test_fromPage_missing_lazy(self) -> None:
        """Test lazy loading of item from nonexistent source page."""
        # this is a deleted page, and should not have a wikidata item
        link = pywikibot.page.Link('Test page', self.site)
        page = pywikibot.Page(link)
        # ItemPage.fromPage should raise an exception when not lazy loading
        # and that exception should refer to the source title 'Test page'
        # not the Item being created.
        with self.assertRaisesRegex(NoPageError, 'Test page'):
            ItemPage.fromPage(page, lazy_load=False)

        item = ItemPage.fromPage(page, lazy_load=True)

        # Now verify that delay loading will result in the desired semantics.
        # It should not raise NoPageError on the wikibase item which has a
        # title like '-1' or 'Null', as that is useless to determine the cause
        # without a full debug log.
        # It should raise NoPageError on the source page, with title 'Test
        # page' as that is what the bot operator needs to see in the log
        # output.
        with self.assertRaisesRegex(NoPageError, 'Test page'):
            item.get()

    def test_from_entity_uri(self) -> None:
        """Test ItemPage.from_entity_uri."""
        repo = self.get_repo()
        entity_uri = 'http://www.wikidata.org/entity/Q124'
        self.assertEqual(ItemPage.from_entity_uri(repo, entity_uri),
                         ItemPage(repo, 'Q124'))

    def test_from_entity_uri_not_a_data_repo(self) -> None:
        """Test ItemPage.from_entity_uri with a non-Wikibase site."""
        repo = self.site
        entity_uri = 'http://www.wikidata.org/entity/Q124'
        regex = r' is not a data repository\.$'
        with self.assertRaisesRegex(TypeError, regex):
            ItemPage.from_entity_uri(repo, entity_uri)

    def test_from_entity_uri_wrong_repo(self) -> None:
        """Test ItemPage.from_entity_uri with unexpected item repo."""
        repo = self.get_repo()
        entity_uri = 'http://test.wikidata.org/entity/Q124'
        regex = (r'^The supplied data repository \(.+\) does not '
                 r'correspond to that of the item \(.+\)$')
        with self.assertRaisesRegex(ValueError, regex):
            ItemPage.from_entity_uri(repo, entity_uri)

    def test_from_entity_uri_invalid_title(self) -> None:
        """Test ItemPage.from_entity_uri with an invalid item title format."""
        repo = self.get_repo()
        entity_uri = 'http://www.wikidata.org/entity/Nonsense'
        regex = r"^'.+' is not a valid .+ page title$"
        with self.assertRaisesRegex(InvalidTitleError, regex):
            ItemPage.from_entity_uri(repo, entity_uri)

    def test_from_entity_uri_no_item(self) -> None:
        """Test ItemPage.from_entity_uri with non-existent item."""
        repo = self.get_repo()
        entity_uri = 'http://www.wikidata.org/entity/Q999999999999999999'
        regex = r"^Page .+ doesn't exist\.$"
        with self.assertRaisesRegex(NoPageError, regex):
            ItemPage.from_entity_uri(repo, entity_uri)

    def test_from_entity_uri_no_item_lazy(self) -> None:
        """Test ItemPage.from_entity_uri with lazy loaded non-existent item."""
        repo = self.get_repo()
        entity_uri = 'http://www.wikidata.org/entity/Q999999999999999999'
        expected_item = ItemPage(repo, 'Q999999999999999999')
        self.assertEqual(
            ItemPage.from_entity_uri(repo, entity_uri, lazy_load=True),
            expected_item)

        self.assertFalse(expected_item.exists())  # ensure actually missing


class TestRedirects(WikidataTestCase):

    """Test redirect and non-redirect items."""

    def test_normal_item(self) -> None:
        """Test normal item."""
        wikidata = self.get_repo()
        item = ItemPage(wikidata, 'Q1')
        self.assertFalse(item.isRedirectPage())
        self.assertTrue(item.exists())
        regex = r'^Page .+ is not a redirect page\.$'
        with self.assertRaisesRegex(IsNotRedirectPageError, regex):
            item.getRedirectTarget()

    def test_redirect_item(self) -> None:
        """Test redirect item."""
        wikidata = self.get_repo()
        item = ItemPage(wikidata, 'Q10008448')
        item.get(get_redirect=True)
        target = ItemPage(wikidata, 'Q8422626')
        # tests after get operation
        self.assertTrue(item.isRedirectPage())
        self.assertTrue(item.exists())
        self.assertEqual(item.getRedirectTarget(), target)
        self.assertIsInstance(item.getRedirectTarget(), ItemPage)
        regex = r'^Page .+ is a redirect page\.$'
        with self.assertRaisesRegex(IsRedirectPageError, regex):
            item.get()

    def test_redirect_item_without_get(self) -> None:
        """Test redirect item without explicit get operation."""
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata, 'Q10008448')
        self.assertTrue(item.exists())
        self.assertTrue(item.isRedirectPage())
        target = pywikibot.ItemPage(wikidata, 'Q8422626')
        self.assertEqual(item.getRedirectTarget(), target)


class TestPropertyPage(WikidataTestCase):

    """Test PropertyPage."""

    def test_property_empty_property(self) -> None:
        """Test creating a PropertyPage without a title and datatype."""
        wikidata = self.get_repo()
        regex = r'^"datatype" is required for new property\.$'
        with self.assertRaisesRegex(TypeError, regex):
            PropertyPage(wikidata)

    def test_property_empty_title(self) -> None:
        """Test creating a PropertyPage without a title."""
        wikidata = self.get_repo()
        regex = r"^Property's title cannot be empty$"
        with self.assertRaisesRegex(InvalidTitleError, regex):
            PropertyPage(wikidata, title='')

    def test_globe_coordinate(self) -> None:
        """Test a coordinate PropertyPage has the correct type."""
        wikidata = self.get_repo()
        property_page = PropertyPage(wikidata, 'P625')
        self.assertEqual(property_page.type, 'globe-coordinate')

        claim = pywikibot.Claim(wikidata, 'P625')
        self.assertEqual(claim.type, 'globe-coordinate')

    def test_get(self) -> None:
        """Test PropertyPage.get() method."""
        wikidata = self.get_repo()
        property_page = PropertyPage(wikidata, 'P625')
        property_page.get()
        self.assertEqual(property_page.type, 'globe-coordinate')

    def test_new_claim(self) -> None:
        """Test that PropertyPage.newClaim uses cached datatype."""
        wikidata = self.get_repo()
        property_page = PropertyPage(wikidata, 'P625')
        property_page.get()
        claim = property_page.newClaim()
        self.assertEqual(claim.type, 'globe-coordinate')

        # Now verify that it isn't fetching the type from the property
        # data in the repo by setting the cache to the incorrect type
        # and checking that it is the cached value that is used.
        property_page._type = 'wikibase-item'
        claim = property_page.newClaim()
        self.assertEqual(claim.type, 'wikibase-item')

    def test_as_target(self) -> None:
        """Test that PropertyPage can be used as a value."""
        wikidata = self.get_repo()
        property_page = PropertyPage(wikidata, 'P1687')
        claim = property_page.newClaim()
        claim.setTarget(property_page)
        self.assertEqual(claim.type, 'wikibase-property')
        self.assertEqual(claim.target, property_page)

    @unittest.expectedFailure  # T145971
    def test_exists(self) -> None:
        """Test the exists method of PropertyPage."""
        wikidata = self.get_repo()
        property_page = PropertyPage(wikidata, 'P1687')
        self.assertTrue(property_page.exists())
        # Retry with cached _content.
        self.assertTrue(property_page.exists())


class TestClaim(WikidataTestCase):

    """Test Claim object functionality."""

    def test_claim_eq_simple(self) -> None:
        """Test comparing two claims.

        If they have the same property and value, they are equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        self.assertEqual(claim1, claim2)
        self.assertEqual(claim2, claim1)

    def test_claim_eq_simple_different_value(self) -> None:
        """Test comparing two claims.

        If they have the same property and different values, they are
        not equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q1'))
        self.assertNotEqual(claim1, claim2)
        self.assertNotEqual(claim2, claim1)

    def test_claim_eq_simple_different_rank(self) -> None:
        """Test comparing two claims.

        If they have the same property and value and different ranks,
        they are equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        claim1.setRank('preferred')
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        self.assertEqual(claim1, claim2)
        self.assertEqual(claim2, claim1)

    def test_claim_eq_simple_different_snaktype(self) -> None:
        """Test comparing two claims.

        If they have the same property and different snaktypes, they are
        not equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setSnakType('novalue')
        self.assertNotEqual(claim1, claim2)
        self.assertNotEqual(claim2, claim1)

    def test_claim_eq_simple_different_property(self) -> None:
        """Test comparing two claims.

        If they have the same value and different properties, they are
        not equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        claim2 = pywikibot.Claim(wikidata, 'P21')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        self.assertNotEqual(claim1, claim2)
        self.assertNotEqual(claim2, claim1)

    def test_claim_eq_with_qualifiers(self) -> None:
        """Test comparing two claims.

        If they have the same property, value and qualifiers, they are
        equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        qualifier1 = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier1.setTarget('foo')
        claim1.addQualifier(qualifier1)
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        qualifier2 = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier2.setTarget('foo')
        claim2.addQualifier(qualifier2)
        self.assertEqual(claim1, claim2)
        self.assertEqual(claim2, claim1)

    def test_claim_eq_with_different_qualifiers(self) -> None:
        """Test comparing two claims.

        If they have the same property and value and different
        qualifiers, they are not equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        qualifier1 = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier1.setTarget('foo')
        claim1.addQualifier(qualifier1)
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        qualifier2 = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier2.setTarget('bar')
        claim2.addQualifier(qualifier2)
        self.assertNotEqual(claim1, claim2)
        self.assertNotEqual(claim2, claim1)

    def test_claim_eq_one_without_qualifiers(self) -> None:
        """Test comparing two claims.

        If they have the same property and value and one of them has no
        qualifiers while the other one does, they are not equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        qualifier = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier.setTarget('foo')
        claim1.addQualifier(qualifier)
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        self.assertNotEqual(claim1, claim2)
        self.assertNotEqual(claim2, claim1)

    def test_claim_eq_with_different_sources(self) -> None:
        """Test comparing two claims.

        If they have the same property and value and different sources,
        they are equal.
        """
        wikidata = self.get_repo()
        claim1 = pywikibot.Claim(wikidata, 'P31')
        claim1.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        source1 = pywikibot.Claim(wikidata, 'P143', is_reference=True)
        source1.setTarget(pywikibot.ItemPage(wikidata, 'Q328'))
        claim1.addSource(source1)
        claim2 = pywikibot.Claim(wikidata, 'P31')
        claim2.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        source2 = pywikibot.Claim(wikidata, 'P143', is_reference=True)
        source2.setTarget(pywikibot.ItemPage(wikidata, 'Q48183'))
        claim2.addSource(source2)
        self.assertEqual(claim1, claim2)
        self.assertEqual(claim2, claim1)

    def test_claim_copy_is_equal(self) -> None:
        """Test making a copy of a claim.

        The copy of a claim should be always equal to the claim.
        """
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P31')
        claim.setTarget(pywikibot.ItemPage(wikidata, 'Q5'))
        qualifier = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier.setTarget('foo')
        source = pywikibot.Claim(wikidata, 'P143', is_reference=True)
        source.setTarget(pywikibot.ItemPage(wikidata, 'Q328'))
        claim.addQualifier(qualifier)
        claim.addSource(source)
        copy = claim.copy()
        self.assertEqual(claim, copy)

    def test_claim_copy_is_equal_qualifier(self) -> None:
        """Test making a copy of a claim.

        The copy of a qualifier should be always equal to the qualifier.
        """
        wikidata = self.get_repo()
        qualifier = pywikibot.Claim(wikidata, 'P214', is_qualifier=True)
        qualifier.setTarget('foo')
        copy = qualifier.copy()
        self.assertEqual(qualifier, copy)
        self.assertTrue(qualifier.isQualifier)
        self.assertTrue(copy.isQualifier)

    def test_claim_copy_is_equal_source(self) -> None:
        """Test making a copy of a claim.

        The copy of a source should be always equal to the source.
        """
        wikidata = self.get_repo()
        source = pywikibot.Claim(wikidata, 'P143', is_reference=True)
        source.setTarget(pywikibot.ItemPage(wikidata, 'Q328'))
        copy = source.copy()
        self.assertEqual(source, copy)
        self.assertTrue(source.isReference)
        self.assertTrue(copy.isReference)


class TestClaimSetValue(WikidataTestCase):

    """Test setting claim values."""

    def test_set_website(self) -> None:
        """Test setting claim of url type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P856')
        self.assertEqual(claim.type, 'url')
        target = 'https://en.wikipedia.org/'
        claim.setTarget(target)
        self.assertEqual(claim.target, target)

    def test_set_WbMonolingualText(self) -> None:
        """Test setting claim of monolingualtext type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P1450')
        self.assertEqual(claim.type, 'monolingualtext')
        target = pywikibot.WbMonolingualText(text='Test this!', language='en')
        claim.setTarget(target)
        self.assertEqual(claim.target, target)

    def test_set_WbQuantity(self) -> None:
        """Test setting claim of quantity type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P1106')
        self.assertEqual(claim.type, 'quantity')
        target = pywikibot.WbQuantity(
            amount=1234, error=1, unit='http://www.wikidata.org/entity/Q11573')
        claim.setTarget(target)
        self.assertEqual(claim.target, target)

    def test_set_math(self) -> None:
        """Test setting claim of math type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P2535')
        self.assertEqual(claim.type, 'math')
        target = 'a^2 + b^2 = c^2'
        claim.setTarget(target)
        self.assertEqual(claim.target, target)

    def test_set_identifier(self) -> None:
        """Test setting claim of external-id type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P214')
        self.assertEqual(claim.type, 'external-id')
        target = 'Any string is a valid identifier'
        claim.setTarget(target)
        self.assertEqual(claim.target, target)

    def test_set_date(self) -> None:
        """Test setting claim of time type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P569')
        self.assertEqual(claim.type, 'time')
        claim.setTarget(pywikibot.WbTime(
            year=2001, month=1, day=1, site=wikidata))
        self.assertEqual(claim.target.year, 2001)
        self.assertEqual(claim.target.month, 1)
        self.assertEqual(claim.target.day, 1)

    def test_set_musical_notation(self) -> None:
        """Test setting claim of musical-notation type."""
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P6604')
        self.assertEqual(claim.type, 'musical-notation')
        target = "\\relative c' { c d e f | g2 g | a4 a a a | g1 |}"
        claim.setTarget(target)
        self.assertEqual(claim.target, target)

    def test_set_incorrect_target_value(self) -> None:
        """Test setting claim of the incorrect value."""
        wikidata = self.get_repo()
        date_claim = pywikibot.Claim(wikidata, 'P569')
        regex = r' is not type .+\.$'
        with self.assertRaisesRegex(ValueError, regex):
            date_claim.setTarget('foo')
        url_claim = pywikibot.Claim(wikidata, 'P856')
        with self.assertRaisesRegex(ValueError, regex):
            url_claim.setTarget(pywikibot.WbTime(2001, site=wikidata))
        mono_claim = pywikibot.Claim(wikidata, 'P1450')
        with self.assertRaisesRegex(ValueError, regex):
            mono_claim.setTarget('foo')
        quantity_claim = pywikibot.Claim(wikidata, 'P1106')
        with self.assertRaisesRegex(ValueError, regex):
            quantity_claim.setTarget('foo')


class TestItemBasePageMethods(WikidataTestCase, BasePageMethodsTestBase):

    """Test behavior of ItemPage methods inherited from BasePage."""

    def setup_page(self) -> None:
        """Set up test page."""
        self._page = ItemPage(self.get_repo(), 'Q60')

    def test_basepage_methods(self) -> None:
        """Test ItemPage methods inherited from superclass BasePage."""
        self._test_invoke()
        self._test_no_wikitext()

    def test_item_is_hashable(self) -> None:
        """Ensure that ItemPages are hashable."""
        list_of_dupes = [self._page, self._page]
        self.assertLength(set(list_of_dupes), 1)


class TestPageMethodsWithItemTitle(WikidataTestCase, BasePageMethodsTestBase):

    """Test behavior of Page methods for wikibase item."""

    def setup_page(self) -> None:
        """Set up tests."""
        self._page = pywikibot.Page(self.site, 'Q60')

    def test_basepage_methods(self) -> None:
        """Test Page methods inherited from superclass BasePage with Q60."""
        self._test_invoke()
        self._test_no_wikitext()


class TestLinks(WikidataTestCase):

    """Test cases to test links stored in Wikidata.

    Uses a stored data file for the wikibase item. However wikibase
    creates site objects for each sitelink, and the unit test directly
    creates a Site for 'wikipedia:af' to use in a comparison.
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

    def setUp(self) -> None:
        """Set up tests."""
        super().setUp()
        self.wdp = ItemPage(self.get_repo(), 'Q60')
        self.wdp.id = 'Q60'
        with open(join_pages_path('Q60_only_sitelinks.wd')) as f:
            self.wdp._content = json.load(f)
        self.wdp.get()

    def test_iterlinks_page_object(self) -> None:
        """Test iterlinks for page objects."""
        page = next(pg for pg in self.wdp.iterlinks() if pg.site.code == 'af')
        self.assertEqual(page, pywikibot.Page(self.get_site('afwiki'),
                         'New York Stad'))

    def test_iterlinks_filtering(self) -> None:
        """Test iterlinks for a given family."""
        wikilinks = list(self.wdp.iterlinks('wikipedia'))
        wvlinks = list(self.wdp.iterlinks('wikivoyage'))

        self.assertLength(wikilinks, 3)
        self.assertLength(wvlinks, 2)


class TestWriteNormalizeData(TestCase):

    """Test cases for routines that normalize data for writing to Wikidata.

    Exercises ItemPage._normalizeData with data that is not normalized
    and data which is already normalized.
    """

    net = False

    def setUp(self) -> None:
        """Set up tests."""
        super().setUp()
        self.data_out = {
            'labels': {'en': {'language': 'en', 'value': 'Foo'}},
            'descriptions': {'en': {'language': 'en', 'value': 'Desc'}},
            'aliases': {'en': [
                {'language': 'en', 'value': 'Bah'},
                {'language': 'en', 'value': 'Bar', 'remove': ''},
            ]},
        }

    def test_normalize_data(self) -> None:
        """Test _normalizeData() method."""
        data_in = {
            'labels': {'en': 'Foo'},
            'descriptions': {'en': 'Desc'},
            'aliases': {'en': [
                'Bah',
                {'language': 'en', 'value': 'Bar', 'remove': ''},
            ]},
        }

        response = ItemPage._normalizeData(data_in)
        self.assertEqual(response, self.data_out)

    def test_normalized_data(self) -> None:
        """Test _normalizeData() method for normalized data."""
        response = ItemPage._normalizeData(
            copy.deepcopy(self.data_out))
        self.assertEqual(response, self.data_out)

    def test_normalized_invalid_data(self) -> None:
        """Test _normalizeData() method for invalid data."""
        data = copy.deepcopy(self.data_out)
        data['aliases']['en'] = tuple(data['aliases']['en'])
        with self.assertRaisesRegex(TypeError,
                                    "Unsupported value type 'tuple'"):
            ItemPage._normalizeData(data)


class TestPreloadingEntityGenerator(TestCase):

    """Test preloading item generator."""

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

    def test_non_item_gen(self) -> None:
        """Test PreloadingEntityGenerator with getReferences()."""
        site = self.get_site('wikidata')
        page = pywikibot.Page(site, 'Property:P31')
        ref_gen = page.getReferences(follow_redirects=False, total=5)
        gen = pagegenerators.PreloadingEntityGenerator(ref_gen)
        for item in gen:
            self.assertIsInstance(item, ItemPage)

    def test_foreign_page_item_gen(self) -> None:
        """Test PreloadingEntityGenerator with connected pages."""
        site = self.get_site('enwiki')
        page_gen = [pywikibot.Page(site, 'Main Page'),
                    pywikibot.Page(site, 'New York City')]
        gen = pagegenerators.PreloadingEntityGenerator(page_gen)
        for item in gen:
            self.assertIsInstance(item, ItemPage)


class TestNamespaces(WikidataTestCase):

    """Test cases to test namespaces of Wikibase entities."""

    def test_empty_wikibase_page(self) -> None:
        """Test empty wikibase page.

        As a base class it should be able to instantiate it with minimal
        arguments
        """
        wikidata = self.get_repo()
        page = WikibasePage(wikidata)
        regex = r' object has no attribute '
        with self.assertRaisesRegex(AttributeError, regex):
            page.namespace()
        page = WikibasePage(wikidata, title='')
        with self.assertRaisesRegex(AttributeError, regex):
            page.namespace()

        page = WikibasePage(wikidata, ns=0)
        self.assertEqual(page.namespace(), 0)
        page = WikibasePage(wikidata, entity_type='item')
        self.assertEqual(page.namespace(), 0)

        page = WikibasePage(wikidata, ns=120)
        self.assertEqual(page.namespace(), 120)
        page = WikibasePage(wikidata, title='', ns=120)
        self.assertEqual(page.namespace(), 120)
        page = WikibasePage(wikidata, entity_type='property')
        self.assertEqual(page.namespace(), 120)

        # mismatch in namespaces
        regex = r'^Namespace ".+" is not valid for Wikibase entity type ".+"$'
        with self.assertRaisesRegex(ValueError, regex):
            WikibasePage(wikidata, ns=0, entity_type='property')
        with self.assertRaisesRegex(ValueError, regex):
            WikibasePage(wikidata, ns=120, entity_type='item')

    def test_wikibase_link_namespace(self) -> None:
        """Test the title resolved to a namespace correctly."""
        wikidata = self.get_repo()
        # title without any namespace clues (ns or entity_type)
        # should verify the Link namespace is appropriate
        page = WikibasePage(wikidata, title='Q6')
        self.assertEqual(page.namespace(), 0)
        page = WikibasePage(wikidata, title='Property:P60')
        self.assertEqual(page.namespace(), 120)

    def test_wikibase_namespace_selection(self) -> None:
        """Test various ways to correctly specify the namespace."""
        wikidata = self.get_repo()

        page = ItemPage(wikidata, 'Q60')
        self.assertEqual(page.namespace(), 0)
        page.get()

        page = ItemPage(wikidata, title='Q60')
        self.assertEqual(page.namespace(), 0)
        page.get()

        page = WikibasePage(wikidata, title='Q60', ns=0)
        self.assertEqual(page.namespace(), 0)
        page.get()

        page = WikibasePage(wikidata, title='Q60',
                            entity_type='item')
        self.assertEqual(page.namespace(), 0)
        page.get()

        page = PropertyPage(wikidata, 'Property:P6')
        self.assertEqual(page.namespace(), 120)
        page.get()

        page = PropertyPage(wikidata, 'P6')
        self.assertEqual(page.namespace(), 120)
        page.get()

        page = WikibasePage(wikidata, title='Property:P6')
        self.assertEqual(page.namespace(), 120)
        page.get()

        page = WikibasePage(wikidata, title='P6', ns=120)
        self.assertEqual(page.namespace(), 120)
        page.get()

        page = WikibasePage(wikidata, title='P6',
                            entity_type='property')
        self.assertEqual(page.namespace(), 120)
        page.get()

    def test_wrong_namespaces(self) -> None:
        """Test incorrect namespaces for Wikibase entities."""
        wikidata = self.get_repo()
        # All subclasses of WikibasePage raise a ValueError
        # if the namespace for the page title is not correct
        regex = r': Namespace ".+" is not valid$'
        with self.assertRaisesRegex(ValueError, regex):
            WikibasePage(wikidata, title='Wikidata:Main Page')
        regex = r"^'.+' is not in the namespace "
        with self.assertRaisesRegex(ValueError, regex):
            ItemPage(wikidata, 'File:Q1')
        with self.assertRaisesRegex(ValueError, regex):
            PropertyPage(wikidata, 'File:P60')

    def test_item_unknown_namespace(self) -> None:
        """Test unknown namespaces for Wikibase entities."""
        # The 'Invalid:' is not a known namespace, so is parsed to be
        # part of the title in namespace 0
        # TODO: These items have inappropriate titles, which should
        #       raise an error.
        wikidata = self.get_repo()
        regex = r"^'.+' is not a valid item page title$"
        with self.assertRaisesRegex(InvalidTitleError, regex):
            ItemPage(wikidata, 'Invalid:Q1')


class TestAlternateNamespaces(WikidataTestCase):

    """Test cases to test namespaces of Wikibase entities."""

    cached = False
    dry = True

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test class."""
        super().setUpClass()

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

    def test_alternate_item_namespace(self) -> None:
        """Test alternate item namespace."""
        item = ItemPage(self.repo, 'Q60')
        self.assertEqual(item.namespace(), 90)
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.title(), 'Item:Q60')
        self.assertEqual(item._defined_by(), {'ids': 'Q60'})

        item = ItemPage(self.repo, 'Item:Q60')
        self.assertEqual(item.namespace(), 90)
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.title(), 'Item:Q60')
        self.assertEqual(item._defined_by(), {'ids': 'Q60'})

    def test_alternate_property_namespace(self) -> None:
        """Test alternate property namespace."""
        prop = PropertyPage(self.repo, 'P21')
        self.assertEqual(prop.namespace(), 92)
        self.assertEqual(prop.id, 'P21')
        self.assertEqual(prop.title(), 'Prop:P21')
        self.assertEqual(prop._defined_by(), {'ids': 'P21'})

        prop = PropertyPage(self.repo, 'Prop:P21')
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
            'item': 'Q32119',
        },
        # test.wikidata is also
        'wikidatatest': {
            'family': 'wikidata',
            'code': 'test',
            'item': 'Q33',
        },
    }

    def test_own_client(self, key) -> None:
        """Test that a data repository family can be its own client."""
        site = self.get_site(key)
        page = self.get_mainpage(site)
        item = ItemPage.fromPage(page)
        self.assertEqual(page.site, site)
        self.assertEqual(item.site, site)

    def test_page_from_repository(self, key) -> None:
        """Test that page_from_repository method works for wikibase too."""
        site = self.get_site(key)
        page = site.page_from_repository('Q5296')
        self.assertEqual(page, self.get_mainpage(site))

    def test_redirect_from_repository(self, key) -> None:
        """Test page_from_repository method with redirects."""
        site = self.get_site(key)
        item = self.sites[key]['item']
        with self.assertRaisesRegex(
            IsRedirectPageError,
                fr'{self.sites[key]["item"]}\]\] is a redirect'):
            site.page_from_repository(item)


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

    def test_not_supported_family(self, key) -> None:
        """Test that family without a data repository causes error."""
        site = self.get_site(key)

        self.wdp = pywikibot.Page(site, self.sites[key]['page_title'])
        regex = r' has no data repository$'
        with self.assertRaisesRegex(WikiBaseError, regex):
            ItemPage.fromPage(self.wdp)
        with self.assertRaisesRegex(WikiBaseError, regex):
            self.wdp.data_item()

    def test_has_data_repository(self, key) -> None:
        """Test that site has no data repository."""
        site = self.get_site(key)
        self.assertFalse(site.has_data_repository)

    def test_page_from_repository_fails(self, key) -> None:
        """Test that page_from_repository method fails."""
        site = self.get_site(key)
        dummy_item = 'Q1'
        regex = r'^Wikibase is not implemented for .+\.$'
        with self.assertRaisesRegex(UnknownExtensionError, regex):
            site.page_from_repository(dummy_item)


class TestJSON(WikidataTestCase):

    """Test cases to test toJSON() functions."""

    def setUp(self) -> None:
        """Set up test."""
        super().setUp()
        wikidata = self.get_repo()
        self.wdp = ItemPage(wikidata, 'Q60')
        self.wdp.id = 'Q60'
        with open(join_pages_path('Q60.wd')) as f:
            self.wdp._content = json.load(f)
        self.wdp.get()
        del self.wdp._content['id']
        del self.wdp._content['type']
        del self.wdp._content['lastrevid']
        del self.wdp._content['pageid']

    def test_base_data(self) -> None:
        """Test labels and aliases collections."""
        item = self.wdp
        self.assertIn('en', item.labels)
        self.assertEqual(item.labels['en'], 'New York City')
        self.assertIn('en', item.aliases)
        self.assertIn('NYC', item.aliases['en'])

    def test_str_repr(self) -> None:
        """Test str and repr of labels and aliases."""
        self.assertEqual(
            str(self.wdp.labels),
            "LanguageDict({'af': 'New York Stad', 'als': 'New York City', "
            "'am': 'ኒው ዮርክ ከተማ', 'an': 'Nueva York', ...})"
        )
        self.assertEqual(
            str(self.wdp.aliases),
            "AliasesDict({'be': ['Горад Нью-Ёрк'], 'be-tarask': ['Нью Ёрк'], "
            "'ca': ['Ciutat de Nova York', 'New York City',"
            " 'New York City (New York)', 'NYC', 'N. Y.', 'N Y'], "
            "'da': ['New York City'], ...})"
        )
        self.assertEqual(str(self.wdp.labels), repr(self.wdp.labels))
        self.assertEqual(str(self.wdp.aliases), repr(self.wdp.aliases))

    def test_itempage_json(self) -> None:
        """Test itempage json."""
        old = json.dumps(self.wdp._content, indent=2, sort_keys=True)
        new = json.dumps(self.wdp.toJSON(), indent=2, sort_keys=True)

        self.assertEqual(old, new)

    def test_json_diff(self) -> None:
        """Test json diff."""
        del self.wdp.labels['en']
        self.wdp.aliases['de'].append('New York')
        self.wdp.aliases['de'].append('foo')
        self.wdp.aliases['de'].remove('NYC')
        del self.wdp.aliases['nl']
        del self.wdp.claims['P213']
        del self.wdp.sitelinks['afwiki']
        self.wdp.sitelinks['nlwiki']._badges = set()
        expected = {
            'labels': {
                'en': {
                    'language': 'en',
                    'value': ''
                }
            },
            'aliases': {
                'de': [
                    {'language': 'de', 'value': 'City of New York'},
                    {'language': 'de', 'value': 'The Big Apple'},
                    {'language': 'de', 'value': 'New York'},
                    {'language': 'de', 'value': 'New York'},
                    {'language': 'de', 'value': 'foo'},
                ],
                'nl': [
                    {'language': 'nl', 'value': 'New York', 'remove': ''},
                ],
            },
            'claims': {
                'P213': [
                    {
                        'id': 'Q60$0427a236-4120-7d00-fa3e-e23548d4c02d',
                        'remove': ''
                    }
                ]
            },
            'sitelinks': {
                'afwiki': {
                    'site': 'afwiki',
                    'title': '',
                },
                'nlwiki': {
                    'site': 'nlwiki',
                    'title': 'New York City',
                    'badges': ['']
                }
            }
        }
        diff = self.wdp.toJSON(diffto=self.wdp._content)
        self.assertEqual(diff, expected)


class TestHighLevelApi(WikidataTestCase):

    """Test high-level API for Wikidata."""

    def test_get_best_claim(self) -> None:
        """Test getting the best claim for a property."""
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata, 'Q90')
        item.get()
        self.assertEqual(item.get_best_claim('P17').getTarget(),
                         pywikibot.ItemPage(wikidata, 'Q142'))

    def test_get_value_at_timestamp(self) -> None:
        """Test getting the value of a claim at a specific timestamp."""
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata, 'Q90')
        item.get()
        wbtime = pywikibot.WbTime(year=2021, month=1, day=1, site=wikidata)
        claim = item.get_value_at_timestamp('P17', wbtime)
        self.assertEqual(claim, pywikibot.ItemPage(wikidata, 'Q142'))

    def test_with_monolingual_good_language(self) -> None:
        """Test getting a monolingual text claim with a good language."""
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata, 'Q183')
        item.get()
        wbtime = pywikibot.WbTime(year=2021, month=1, day=1, site=wikidata)
        claim = item.get_value_at_timestamp('P1448', wbtime, 'ru')
        self.assertIsInstance(claim, pywikibot.WbMonolingualText)
        self.assertEqual(claim.language, 'ru')

    def test_with_monolingual_wrong_language(self) -> None:
        """Test getting a monolingual text claim with a wrong language."""
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata, 'Q183')
        item.get()
        wbtime = pywikibot.WbTime(year=2021, month=1, day=1, site=wikidata)
        claim = item.get_value_at_timestamp('P1448', wbtime, 'en')
        self.assertIsNone(claim, None)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
