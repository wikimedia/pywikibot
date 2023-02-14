#!/usr/bin/env python3
"""Tests for the Wikidata parts of the page module."""
#
# (C) Pywikibot team, 2019-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot.page._collections import (
    AliasesDict,
    ClaimCollection,
    LanguageDict,
    SiteLinkCollection,
)
from tests.aspects import WikidataTestCase


class DataCollectionTestCase(WikidataTestCase):

    """Test case for a Wikibase collection class."""

    collection_class = None

    def _test_new_empty(self):
        """Test that new_empty method returns empty collection."""
        cls = self.collection_class
        result = cls.new_empty(self.get_repo())
        self.assertIsEmpty(result)


class TestLanguageDict(DataCollectionTestCase):

    """Test cases covering LanguageDict methods."""

    collection_class = LanguageDict

    family = 'wikipedia'
    code = 'en'

    dry = True

    def setUp(self):
        """Setup tests."""
        super().setUp()
        self.site = self.get_site()
        self.lang_out = {'en': 'foo', 'zh': 'bar'}

    def test_init(self):
        """Test LanguageDict initializer."""
        ld = LanguageDict()
        self.assertLength(ld, 0)
        ld = LanguageDict(self.lang_out)
        self.assertLength(ld, 2)

    def test_setitem(self):
        """Test LanguageDict.__setitem__ metamethod."""
        ld = LanguageDict(self.lang_out)
        self.assertIn('en', ld)
        ld[self.site] = 'bar'
        self.assertIn('en', ld)

    def test_getitem(self):
        """Test LanguageDict.__getitem__ metamethod."""
        ld = LanguageDict(self.lang_out)
        self.assertEqual(ld['en'], 'foo')
        self.assertEqual(ld[self.site], 'foo')
        self.assertIsNone(ld.get('de'))

    def test_delitem(self):
        """Test LanguageDict.__delitem__ metamethod."""
        ld = LanguageDict(self.lang_out)
        ld.pop(self.site)
        ld.pop('zh')
        self.assertNotIn('en', ld)
        self.assertNotIn('zh', ld)
        self.assertLength(ld, 0)

    def test_fromJSON(self):
        """Test LanguageDict.fromJSON method."""
        ld = LanguageDict.fromJSON(
            {'en': {'language': 'en', 'value': 'foo'},
             'zh': {'language': 'zh', 'value': 'bar'}})
        self.assertIsInstance(ld, LanguageDict)
        self.assertEqual(ld, LanguageDict(self.lang_out))

    def test_toJSON(self):
        """Test LanguageDict.toJSON method."""
        ld = LanguageDict()
        self.assertEqual(ld.toJSON(), {})
        ld = LanguageDict(self.lang_out)
        self.assertEqual(
            ld.toJSON(), {'en': {'language': 'en', 'value': 'foo'},
                          'zh': {'language': 'zh', 'value': 'bar'}})

    def test_toJSON_diffto(self):
        """Test LanguageDict.toJSON method."""
        ld = LanguageDict({'de': 'foo', 'zh': 'bar'})
        diffto = {
            'de': {'language': 'de', 'value': 'bar'},
            'en': {'language': 'en', 'value': 'foo'}}
        self.assertEqual(
            ld.toJSON(diffto=diffto),
            {'de': {'language': 'de', 'value': 'foo'},
             'en': {'language': 'en', 'value': ''},
             'zh': {'language': 'zh', 'value': 'bar'}})

    def test_normalizeData(self):
        """Test LanguageDict.normalizeData method."""
        self.assertEqual(
            LanguageDict.normalizeData(self.lang_out),
            {'en': {'language': 'en', 'value': 'foo'},
             'zh': {'language': 'zh', 'value': 'bar'}})

    def test_new_empty(self):
        """Test that new_empty method returns empty collection."""
        self._test_new_empty()


class TestAliasesDict(DataCollectionTestCase):

    """Test cases covering AliasesDict methods."""

    collection_class = AliasesDict

    family = 'wikipedia'
    code = 'en'

    dry = True

    def setUp(self):
        """Setup tests."""
        super().setUp()
        self.site = self.get_site()
        self.lang_out = {'en': ['foo', 'bar'],
                         'zh': ['foo', 'bar']}

    def test_init(self):
        """Test AliasesDict initializer."""
        ad = AliasesDict()
        self.assertLength(ad, 0)
        ad = AliasesDict(self.lang_out)
        self.assertLength(ad, 2)

    def test_setitem(self):
        """Test AliasesDict.__setitem__ metamethod."""
        ad = AliasesDict(self.lang_out)
        self.assertIn('en', ad)
        self.assertIn('zh', ad)
        ad[self.site] = ['baz']
        self.assertIn('en', ad)

    def test_getitem(self):
        """Test AliasesDict.__getitem__ metamethod."""
        ad = AliasesDict(self.lang_out)
        self.assertEqual(ad['en'], ['foo', 'bar'])
        self.assertEqual(ad[self.site], ['foo', 'bar'])
        self.assertIsNone(ad.get('de'))

    def test_delitem(self):
        """Test AliasesDict.__delitem__ metamethod."""
        ad = AliasesDict(self.lang_out)
        ad.pop(self.site)
        ad.pop('zh')
        self.assertNotIn('en', ad)
        self.assertNotIn('zh', ad)
        self.assertLength(ad, 0)

    def test_fromJSON(self):
        """Test AliasesDict.fromJSON method."""
        ad = AliasesDict.fromJSON(
            {'en': [{'language': 'en', 'value': 'foo'},
                    {'language': 'en', 'value': 'bar'}],
             'zh': [{'language': 'zh', 'value': 'foo'},
                    {'language': 'zh', 'value': 'bar'}],
             })
        self.assertIsInstance(ad, AliasesDict)
        self.assertEqual(ad, AliasesDict(self.lang_out))

    def test_toJSON(self):
        """Test AliasesDict.toJSON method."""
        ad = AliasesDict()
        self.assertEqual(ad.toJSON(), {})
        ad = AliasesDict(self.lang_out)
        self.assertEqual(
            ad.toJSON(),
            {'en': [{'language': 'en', 'value': 'foo'},
                    {'language': 'en', 'value': 'bar'}],
             'zh': [{'language': 'zh', 'value': 'foo'},
                    {'language': 'zh', 'value': 'bar'}],
             })

    def test_toJSON_diffto(self):
        """Test AliasesDict.toJSON method."""
        ad = AliasesDict(self.lang_out)
        diffto = {
            'de': [
                {'language': 'de', 'value': 'foo'},
                {'language': 'de', 'value': 'bar'},
            ],
            'en': [
                {'language': 'en', 'value': 'foo'},
                {'language': 'en', 'value': 'baz'},
            ]}
        self.assertEqual(
            ad.toJSON(diffto=diffto),
            {'de': [{'language': 'de', 'value': 'foo', 'remove': ''},
                    {'language': 'de', 'value': 'bar', 'remove': ''}],
             'en': [{'language': 'en', 'value': 'foo'},
                    {'language': 'en', 'value': 'bar'}],
             'zh': [{'language': 'zh', 'value': 'foo'},
                    {'language': 'zh', 'value': 'bar'}]
             })

    def test_normalizeData(self):
        """Test AliasesDict.normalizeData method."""
        data_in = {'en': [
            {'language': 'en', 'value': 'foo'},
            'bar',
            {'language': 'en', 'value': 'baz', 'remove': ''},
        ]}
        data_out = {'en': [
            {'language': 'en', 'value': 'foo'},
            {'language': 'en', 'value': 'bar'},
            {'language': 'en', 'value': 'baz', 'remove': ''},
        ]}
        self.assertEqual(AliasesDict.normalizeData(data_in), data_out)

    def test_new_empty(self):
        """Test that new_empty method returns empty collection."""
        self._test_new_empty()


class TestClaimCollection(DataCollectionTestCase):

    """Test cases covering ClaimCollection methods."""

    collection_class = ClaimCollection

    def test_new_empty(self):
        """Test that new_empty method returns empty collection."""
        self._test_new_empty()


class TestSiteLinkCollection(DataCollectionTestCase):

    """Test cases covering SiteLinkCollection methods."""

    collection_class = SiteLinkCollection

    def test_new_empty(self):
        """Test that new_empty method returns empty collection."""
        self._test_new_empty()


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
