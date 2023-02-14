#!/usr/bin/env python3
"""Tests for the family module."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
from collections.abc import Mapping
from contextlib import suppress

import pywikibot
from pywikibot.exceptions import UnknownFamilyError
from pywikibot.family import Family, SingleSiteFamily
from pywikibot.tools import suppress_warnings
from tests.aspects import PatchingTestCase, TestCase, unittest
from tests.utils import DrySite


class TestFamily(TestCase):

    """Test cases for Family methods."""

    net = False

    def test_family_load_valid(self):
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

                with suppress_warnings(
                        'wowwiki_family.Family.languages_by_size '
                        'is deprecated'):
                    self.assertIsInstance(f.languages_by_size, list)
                    self.assertGreaterEqual(set(f.langs),
                                            set(f.languages_by_size))

                if isinstance(f, SingleSiteFamily):
                    self.assertIsNotNone(f.code)
                    self.assertIsNotNone(f.domain)
                    self.assertEqual(set(f.langs), {f.code})
                    self.assertEqual(set(f.codes), {f.code})

    def test_family_load_invalid(self):
        """Test that an invalid family raised UnknownFamilyError."""
        with self.assertRaisesRegex(
                UnknownFamilyError,
                'Family unknown does not exist'):
            Family.load('unknown')

    def test_new_same_family_singleton(self):
        """Test that two same Family are the same object and equal."""
        family_1 = Family.load('wikipedia')
        family_2 = Family.load('wikipedia')
        self.assertIs(family_1, family_2)
        self.assertEqual(family_1, family_2)

    def test_new_different_families_ne(self):
        """Test that two different Family are not same nor equal."""
        family_1 = Family.load('wikipedia')
        family_2 = Family.load('wiktionary')
        self.assertIsNot(family_1, family_2)
        self.assertNotEqual(family_1, family_2)

    def test_eq_family_with_string_repr_same_family(self):
        """Test that Family and string with same name are equal."""
        family = Family.load('wikipedia')
        other = 'wikipedia'
        self.assertEqual(family, other)
        self.assertFalse(family != other)  # noqa: H204

    def test_ne_family_with_string_repr_different_family(self):
        """Test that Family and string with different name are not equal."""
        family = Family.load('wikipedia')
        other = 'wikisource'
        self.assertNotEqual(family, other)
        self.assertFalse(family == other)  # noqa: H204

    def test_eq_family_with_string_repr_not_existing_family(self):
        """Test that Family and string with different name are not equal."""
        family = Family.load('wikipedia')
        other = 'unknown'
        with self.assertRaisesRegex(
                UnknownFamilyError,
                'Family unknown does not exist'):
            family.__eq__(other)

    def test_get_obsolete_wp(self):
        """Test three types of obsolete codes."""
        family = Family.load('wikipedia')
        self.assertIsInstance(family.obsolete, Mapping)
        # redirected code (see site tests test_alias_code_site)
        self.assertEqual(family.obsolete['dk'], 'da')
        # closed/locked site (see site tests test_locked_site)
        self.assertIsNone(family.obsolete['mh'])
        # offline site (see site tests test_removed_site)
        self.assertIsNone(family.obsolete['ru-sib'])
        self.assertIn('dk', family.interwiki_replacements)

    def test_set_obsolete(self):
        """Test obsolete can be set."""
        # Construct a temporary family and instantiate it
        family = type('TempFamily', (Family,), {})()

        self.assertEqual(family.obsolete, {})
        self.assertEqual(family.interwiki_replacements, {})
        self.assertEqual(family.interwiki_removals, [])

        family.obsolete = {'a': 'b', 'c': None}
        self.assertEqual(family.obsolete, {'a': 'b', 'c': None})
        self.assertEqual(family.interwiki_replacements, {'a': 'b'})
        self.assertEqual(family.interwiki_removals, ['c'])

    def test_obsolete_readonly(self):
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

    def test_WikimediaFamily_obsolete_readonly(self):
        """Test WikimediaFamily obsolete is readonly."""
        family = Family.load('wikipedia')
        with self.assertRaisesRegex(
                TypeError,
                "'frozenset' object does not support item assignment"):
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

    def setUp(self):
        """Setup default article path."""
        super().setUp()
        self.articlepath = '/wiki/$1'

    def test_from_url_wikipedia_extra(self):
        """Test various URLs against wikipedia regex."""
        self.current_code = 'vo'
        self.current_family = 'wikipedia'

        f = Family.load('wikipedia')

        prefix = 'https://vo.wikipedia.org'

        self.assertEqual(f.from_url(prefix + '/wiki/'), 'vo')
        self.assertEqual(f.from_url(prefix + '/w/index.php'), 'vo')
        self.assertEqual(f.from_url(prefix + '/w/index.php/'), 'vo')
        self.assertEqual(f.from_url(prefix + '/w/index.php?title=$1'), 'vo')

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

    def test_each_family(self):
        """Test each family builds a working regex."""
        for family in pywikibot.config.family_files:
            if family == 'wowwiki':
                self.skipTest(
                    'Family.from_url() does not work for {} (T215077)'
                    .format(family))
            self.current_family = family
            family = Family.load(family)
            for code in family.codes:
                self.current_code = code
                url = ('{}://{}{}/$1'.format(family.protocol(code),
                                             family.hostname(code),
                                             family.path(code)))
                # Families can switch off if they want to be detected using
                # URL. This applies for test:test (there is test:wikipedia)
                with self.subTest(url=url):
                    self.assertEqual(family.from_url(url), code)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
