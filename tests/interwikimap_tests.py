#!/usr/bin/env python3
"""Tests for the site module."""
#
# (C) Pywikibot team, 2018-2023
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

import pywikibot
from pywikibot.tools import suppress_warnings
from tests import WARN_SITE_CODE
from tests.aspects import TestCase


class TestInterwikiMap(TestCase):

    """Test interwiki map and methods."""

    sites = {
        'enwikinews': {
            'family': 'wikinews',
            'code': 'en',
        },
        'enwikibooks': {
            'family': 'wikibooks',
            'code': 'en',
        },
        'enwikiquote': {
            'family': 'wikiquote',
            'code': 'en',
        },
        'enwiktionary': {
            'family': 'wiktionary',
            'code': 'en',
        },
        'enws': {
            'family': 'wikisource',
            'code': 'en',
        },
        'dews': {
            'family': 'wikisource',
            'code': 'de',
        },
        'meta': {
            'family': 'meta',
            'code': 'meta',
        },
        'mediawiki': {
            'family': 'mediawiki',
            'code': 'mediawiki',
        },
        'commons': {
            'family': 'commons',
            'code': 'commons',
        },
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata',
        },
    }

    def test_interwikimap(self, key):
        """Test interwiki map."""
        site = self.get_site(key)
        iw_map = site._interwikimap
        self.assertEqual(site, iw_map._site)
        # test reset()
        iw_map._map = 'foo'
        iw_map.reset()
        self.assertIsNone(iw_map._map)

    def test_iw_entry(self):
        """Test interwiki map entry."""
        site = self.get_site('dews')
        iw_map = site._interwikimap
        self.assertIsNone(iw_map._map)
        iw_map._iw_sites  # load data
        self.assertIsInstance(iw_map._map, dict)
        for entry in iw_map._map.values():
            with self.subTest(url=entry.url):
                self.assertIsNone(entry._site)
                self.assertIsInstance(entry.local, bool)
                self.assertIsInstance(entry.prefix, str)
                if not entry.local:
                    continue

                self.assertTrue(
                    entry.url.startswith(('http', 'irc://')),
                    entry.url + ' does not start with "http" or "irc://')

    def test_interwiki(self, key):
        """Test site.interwiki method."""
        site = self.get_site(key)
        prefix = self.sites[key]['family']
        if prefix == 'mediawiki':
            with self.assertRaises(KeyError):
                site.interwiki(prefix)
        else:
            iw_site = site.interwiki(prefix)
            self.assertEqual(iw_site.family, site.family)


class TestInterwikiMapPrefix(TestCase):

    """Test interwiki map and methods."""

    family = 'wikipedia'
    code = 'en'

    def setUp(self):
        """Setup tests."""
        super().setUp()
        self.iw_map = self.site._interwikimap

    def test_items(self):
        """Test interwikimap items."""
        prefixes = {
            'commons': 'commons',
            'mediawikiwiki': 'mediawiki',
            'meta': 'meta',
            'test': 'wikipedia',
            'als': 'wikipedia',
            'bar': 'wikipedia',
            'de': 'wikipedia',
            'fr': 'wikipedia',
            'frr': 'wikipedia',
            'gsw': 'wikipedia',
            'mw': 'mediawiki',
            'nb': 'wikipedia',
            'no': 'wikipedia',
            'tr': 'wikipedia',
            'zh': 'wikipedia',
        }
        for prefix, family in prefixes.items():
            # special cases
            if prefix in ('gsw',  # unknown wikipedia language
                          'test',  # not an interwiki prefix
                          ):
                continue

            with suppress_warnings(WARN_SITE_CODE, category=UserWarning):
                item = self.iw_map[prefix]
                self.assertEqual(item._site, pywikibot.Site(prefix, family))
                self.assertTrue(item.local)

    def test_invalid_prefix(self):
        """Test wrong interwiki prefix."""
        for prefix in ('foo', 'mediawiki', 'test', ):
            with self.subTest(prefix=prefix), self.assertRaises(KeyError):
                self.iw_map[prefix]


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
