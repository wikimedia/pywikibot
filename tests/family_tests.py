#!/usr/bin/env python3
"""Tests for the family module."""
#
# (C) Pywikibot team, 2014-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from collections.abc import Mapping
from contextlib import suppress

import pywikibot
from pywikibot.exceptions import UnknownFamilyError
from pywikibot.family import Family, SingleSiteFamily
from tests.aspects import PatchingTestCase, TestCase, unittest
from tests.utils import DrySite


class TestFamily(TestCase):

    """Test cases for Family methods."""

    net = False

    def test_family_load_valid(self) -> None:
        """Test that a family can be loaded via Family.load."""
        for name in pywikibot.config.family_files:
            with self.subTest(family=name):
                f = Family.load(name)
                self.assertIsInstance(f.langs, dict)
                self.assertTrue(f.langs)
                self.assertTrue(f.codes)
                self.assertTrue(iter(f.codes))
                self.assertIsInstance(next(iter(f.codes)), str)
                self.assertTrue(f.domains)
                self.assertTrue(iter(f.domains))
                for domain in f.domains:
                    self.assertIsInstance(domain, str)
                    if not domain.startswith('localhost:'):
                        self.assertIn('.', domain)

                self.assertEqual(f.name, name)
                self.assertIsInstance(f.codes, set)
                self.assertGreaterEqual(set(f.langs), set(f.codes))

                if isinstance(f, SingleSiteFamily):
                    self.assertIsNotNone(f.code)
                    self.assertIsNotNone(f.domain)
                    self.assertEqual(set(f.langs), {f.code})
                    self.assertEqual(set(f.codes), {f.code})

    def test_family_load_invalid(self) -> None:
        """Test that an invalid family raised UnknownFamilyError."""
        with self.assertRaisesRegex(
                UnknownFamilyError,
                'Family unknown does not exist'):
            Family.load('unknown')

    def test_new_same_family_singleton(self) -> None:
        """Test that two same Family are the same object and equal."""
        family_1 = Family.load('wikipedia')
        family_2 = Family.load('wikipedia')
        self.assertIs(family_1, family_2)
        self.assertEqual(family_1, family_2)

    def test_new_different_families_ne(self) -> None:
        """Test that two different Family are not same nor equal."""
        family_1 = Family.load('wikipedia')
        family_2 = Family.load('wiktionary')
        self.assertIsNot(family_1, family_2)
        self.assertNotEqual(family_1, family_2)

    def test_eq_family_with_string_repr_same_family(self) -> None:
        """Test that Family and string with same name are equal."""
        family = Family.load('wikipedia')
        other = 'wikipedia'
        self.assertEqual(family, other)
        self.assertFalse(family != other)

    def test_ne_family_with_string_repr_different_family(self) -> None:
        """Test that Family and string with different name are not equal."""
        family = Family.load('wikipedia')
        other = 'wikisource'
        self.assertNotEqual(family, other)
        self.assertFalse(family == other)

    def test_eq_family_with_string_repr_not_existing_family(self) -> None:
        """Test that Family and string with different name are not equal."""
        family = Family.load('wikipedia')
        other = 'unknown'
        with self.assertRaisesRegex(
                UnknownFamilyError,
                'Family unknown does not exist'):
            family.__eq__(other)

    def test_get_obsolete_wp(self) -> None:
        """Test three types of obsolete codes."""
        family = Family.load('wikipedia')
        self.assertIsInstance(family.obsolete, Mapping)
        # redirected code (see site tests test_alias_code_site)
        self.assertEqual(family.code_aliases['dk'], 'da')
        self.assertEqual(family.interwiki_replacements['dk'], 'da')
        self.assertEqual(family.obsolete['dk'], 'da')
        # closed/locked site (see site tests test_locked_site)
        self.assertIsNone(family.obsolete['mh'])
        # offline site (see site tests test_removed_site)
        self.assertIsNone(family.obsolete['ru-sib'])
        self.assertIn('dk', family.interwiki_replacements)

    def test_obsolete_from_attributes(self) -> None:
        """Test obsolete property for given class attributes."""
        # Construct a temporary family and instantiate it
        family = type('TempFamily', (Family,), {})()

        self.assertEqual(family.obsolete, {})
        self.assertEqual(family.interwiki_replacements, {})
        self.assertEqual(family.interwiki_removals, frozenset())

        # Construct a temporary family with other attributes and instantiate it
        family = type('TempFamily', (Family,),
                      {'code_aliases': {'a': 'b'}, 'closed_wikis': ['c']})()
        self.assertEqual(family.obsolete, {'a': 'b', 'c': None})
        self.assertEqual(family.interwiki_replacements, {'a': 'b'})
        self.assertEqual(family.interwiki_removals, frozenset('c'))

    def test_obsolete_readonly(self) -> None:
        """Test obsolete result not updatable."""
        family = Family.load('wikipedia')
        with self.assertRaisesRegex(
                AttributeError,
                "'mappingproxy' object has no attribute 'update'"):
            family.obsolete.update({})

        with self.assertRaisesRegex(
                TypeError,
                "'mappingproxy' object does not support item assignment"):
            family.obsolete['a'] = 'b'

        with self.assertRaisesRegex(
                AttributeError,
                "property 'obsolete' of 'Family' object has no setter|"
                "can't set attribute"):
            family.obsolete = {'a': 'b', 'c': None}


class TestFamilyUrlRegex(PatchingTestCase):

    """Test family URL regex."""

    net = False

    @PatchingTestCase.patched(pywikibot, 'Site')
    def Site(self, *args, **kwargs):
        """Own DrySite creator."""
        code, fam, *args = args
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {})
        self.assertEqual(code, self.current_code)
        self.assertEqual(fam, self.current_family)
        site = DrySite(code, fam, None)
        site._siteinfo._cache['general'] = ({'articlepath': self.articlepath},
                                            True)
        return site

    def setUp(self) -> None:
        """Setup default article path."""
        super().setUp()
        self.articlepath = '/wiki/$1'

    def test_from_url(self) -> None:
        """Test various URLs for Family.from_url."""
        self.current_code = 'vo'
        self.current_family = 'wikipedia'

        f = Family.load('wikipedia')

        prefix = 'https://vo.wikipedia.org'

        self.assertEqual(f.from_url(prefix + '/wiki/'), 'vo')
        self.assertEqual(f.from_url(prefix + '/w/index.php'), 'vo')
        self.assertEqual(f.from_url(prefix + '/w/index.php/'), 'vo')
        self.assertEqual(f.from_url(prefix + '/w/index.php?title=$1'), 'vo')
        # url without scripts/api path
        self.assertEqual(f.from_url(prefix), 'vo')

        self.assertEqual(f.from_url(prefix + '/wiki/$1'), 'vo')
        self.assertEqual(f.from_url('//vo.wikipedia.org/wiki/$1'), 'vo')
        self.assertEqual(f.from_url(prefix + '/w/index.php/$1'), 'vo')
        self.assertEqual(f.from_url('//vo.wikipedia.org/wiki/$1'), 'vo')
        # including title
        self.assertEqual(f.from_url(prefix + '/wiki/Main_page'), 'vo')
        self.assertEqual(f.from_url(prefix + '/w/index.php?title=Foo'), 'vo')

        # Text after $1 is allowed
        self.assertEqual(f.from_url('//vo.wikipedia.org/wiki/$1/foo'), 'vo')

        # the IWM may contain the wrong protocol, but it's only used to
        # determine a site so using HTTP or HTTPS is not an issue
        self.assertEqual(f.from_url('http://vo.wikipedia.org/wiki/$1'), 'vo')

        # wrong protocol
        self.assertIsNone(f.from_url('ftp://vo.wikipedia.org/wiki/$1'))
        # wrong code
        self.assertIsNone(f.from_url('https://foobar.wikipedia.org/wiki/$1'))
        # wrong family
        self.assertIsNone(f.from_url('https://vo.wikibooks.org/wiki/$1'))
        self.assertIsNone(f.from_url('http://vo.wikibooks.org/wiki/$1'))
        # invalid path
        self.assertIsNone(f.from_url('https://vo.wikipedia.org/wik/$1'))
        self.assertIsNone(f.from_url('https://vo.wikipedia.org/index.php/$1'))

    def test_each_family(self) -> None:
        """Test each family builds a working regex."""
        for family in pywikibot.config.family_files:
            if family == 'wowwiki':
                self.skipTest(
                    f'Family.from_url() does not work for {family} (T215077)')
            self.current_family = family
            family = Family.load(family)
            for code in family.codes:
                self.current_code = code
                url = f'{family.protocol(code)}://{family.hostname(code)}'
                url_with_path = url + f'{family.path(code)}/$1'
                with self.subTest(url=url):
                    self.assertEqual(family.from_url(url), code)
                    self.assertEqual(family.from_url(url_with_path), code)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
