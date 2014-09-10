# -*- coding: utf-8  -*-
"""Tests for the Wikidata parts of the page module."""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import os
import pywikibot
from pywikibot import pagegenerators
from pywikibot.page import WikibasePage
from pywikibot.site import Namespace
from pywikibot.data.api import APIError
import json
import copy

from tests.aspects import unittest, WikidataTestCase, TestCase


# fetch a page which is very likely to be unconnected, which doesnt have
# a generator, and unit tests may be used to test old versions of pywikibot
def _get_test_unconnected_page(site):
    gen = pagegenerators.NewpagesPageGenerator(site=site, total=10,
                                               namespaces=[1, ])
    for page in gen:
        if not page.properties().get('wikibase_item'):
            return page


class TestGeneral(WikidataTestCase):

    @classmethod
    def setUpClass(cls):
        super(TestGeneral, cls).setUpClass()
        enwiki = pywikibot.Site('en', 'wikipedia')
        cls.mainpage = pywikibot.Page(pywikibot.page.Link("Main Page", enwiki))

    def testWikibase(self):
        repo = self.get_repo()
        item_namespace = repo.namespaces()[0]
        self.assertEqual(item_namespace.defaultcontentmodel, 'wikibase-item')
        item = pywikibot.ItemPage.fromPage(self.mainpage)
        self.assertIsInstance(item, pywikibot.ItemPage)
        self.assertEqual(item.getID(), 'Q5296')
        self.assertEqual(item.title(), 'Q5296')
        self.assertIn('en', item.labels)
        self.assertTrue(item.labels['en'].lower().endswith('main page'))
        self.assertIn('en', item.aliases)
        self.assertIn('HomePage', item.aliases['en'])
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

        # test WbTime
        t = pywikibot.WbTime(site=repo, year=2010, hour=12, minute=43)
        self.assertEqual(t.toTimestr(), '+00000002010-01-01T12:43:00Z')
        self.assertRaises(ValueError, pywikibot.WbTime, site=repo, precision=15)
        self.assertRaises(ValueError, pywikibot.WbTime, site=repo, precision='invalid_precision')

        # test WbQuantity
        q = pywikibot.WbQuantity(amount=1234, error=1)
        self.assertEqual(q.toWikibase(),
                         {'amount': 1234, 'lowerBound': 1233,
                          'upperBound': 1235, 'unit': '1', })
        q = pywikibot.WbQuantity(amount=5, error=(2, 3))
        self.assertEqual(q.toWikibase(),
                         {'amount': 5, 'lowerBound': 2, 'upperBound': 7,
                          'unit': '1', })
        q = pywikibot.WbQuantity(amount=0.044405586)
        self.assertEqual(q.toWikibase(),
                         {'amount': 0.044405586, 'lowerBound': 0.044405586,
                          'upperBound': 0.044405586, 'unit': '1', })
        # test other WbQuantity methods
        self.assertEqual("%s" % q,
                         "{'amount': %(val)r, 'lowerBound': %(val)r, "
                         "'unit': '1', 'upperBound': %(val)r}" % {'val': 0.044405586})
        self.assertEqual("%r" % q,
                         "WbQuantity(amount=%(val)s, "
                         "upperBound=%(val)s, lowerBound=%(val)s, "
                         "unit=1)" % {'val': 0.044405586})
        self.assertEqual(q, q)

        # test WbQuantity.fromWikibase() instantiating
        q = pywikibot.WbQuantity.fromWikibase({u'amount': u'+0.0229',
                                               u'lowerBound': u'0',
                                               u'upperBound': u'1',
                                               u'unit': u'1'})
        self.assertEqual(q.toWikibase(),
                         {'amount': 0.0229, 'lowerBound': 0, 'upperBound': 1,
                          'unit': '1', })

        # test WbQuantity error handling
        self.assertRaises(ValueError, pywikibot.WbQuantity, amount=None,
                          error=1)
        self.assertRaises(NotImplementedError, pywikibot.WbQuantity, amount=789,
                          unit='invalid_unit')

        # test WikibasePage.__cmp__
        self.assertEqual(pywikibot.ItemPage.fromPage(self.mainpage),
                         pywikibot.ItemPage(repo, 'q5296'))

    def testItemPageExtensionability(self):
        class MyItemPage(pywikibot.ItemPage):
            pass
        self.assertIsInstance(MyItemPage.fromPage(self.mainpage), MyItemPage)


class TestItemLoad(WikidataTestCase):

    """Test each of the three code paths for item creation:
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
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(hasattr(item, '_title'), False)
        self.assertEqual(hasattr(item, '_site'), False)
        self.assertEqual(item.title(), 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        self.assertEqual(hasattr(item, '_content'), False)
        item.get()
        self.assertEqual(hasattr(item, '_content'), True)

    def test_load_item_set_id(self):
        """Test setting item.id attribute on empty item."""
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata, '-1')
        self.assertEqual(item._link._title, '-1')
        item.id = 'Q60'
        self.assertEqual(hasattr(item, '_content'), False)
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(hasattr(item, '_content'), False)
        item.get()
        self.assertEqual(hasattr(item, '_content'), True)
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
        self.assertRaises(TypeError, pywikibot.ItemPage, wikidata)

    def test_item_invalid_titles(self):

        wikidata = self.get_repo()

        def check(title, exception):
            item = pywikibot.ItemPage(wikidata, title)
            if title != '':
                ucfirst_title = title[0].upper() + title[1:]
            else:
                ucfirst_title = title
            self.assertEqual(item._link._title, ucfirst_title)
            self.assertEqual(item.id, title.upper())
            self.assertEqual(item.title(), title.upper())
            self.assertEqual(hasattr(item, '_content'), False)
            self.assertRaises(exception, item.get)
            self.assertEqual(hasattr(item, '_content'), False)
            self.assertEqual(item.title(), title.upper())

        check('', KeyError)

        for title in ['-1', '1', 'Q0.5', 'NULL', 'null', 'Q', 'Q-1']:
            check(title, APIError)

    def test_item_untrimmed_title(self):
        wikidata = self.get_repo()
        item = pywikibot.ItemPage(wikidata, ' Q60 ')
        self.assertEqual(item._link._title, 'Q60')
        self.assertEqual(item.title(), 'Q60')
        item.get()

    def test_item_missing(self):
        wikidata = self.get_repo()
        # this item is deleted
        item = pywikibot.ItemPage(wikidata, 'Q404')
        self.assertEqual(item._link._title, 'Q404')
        self.assertEqual(item.title(), 'Q404')
        self.assertEqual(hasattr(item, '_content'), False)
        self.assertEqual(item.id, 'Q404')
        self.assertEqual(item.getID(), 'Q404')
        self.assertEqual(item.getID(numeric=True), 404)
        self.assertEqual(hasattr(item, '_content'), False)
        self.assertRaises(pywikibot.NoPage, item.get)
        self.assertEqual(hasattr(item, '_content'), True)
        self.assertEqual(item._link._title, 'Q404')
        self.assertEqual(item.title(), 'Q404')
        self.assertEqual(item.exists(), False)

    def test_fromPage_noprops(self):
        page = self.nyc
        item = pywikibot.ItemPage.fromPage(page)
        self.assertEqual(item._link._title, 'Null')  # not good
        self.assertEqual(hasattr(item, 'id'), False)
        self.assertEqual(hasattr(item, '_content'), False)
        self.assertEqual(item.title(), 'Q60')
        self.assertEqual(hasattr(item, '_content'), True)
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        item.get()
        self.assertEqual(item.exists(), True)

    def test_fromPage_props(self):
        page = self.nyc
        # fetch page properties
        page.properties()
        item = pywikibot.ItemPage.fromPage(page)
        self.assertEqual(item._link._title, 'Q60')
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(hasattr(item, '_content'), False)
        self.assertEqual(item.title(), 'Q60')
        self.assertEqual(hasattr(item, '_content'), False)
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.getID(), 'Q60')
        self.assertEqual(item.getID(numeric=True), 60)
        self.assertEqual(hasattr(item, '_content'), False)
        item.get()
        self.assertEqual(hasattr(item, '_content'), True)
        self.assertEqual(item.exists(), True)

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

                item = pywikibot.ItemPage.fromPage(page)
                self.assertEqual(hasattr(item, 'id'), False)
                self.assertEqual(hasattr(item, '_title'), True)
                self.assertEqual(hasattr(item, '_site'), True)
                self.assertEqual(hasattr(item, '_content'), False)

                self.assertEqual(item._link._title, 'Null')
                # the method 'exists' does not raise an exception
                if method == 'exists':
                    self.assertEqual(item.exists(), False)
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

                self.assertEqual(hasattr(item, '_content'), True)

                self.assertEqual(item.exists(), False)

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
        item = pywikibot.ItemPage.fromPage(page)

        # Now verify that delay loading will result in the desired semantics.
        # It should not raise NoPage on the wikibase item which has a title
        # like '-1' or 'Null', as that is useless to determine the cause
        # without a full debug log.
        # It should raise NoPage on the page, as that is what the
        # bot operator needs to see in the log output.
        self.assertRaisesRegexp(pywikibot.NoPage, 'Test page', item.get)


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
        target = pywikibot.ItemPage(wikidata, 'Q8422626')
        self.assertTrue(item.isRedirectPage())
        self.assertEqual(item.getRedirectTarget(), target)


class TestPropertyPage(WikidataTestCase):

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

    def test_set_website(self):
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P856')
        self.assertEqual(claim.type, 'url')
        claim.setTarget('https://en.wikipedia.org/')
        self.assertEqual(claim.target, 'https://en.wikipedia.org/')

    def test_set_date(self):
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P569')
        self.assertEqual(claim.type, 'time')
        claim.setTarget(pywikibot.WbTime(year=2001, month=1, day=1, site=wikidata))
        self.assertEqual(claim.target.year, 2001)
        self.assertEqual(claim.target.month, 1)
        self.assertEqual(claim.target.day, 1)

    def test_set_incorrect_target_value(self):
        wikidata = self.get_repo()
        claim = pywikibot.Claim(wikidata, 'P569')
        self.assertRaises(ValueError, claim.setTarget, 'foo')
        claim = pywikibot.Claim(wikidata, 'P856')
        self.assertRaises(ValueError, claim.setTarget, pywikibot.WbTime(2001, site=wikidata))


class TestPageMethods(WikidataTestCase):

    """Test cases to test methods of Page() behave correctly with Wikibase"""

    family = 'wikidata'
    code = 'test'

    def test_page_methods(self):
        """Test ItemPage methods inherited from superclass Page."""
        wikidatatest = self.get_repo()
        self.wdp = pywikibot.ItemPage(wikidatatest, 'Q6')
        self.assertRaises(pywikibot.PageNotSaved, self.wdp.save)
        self.wdp.previousRevision()
        self.assertEqual(self.wdp.langlinks(), [])
        self.assertEqual(self.wdp.templates(), [])
        self.assertFalse(self.wdp.isCategoryRedirect())
        self.wdp.templatesWithParams()


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
        self.wdp._content = json.load(open(os.path.join(os.path.split(__file__)[0], 'pages', 'Q60_only_sitelinks.wd')))
        self.wdp.get()

    def test_iterlinks_page_object(self):
        page = [pg for pg in self.wdp.iterlinks() if pg.site.language() == 'af'][0]
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
    lang = 'en'

    def setUp(self):
        super(TestWriteNormalizeLang, self).setUp()
        self.site = pywikibot.Site('en', 'wikipedia')
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
        self.data_out = {'aliases':
                         {'en':
                            [
                                {'language': 'en',
                                 'value': 'Bah'}
                            ],
                          },
                         'labels':
                          {'en':
                             {'language': 'en',
                              'value': 'Foo'},
                           }
                         }

    def test_normalize_data(self):
        data_in = {'aliases':
                   {'en': ['Bah']},
                   'labels':
                   {'en': 'Foo'},
                   }

        response = WikibasePage._normalizeData(data_in)
        self.assertEqual(response, self.data_out)

    def test_normalized_data(self):
        response = WikibasePage._normalizeData(
            copy.deepcopy(self.data_out))
        self.assertEqual(response, self.data_out)


class TestNamespaces(WikidataTestCase):

    """Test cases to test namespaces of Wikibase entities"""

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
        page = pywikibot.page.ItemPage(wikidata, 'Q6')
        self.assertEqual(page.namespace(), 0)
        page = pywikibot.page.ItemPage(wikidata, title='Q6')
        self.assertEqual(page.namespace(), 0)

        page = pywikibot.page.WikibasePage(wikidata, title='Q6', ns=0)
        self.assertEqual(page.namespace(), 0)
        page = pywikibot.page.WikibasePage(wikidata, title='Q6',
                                           entity_type='item')
        self.assertEqual(page.namespace(), 0)

        page = pywikibot.page.PropertyPage(wikidata, 'Property:P60')
        self.assertEqual(page.namespace(), 120)
        page = pywikibot.page.PropertyPage(wikidata, 'P60')
        self.assertEqual(page.namespace(), 120)

        page = pywikibot.page.WikibasePage(wikidata, title='P60', ns=120)
        self.assertEqual(page.namespace(), 120)
        page = pywikibot.page.WikibasePage(wikidata, title='P60',
                                           entity_type='property')
        self.assertEqual(page.namespace(), 120)

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
        item = pywikibot.ItemPage(wikidata, 'Invalid:Q1')
        self.assertEqual(item.namespace(), 0)
        self.assertEqual(item.id, 'INVALID:Q1')
        self.assertEqual(item.title(), 'INVALID:Q1')
        self.assertEqual(hasattr(item, '_content'), False)
        self.assertRaises(APIError, item.get)
        self.assertEqual(hasattr(item, '_content'), False)
        self.assertEqual(item.title(), 'INVALID:Q1')


class TestAlternateNamespaces(TestCase):

    """Test cases to test namespaces of Wikibase entities"""

    net = False

    def setUp(self):
        super(TestAlternateNamespaces, self).setUp()

        class DrySite(pywikibot.site.DataSite):
            _namespaces = {
                90: Namespace(id=90,
                              canonical_name='Item',
                              defaultcontentmodel='wikibase-item'),
                92: Namespace(id=92,
                              canonical_name='Prop',
                              defaultcontentmodel='wikibase-property')
            }

            __init__ = lambda *args: None
            code = 'test'
            family = lambda: None
            family.name = 'test'
            _logged_in_as = None
            _siteinfo = {'case': 'first-letter'}
            _item_namespace = None
            _property_namespace = None

            def encoding(self):
                return 'utf-8'

            def encodings(self):
                return []

        self.site = DrySite('test', 'mock', None, None)

    def test_alternate_item_namespace(self):
        item = pywikibot.ItemPage(self.site, 'Q60')
        self.assertEqual(item.namespace(), 90)
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.title(), 'Item:Q60')
        self.assertEqual(item._defined_by(), {'ids': 'Q60'})

        item = pywikibot.ItemPage(self.site, 'Item:Q60')
        self.assertEqual(item.namespace(), 90)
        self.assertEqual(item.id, 'Q60')
        self.assertEqual(item.title(), 'Item:Q60')
        self.assertEqual(item._defined_by(), {'ids': 'Q60'})

    def test_alternate_property_namespace(self):
        prop = pywikibot.PropertyPage(self.site, 'P21')
        self.assertEqual(prop.namespace(), 92)
        self.assertEqual(prop.id, 'P21')
        self.assertEqual(prop.title(), 'Prop:P21')
        self.assertEqual(prop._defined_by(), {'ids': 'P21'})

        prop = pywikibot.PropertyPage(self.site, 'Prop:P21')
        self.assertEqual(prop.namespace(), 92)
        self.assertEqual(prop.id, 'P21')
        self.assertEqual(prop.title(), 'Prop:P21')
        self.assertEqual(prop._defined_by(), {'ids': 'P21'})


class TestOwnClient(TestCase):

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

    def test_not_supported_family(self, key):
        """Test that family without a data repository causes error."""
        site = self.get_site(key)

        self.wdp = pywikibot.Page(site, self.sites[key]['page_title'])
        self.assertRaises(pywikibot.WikiBaseError,
                          pywikibot.ItemPage.fromPage, self.wdp)
        self.assertRaisesRegexp(pywikibot.WikiBaseError,
                                'no transcluded data',
                                self.wdp.data_item)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
