# -*- coding: utf-8  -*-
"""
Tests for the Wikidata parts of the page module.
"""
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
from pywikibot.data.api import APIError
import json

from tests.utils import PywikibotTestCase, unittest

site = pywikibot.Site('en', 'wikipedia')
mainpage = pywikibot.Page(pywikibot.page.Link("Main Page", site))
wikidata = site.data_repository()
wikidatatest = pywikibot.Site('test', 'wikidata').data_repository()


# fetch a page which is very likely to be unconnected, which doesnt have
# a generator, and unit tests may be used to test old versions of pywikibot
def _get_test_unconnected_page(site):
    gen = pagegenerators.NewpagesPageGenerator(site=site, total=10,
                                               namespaces=[1, ])
    for page in gen:
        if not page.properties().get('wikibase_item'):
            return page


class TestGeneral(PywikibotTestCase):

    def testWikibase(self):
        if not site.has_transcluded_data:
            return
        repo = site.data_repository()
        item_namespace = repo.namespaces()[0]
        self.assertEqual(item_namespace.defaultcontentmodel, 'wikibase-item')
        item = pywikibot.ItemPage.fromPage(mainpage)
        self.assertType(item, pywikibot.ItemPage)
        self.assertEqual(item.getID(), 'Q5296')
        self.assertEqual(item.title(), 'Q5296')
        self.assertTrue('en' in item.labels)
        self.assertTrue(item.labels['en'].lower().endswith('main page'))
        self.assertTrue('en' in item.aliases)
        self.assertTrue('HomePage' in item.aliases['en'])
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
        t = pywikibot.WbTime(site=wikidata, year=2010, hour=12, minute=43)
        self.assertEqual(t.toTimestr(), '+00000002010-01-01T12:43:00Z')
        self.assertRaises(ValueError, pywikibot.WbTime, site=wikidata, precision=15)
        self.assertRaises(ValueError, pywikibot.WbTime, site=wikidata, precision='invalid_precision')

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
        self.assertEqual(pywikibot.ItemPage.fromPage(mainpage),
                         pywikibot.ItemPage(repo, 'q5296'))

    def testItemPageExtensionability(self):
        class MyItemPage(pywikibot.ItemPage):
            pass
        self.assertIsInstance(MyItemPage.fromPage(mainpage), MyItemPage)

    def test_not_supported_family(self):
        """Test that family without a data repository causes error."""
        # Wikispecies is not supported by Wikidata yet.
        species_site = pywikibot.Site('species', 'species')
        self.wdp = pywikibot.Page(species_site, 'Main Page')
        self.assertRaises(pywikibot.WikiBaseError,
                          pywikibot.ItemPage.fromPage, self.wdp)
        self.assertRaisesRegexp(pywikibot.WikiBaseError,
                                'species.*no transcluded data',
                                self.wdp.data_item)

        # test.wikidata does not have a data repository.
        self.wdp = pywikibot.ItemPage(wikidatatest, 'Q6')
        self.assertRaises(pywikibot.WikiBaseError,
                          pywikibot.ItemPage.fromPage, self.wdp)

        # The main Wikidata also does not have a data repository.
        # It is a data repository, but no pages on Wikidata have
        # a linked page.
        self.wdp = pywikibot.ItemPage(wikidata, 'Q60')
        self.assertRaises(pywikibot.WikiBaseError,
                          pywikibot.ItemPage.fromPage, self.wdp)

        self.wdp = pywikibot.Page(wikidata, 'Main Page', ns=4)
        self.assertRaises(pywikibot.WikiBaseError,
                          pywikibot.ItemPage.fromPage, self.wdp)


class TestItemLoad(PywikibotTestCase):
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
    def test_item_normal(self):
        item = pywikibot.ItemPage(wikidata, 'Q60')
        self.assertEquals(item._link._title, 'Q60')
        self.assertEquals(item.id, 'Q60')
        self.assertEquals(hasattr(item, '_title'), False)
        self.assertEquals(hasattr(item, '_site'), False)
        self.assertEquals(item.title(), 'Q60')
        self.assertEquals(item.getID(), 'Q60')
        self.assertEquals(item.getID(numeric=True), 60)
        self.assertEquals(hasattr(item, '_content'), False)
        item.get()
        self.assertEquals(hasattr(item, '_content'), True)

    def test_load_item_set_id(self):
        """Test setting item.id attribute on empty item."""
        item = pywikibot.ItemPage(wikidata, '-1')
        self.assertEquals(item._link._title, '-1')
        item.id = 'Q60'
        self.assertEquals(hasattr(item, '_content'), False)
        self.assertEquals(item.getID(), 'Q60')
        self.assertEquals(hasattr(item, '_content'), False)
        item.get()
        self.assertEquals(hasattr(item, '_content'), True)
        self.assertTrue('en' in item.labels)
        self.assertEquals(item.labels['en'], 'New York City')
        self.assertEquals(item.title(), 'Q60')

    def test_reuse_item_set_id(self):
        """
        Test modifying item.id attribute.

        Some scripts are using item.id = 'Q60' semantics, which does work
        but modifying item.id does not currently work, and this test
        highlights that it breaks silently.
        """
        item = pywikibot.ItemPage(wikidata, 'Q60')
        item.get()
        self.assertEquals(item.labels['en'], 'New York City')

        # When the id attribute is modified, the ItemPage goes into
        # an inconsistent state.
        item.id = 'Q5296'
        # The title is updated correctly
        self.assertEquals(item.title(), 'Q5296')

        # This del has no effect on the test; it is here to demonstrate that
        # it doesnt help to clear this piece of saved state.
        del item._content
        # The labels are not updated; assertion showing undesirable behaviour:
        self.assertEquals(item.labels['en'], 'New York City')
        # TODO: This is the assertion that this test should be using:
        # self.assertTrue(item.labels['en'].lower().endswith('main page'))

    def test_empty_item(self):
        # should not raise an error as the constructor only requires
        # the site parameter, with the title parameter defaulted to None
        self.assertRaises(TypeError, pywikibot.ItemPage, wikidata)

    def test_item_invalid_titles(self):

        def check(title, exception):
            item = pywikibot.ItemPage(wikidata, title)
            if title != '':
                ucfirst_title = title[0].upper() + title[1:]
            else:
                ucfirst_title = title
            self.assertEquals(item._link._title, ucfirst_title)
            self.assertEquals(item.id, title.upper())
            self.assertEquals(item.title(), title.upper())
            self.assertEquals(hasattr(item, '_content'), False)
            self.assertRaises(exception, item.get)
            self.assertEquals(hasattr(item, '_content'), False)
            self.assertEquals(item.title(), title.upper())

        check('', KeyError)

        for title in ['-1', '1', 'Q0.5', 'NULL', 'null', 'Q', 'Q-1']:
            check(title, APIError)

    def test_item_untrimmed_title(self):
        # spaces in the title cause an error
        item = pywikibot.ItemPage(wikidata, ' Q60 ')
        self.assertEquals(item._link._title, 'Q60')
        self.assertEquals(item.title(), ' Q60 ')
        self.assertRaises(APIError, item.get)

    def test_item_missing(self):
        # this item is deleted
        item = pywikibot.ItemPage(wikidata, 'Q404')
        self.assertEquals(item._link._title, 'Q404')
        self.assertEquals(item.title(), 'Q404')
        self.assertEquals(hasattr(item, '_content'), False)
        self.assertEquals(item.id, 'Q404')
        self.assertEquals(item.getID(), 'Q404')
        self.assertEquals(item.getID(numeric=True), 404)
        self.assertEquals(hasattr(item, '_content'), False)
        self.assertRaises(pywikibot.NoPage, item.get)
        self.assertEquals(hasattr(item, '_content'), True)
        self.assertEquals(item._link._title, 'Q404')
        self.assertEquals(item.title(), 'Q404')
        self.assertEquals(item.exists(), False)

    def test_fromPage_noprops(self):
        page = pywikibot.Page(pywikibot.page.Link("New York City", site))
        item = pywikibot.ItemPage.fromPage(page)
        self.assertEquals(item._link._title, 'Null')  # not good
        self.assertEquals(hasattr(item, 'id'), False)
        self.assertEquals(hasattr(item, '_content'), False)
        self.assertEquals(item.title(), 'Q60')
        self.assertEquals(hasattr(item, '_content'), True)
        self.assertEquals(item.id, 'Q60')
        self.assertEquals(item.getID(), 'Q60')
        self.assertEquals(item.getID(numeric=True), 60)
        item.get()
        self.assertEquals(item.exists(), True)

    def test_fromPage_props(self):
        page = pywikibot.Page(pywikibot.page.Link("New York City", site))
        # fetch page properties
        page.properties()
        item = pywikibot.ItemPage.fromPage(page)
        self.assertEquals(item._link._title, 'Q60')
        self.assertEquals(item.id, 'Q60')
        self.assertEquals(hasattr(item, '_content'), False)
        self.assertEquals(item.title(), 'Q60')
        self.assertEquals(hasattr(item, '_content'), False)
        self.assertEquals(item.id, 'Q60')
        self.assertEquals(item.getID(), 'Q60')
        self.assertEquals(item.getID(numeric=True), 60)
        self.assertEquals(hasattr(item, '_content'), False)
        item.get()
        self.assertEquals(hasattr(item, '_content'), True)
        self.assertEquals(item.exists(), True)

    def test_fromPage_invalid_title(self):
        page = pywikibot.Page(pywikibot.page.Link("[]", site))
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
                self.assertEquals(hasattr(item, 'id'), False)
                self.assertEquals(hasattr(item, '_title'), True)
                self.assertEquals(hasattr(item, '_site'), True)
                self.assertEquals(hasattr(item, '_content'), False)

                self.assertEquals(item._link._title, 'Null')
                # the method 'exists' does not raise an exception
                if method == 'exists':
                    self.assertEquals(item.exists(), False)
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
                    self.assertEquals(item._link._title, '-1')

                self.assertEquals(hasattr(item, '_content'), True)

                self.assertEquals(item.exists(), False)

    def test_fromPage_redirect(self):
        # this is a redirect, and should not have a wikidata item
        link = pywikibot.page.Link("Main page", site)
        self._test_fromPage_noitem(link)

    def test_fromPage_missing(self):
        # this is a deleted page, and should not have a wikidata item
        link = pywikibot.page.Link("Test page", site)
        self._test_fromPage_noitem(link)

    def test_fromPage_noitem(self):
        # this is a new page, and should not have a wikidata item yet
        page = _get_test_unconnected_page(site)
        link = page._link
        self._test_fromPage_noitem(link)

    def test_fromPage_missing_lazy(self):
        """Test lazy loading of item from nonexistent source page."""
        # this is a deleted page, and should not have a wikidata item
        link = pywikibot.page.Link("Test page", site)
        page = pywikibot.Page(link)
        item = pywikibot.ItemPage.fromPage(page)

        # Now verify that delay loading will result in the desired semantics.
        # It should not raise NoPage on the wikibase item which has a title
        # like '-1' or 'Null', as that is useless to determine the cause
        # without a full debug log.
        # It should raise NoPage on the page, as that is what the
        # bot operator needs to see in the log output.
        self.assertRaisesRegexp(pywikibot.NoPage, 'Test page', item.get)


class TestPropertyPage(PywikibotTestCase):

    def test_property_empty_property(self):
        self.assertRaises(pywikibot.Error, pywikibot.PropertyPage, wikidata)

    def test_globe_coordinate(self):
        property_page = pywikibot.PropertyPage(wikidata, 'P625')
        self.assertEquals(property_page.type, 'globe-coordinate')
        self.assertEquals(property_page.getType(), 'globecoordinate')

        claim = pywikibot.Claim(wikidata, 'P625')
        self.assertEquals(claim.type, 'globe-coordinate')
        self.assertEquals(claim.getType(), 'globecoordinate')


class TestClaimSetValue(PywikibotTestCase):

    def test_set_website(self):
        claim = pywikibot.Claim(wikidata, 'P856')
        self.assertEquals(claim.type, 'url')
        claim.setTarget('https://en.wikipedia.org/')
        self.assertEquals(claim.target, 'https://en.wikipedia.org/')

    def test_set_date(self):
        claim = pywikibot.Claim(wikidata, 'P569')
        self.assertEquals(claim.type, 'time')
        claim.setTarget(pywikibot.WbTime(year=2001, month=01, day=01, site=wikidata))
        self.assertEquals(claim.target.year, 2001)
        self.assertEquals(claim.target.month, 1)
        self.assertEquals(claim.target.day, 1)

    def test_set_incorrect_target_value(self):
        claim = pywikibot.Claim(wikidata, 'P569')
        self.assertRaises(ValueError, claim.setTarget, 'foo')
        claim = pywikibot.Claim(wikidata, 'P856')
        self.assertRaises(ValueError, claim.setTarget, pywikibot.WbTime(2001, site=wikidata))


class TestPageMethods(PywikibotTestCase):
    """Test cases to test methods of Page() behave correctly with Wikibase"""

    def test_page_methods(self):
        """Test ItemPage methods inherited from superclass Page."""
        self.wdp = pywikibot.ItemPage(wikidatatest, 'Q6')
        self.assertRaises(pywikibot.WikiBaseError, self.wdp.data_item)
        self.assertRaises(pywikibot.PageNotSaved, self.wdp.save)
        self.wdp.previousRevision()
        self.assertEquals(self.wdp.langlinks(), [])
        self.assertEquals(self.wdp.templates(), [])
        self.assertFalse(self.wdp.isCategoryRedirect())
        self.wdp.templatesWithParams()


class TestLinks(PywikibotTestCase):
    """Test cases to test links stored in Wikidata"""
    def setUp(self):
        super(TestLinks, self).setUp()
        self.wdp = pywikibot.ItemPage(wikidata, 'Q60')
        self.wdp.id = 'Q60'
        self.wdp._content = json.load(open(os.path.join(os.path.split(__file__)[0], 'pages', 'Q60_only_sitelinks.wd')))
        self.wdp.get()

    def test_iterlinks_page_object(self):
        page = [pg for pg in self.wdp.iterlinks() if pg.site.language() == 'af'][0]
        self.assertEquals(page, pywikibot.Page(pywikibot.Site('af', 'wikipedia'), u'New York Stad'))

    def test_iterlinks_filtering(self):
        wikilinks = list(self.wdp.iterlinks('wikipedia'))
        wvlinks = list(self.wdp.iterlinks('wikivoyage'))

        self.assertEquals(len(wikilinks), 3)
        self.assertEquals(len(wvlinks), 2)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
