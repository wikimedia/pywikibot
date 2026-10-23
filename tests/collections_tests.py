#!/usr/bin/env python3
#
# (C) Pywikibot team, 2019-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the Wikidata parts of the page module."""
from __future__ import annotations

import copy
import unittest
from contextlib import suppress

from pywikibot.page._collections import (
    AliasesDict,
    ClaimCollection,
    LanguageDict,
    SiteLinkCollection,
)
from pywikibot.page._wikibase import (
    LexemeFormCollection,
    LexemeSense,
    LexemeSenseCollection,
)
from tests.aspects import TestCase, WikidataTestCase


class TestSubEntityCollection(TestCase):

    """Test sub-entity collection indexing."""

    net = False

    def test_id_index_after_mutation(self) -> None:
        """Keep ID lookup consistent after deletion and insertion."""
        first = LexemeSense(None, 'L1-S1')
        second = LexemeSense(None, 'L1-S2')
        collection = LexemeSenseCollection(None, [first, second])

        del collection[first.id]
        self.assertIs(collection[second.id], second)

        collection.insert(0, first)
        self.assertIs(collection[first.id], first)
        self.assertIs(collection[second.id], second)

        del collection[-len(collection)]
        self.assertIs(collection[second.id], second)


class DataCollectionTestCase(WikidataTestCase):

    """Test case for a Wikibase collection class."""

    collection_class = None

    def _test_new_empty(self) -> None:
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

    def setUp(self) -> None:
        """Set up tests."""
        super().setUp()
        self.site = self.get_site()
        self.lang_out = {'en': 'foo', 'zh': 'bar'}

    def test_init(self) -> None:
        """Test LanguageDict initializer."""
        ld = LanguageDict()
        self.assertLength(ld, 0)
        ld = LanguageDict(self.lang_out)
        self.assertLength(ld, 2)

    def test_setitem(self) -> None:
        """Test LanguageDict.__setitem__ metamethod."""
        ld = LanguageDict(self.lang_out)
        self.assertIn('en', ld)
        ld[self.site] = 'bar'
        self.assertIn('en', ld)

    def test_getitem(self) -> None:
        """Test LanguageDict.__getitem__ metamethod."""
        ld = LanguageDict(self.lang_out)
        self.assertEqual(ld['en'], 'foo')
        self.assertEqual(ld[self.site], 'foo')
        self.assertIsNone(ld.get('de'))

    def test_delitem(self) -> None:
        """Test LanguageDict.__delitem__ metamethod."""
        ld = LanguageDict(self.lang_out)
        ld.pop(self.site)
        ld.pop('zh')
        self.assertNotIn('en', ld)
        self.assertNotIn('zh', ld)
        self.assertLength(ld, 0)

    def test_fromJSON(self) -> None:
        """Test LanguageDict.fromJSON method."""
        ld = LanguageDict.fromJSON(
            {'en': {'language': 'en', 'value': 'foo'},
             'zh': {'language': 'zh', 'value': 'bar'}})
        self.assertIsInstance(ld, LanguageDict)
        self.assertEqual(ld, LanguageDict(self.lang_out))

    def test_toJSON(self) -> None:
        """Test LanguageDict.toJSON method."""
        ld = LanguageDict()
        self.assertEqual(ld.toJSON(), {})
        ld = LanguageDict(self.lang_out)
        self.assertEqual(
            ld.toJSON(), {'en': {'language': 'en', 'value': 'foo'},
                          'zh': {'language': 'zh', 'value': 'bar'}})

    def test_toJSON_diffto(self) -> None:
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

    def test_normalizeData(self) -> None:
        """Test LanguageDict.normalizeData method."""
        self.assertEqual(
            LanguageDict.normalizeData(self.lang_out),
            {'en': {'language': 'en', 'value': 'foo'},
             'zh': {'language': 'zh', 'value': 'bar'}})

    def test_new_empty(self) -> None:
        """Test that new_empty method returns empty collection."""
        self._test_new_empty()


class TestAliasesDict(DataCollectionTestCase):

    """Test cases covering AliasesDict methods."""

    collection_class = AliasesDict

    family = 'wikipedia'
    code = 'en'

    dry = True

    def setUp(self) -> None:
        """Set up tests."""
        super().setUp()
        self.site = self.get_site()
        self.lang_out = {'en': ['foo', 'bar'],
                         'zh': ['foo', 'bar']}

    def test_init(self) -> None:
        """Test AliasesDict initializer."""
        ad = AliasesDict()
        self.assertLength(ad, 0)
        ad = AliasesDict(self.lang_out)
        self.assertLength(ad, 2)

    def test_setitem(self) -> None:
        """Test AliasesDict.__setitem__ metamethod."""
        ad = AliasesDict(self.lang_out)
        self.assertIn('en', ad)
        self.assertIn('zh', ad)
        ad[self.site] = ['baz']
        self.assertIn('en', ad)

    def test_getitem(self) -> None:
        """Test AliasesDict.__getitem__ metamethod."""
        ad = AliasesDict(self.lang_out)
        self.assertEqual(ad['en'], ['foo', 'bar'])
        self.assertEqual(ad[self.site], ['foo', 'bar'])
        self.assertIsNone(ad.get('de'))

    def test_delitem(self) -> None:
        """Test AliasesDict.__delitem__ metamethod."""
        ad = AliasesDict(self.lang_out)
        ad.pop(self.site)
        ad.pop('zh')
        self.assertNotIn('en', ad)
        self.assertNotIn('zh', ad)
        self.assertLength(ad, 0)

    def test_fromJSON(self) -> None:
        """Test AliasesDict.fromJSON method."""
        ad = AliasesDict.fromJSON(
            {'en': [{'language': 'en', 'value': 'foo'},
                    {'language': 'en', 'value': 'bar'}],
             'zh': [{'language': 'zh', 'value': 'foo'},
                    {'language': 'zh', 'value': 'bar'}],
             })
        self.assertIsInstance(ad, AliasesDict)
        self.assertEqual(ad, AliasesDict(self.lang_out))

    def test_toJSON(self) -> None:
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

    def test_toJSON_diffto(self) -> None:
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

    def test_normalizeData(self) -> None:
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

    def test_new_empty(self) -> None:
        """Test that new_empty method returns empty collection."""
        self._test_new_empty()


class TestSubEntityJSON(DataCollectionTestCase):

    """Test full serialization, diffs and explicit child operations."""

    dry = True

    def test_collection_diff(self) -> None:
        """Match saved IDs and keep multiple unsaved children distinct."""
        for cls, prefix, key in (
            (LexemeFormCollection, 'L1-F', 'representations'),
            (LexemeSenseCollection, 'L1-S', 'glosses'),
        ):
            with self.subTest(cls=cls):
                baseline = [
                    {'id': prefix + str(index), key: {
                        'en': {'language': 'en', 'value': str(index)}}}
                    for index in (1, 2)
                ]
                if cls is LexemeFormCollection:
                    for entry in baseline:
                        entry['grammaticalFeatures'] = []
                original = copy.deepcopy(baseline)
                collection = cls.fromJSON(baseline, self.get_repo())
                self.assertEqual(collection.toJSON(), baseline)
                self.assertEqual(collection.toJSON(diffto=[]), baseline)
                self.assertEqual(collection.toJSON(diffto=baseline), [])
                getattr(collection[0], key)['en'] = 'changed'
                del collection[1]
                for value in ('new one', 'new two'):
                    entity = cls.type_class(self.get_repo())
                    getattr(entity, key)['en'] = value
                    collection.append(entity)
                changes = collection.toJSON(diffto=baseline)
                self.assertEqual(changes[0], {
                    'id': prefix + '1', key: {
                        'en': {'language': 'en', 'value': 'changed'}}})
                self.assertEqual([entry[key]['en']['value']
                                  for entry in changes[1:3]],
                                 ['new one', 'new two'])
                for entry in changes[1:3]:
                    self.assertEqual(entry['add'], '')
                    self.assertNotIn('id', entry)
                self.assertEqual(changes[-1],
                                 {'id': prefix + '2', 'remove': ''})
                self.assertEqual(baseline, original)
                pending = cls(self.get_repo(), list(collection)[1:])
                pending.clear()
                self.assertEqual(pending.toJSON(), [])
                empty = cls.new_empty(self.get_repo())
                self.assertEqual(empty.toJSON(diffto=baseline), [
                    {'id': entry['id'], 'remove': ''} for entry in baseline])
                with self.assertRaisesRegex(ValueError, 'Duplicate'):
                    collection.toJSON(diffto=baseline + baseline)
                collection.append(collection[0])
                with self.assertRaisesRegex(ValueError, 'Duplicate'):
                    collection.toJSON()

    def test_normalize_operations(self) -> None:
        """Preserve operation markers and reject ambiguous operations."""
        data = [
            {'id': 'L1-F1', 'representations': {'en': 'changed'}},
            {'add': '', 'representations': {'en': 'new'},
             'grammaticalFeatures': []},
            {'id': 'L1-F2', 'remove': ''},
        ]
        original = copy.deepcopy(data)
        normalized = LexemeFormCollection.normalizeData(data)
        self.assertEqual(normalized, [
            {'id': 'L1-F1', 'representations': {
                'en': {'language': 'en', 'value': 'changed'}}},
            {'add': '', 'representations': {
                'en': {'language': 'en', 'value': 'new'}},
             'grammaticalFeatures': []},
            {'id': 'L1-F2', 'remove': ''},
        ])
        self.assertEqual(data, original)
        self.assertEqual(LexemeFormCollection.normalizeData(normalized),
                         normalized)
        for invalid in ({}, {'remove': ''}, {'add': '', 'remove': ''},
                        {'id': 'L1-F1', 'add': ''}):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                LexemeFormCollection.normalizeData([invalid])


class TestClaimCollection(DataCollectionTestCase):

    """Test cases covering ClaimCollection methods."""

    collection_class = ClaimCollection

    def test_new_empty(self) -> None:
        """Test that new_empty method returns empty collection."""
        self._test_new_empty()


class TestSiteLinkCollection(DataCollectionTestCase):

    """Test cases covering SiteLinkCollection methods."""

    collection_class = SiteLinkCollection

    def test_new_empty(self) -> None:
        """Test that new_empty method returns empty collection."""
        self._test_new_empty()


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
