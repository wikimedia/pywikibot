#!/usr/bin/env python3
"""Tests for the site module."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

import pywikibot
from tests.aspects import DefaultWikidataClientTestCase, WikidataTestCase


class TestDataSitePreloading(WikidataTestCase):

    """Test DataSite.preload_entities for repo pages."""

    def test_item(self):
        """Test that ItemPage preloading works for Item objects."""
        datasite = self.get_repo()
        items = [pywikibot.ItemPage(datasite, 'q' + str(num))
                 for num in range(1, 6)]

        seen = []
        for item in datasite.preload_entities(items):
            self.assertIsInstance(item, pywikibot.ItemPage)
            self.assertTrue(hasattr(item, '_content'))
            self.assertNotIn(item, seen)
            seen.append(item)
        self.assertLength(seen, 5)

    def test_item_as_page(self):
        """Test that ItemPage preloading works for Page objects."""
        site = self.get_site()
        datasite = self.get_repo()
        pages = [pywikibot.Page(site, 'q' + str(num))
                 for num in range(1, 6)]

        seen = []
        for item in datasite.preload_entities(pages):
            self.assertIsInstance(item, pywikibot.ItemPage)
            self.assertTrue(hasattr(item, '_content'))
            self.assertNotIn(item, seen)
            seen.append(item)
        self.assertLength(seen, 5)

    def test_property(self):
        """Test that preloading works for properties."""
        datasite = self.get_repo()
        page = pywikibot.Page(datasite, 'P6')
        property_page = next(datasite.preload_entities([page]))
        self.assertIsInstance(property_page, pywikibot.PropertyPage)
        self.assertTrue(hasattr(property_page, '_content'))


class TestDataSiteClientPreloading(DefaultWikidataClientTestCase):

    """Test DataSite.preload_entities for client pages."""

    def test_non_item(self):
        """Test that ItemPage preloading works with Page generator."""
        mainpage = self.get_mainpage()
        datasite = self.get_repo()

        item = next(datasite.preload_entities([mainpage]))
        self.assertIsInstance(item, pywikibot.ItemPage)
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q5296')


class TestDataSiteSearchEntities(WikidataTestCase):

    """Test DataSite.search_entities."""

    def test_general(self):
        """Test basic search_entities functionality."""
        datasite = self.get_repo()
        pages = list(datasite.search_entities('abc', 'en', total=50))
        self.assertIsNotEmpty(pages)
        self.assertLessEqual(len(pages), 50)
        pages = list(datasite.search_entities('alphabet', 'en',
                                              type='property', total=50))
        self.assertIsNotEmpty(pages)
        self.assertLessEqual(len(pages), 50)

    def test_continue(self):
        """Test that continue parameter in search_entities works."""
        datasite = self.get_repo()
        kwargs = {'total': 50}
        pages = datasite.search_entities('Rembrandt', 'en', **kwargs)
        kwargs['continue'] = 1
        pages_continue = datasite.search_entities('Rembrandt', 'en', **kwargs)
        self.assertNotEqual(list(pages), list(pages_continue))

    def test_invalid_language(self):
        """Test behavior of search_entities with invalid language provided."""
        datasite = self.get_repo()
        with self.assertRaises(ValueError):
            datasite.search_entities('abc', 'invalidlanguage')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
