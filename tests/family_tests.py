# -*- coding: utf-8 -*-
"""Tests for the family module."""
#
# (C) Pywikibot team, 2014-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot.site

from pywikibot.exceptions import UnknownFamily
from pywikibot.family import Family, SingleSiteFamily
from pywikibot.tools import StringTypes as basestring

from tests.aspects import (
    unittest,
    TestCase,
    DeprecationTestCase,
    PatchingTestCase,
)
from tests.utils import DrySite


class TestFamily(TestCase):

    """Test cases for Family methods."""

    UNKNOWNFAMILY_RE = 'Family unknown does not exist'
    FAMILY_TYPEERROR_RE = (
        'Family.obsolete not updatable; '
        'use Family.interwiki_removals and Family.interwiki_replacements')
    FROZENSET_TYPEERROR_RE = '\'frozenset\' object does not support item assignment'
    net = False

    def test_family_load_valid(self):
        """Test that a family can be loaded via Family.load."""
        for name in pywikibot.config.family_files:
            f = Family.load(name)
            self.assertIsInstance(f.langs, dict)
            self.assertTrue(f.langs)
            self.assertTrue(f.codes)
            self.assertTrue(iter(f.codes))
            self.assertIsInstance(next(iter(f.codes)), basestring)
            self.assertTrue(f.domains)
            self.assertTrue(iter(f.domains))
            for domain in f.domains:
                self.assertIsInstance(domain, basestring)
                if domain.split(':', 1)[0] != 'localhost':
                    self.assertIn('.', domain)
            self.assertEqual(f.name, name)
            self.assertIsInstance(f.languages_by_size, list)
            self.assertGreaterEqual(set(f.langs), set(f.languages_by_size))
            if len(f.langs) > 2 and f.name not in ['wikimediachapter', 'vikidia']:
                self.assertNotEqual(f.languages_by_size, [])
            if isinstance(f, SingleSiteFamily):
                self.assertIsNotNone(f.code)
                self.assertIsNotNone(f.domain)
                self.assertEqual(set(f.langs), {f.code})
                self.assertEqual(set(f.codes), {f.code})

    def test_family_load_invalid(self):
        """Test that an invalid family raised UnknownFamily exception."""
        self.assertRaisesRegex(
            UnknownFamily,
            self.UNKNOWNFAMILY_RE,
            Family.load,
            'unknown')

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
        self.assertFalse(family != other)

    def test_ne_family_with_string_repr_different_family(self):
        """Test that Family and string with different name are not equal."""
        family = Family.load('wikipedia')
        other = 'wikisource'
        self.assertNotEqual(family, other)
        self.assertFalse(family == other)

    def test_eq_family_with_string_repr_not_existing_family(self):
        """Test that Family and string with different name are not equal."""
        family = Family.load('wikipedia')
        other = 'unknown'
        self.assertRaisesRegex(
            UnknownFamily,
            self.UNKNOWNFAMILY_RE,
            family.__eq__,
            other)

    def test_get_obsolete_wp(self):
        """Test three types of obsolete codes."""
        family = Family.load('wikipedia')
        self.assertIsInstance(family.obsolete, dict)
        # redirected code (see site tests test_alias_code_site)
        self.assertEqual(family.obsolete['dk'], 'da')
        # closed/locked site (see site tests test_locked_site)
        self.assertEqual(family.obsolete['mh'], None)
        # offline site (see site tests test_removed_site)
        self.assertEqual(family.obsolete['ru-sib'], None)

    def test_get_obsolete_test(self):
        """Test WikimediaFamily default obsolete."""
        family = Family.load('test')
        self.assertIn('dk', family.obsolete)
        self.assertIn('dk', family.interwiki_replacements)
        self.assertEqual(family.obsolete, family.interwiki_replacements)
        self.assertEqual(family.interwiki_removals, set())

    def test_set_obsolete(self):
        """Test obsolete can be set."""
        # Construct a temporary family and instantiate it
        family = type(str('TempFamily'), (Family,), {})()

        self.assertEqual(family.obsolete, {})
        self.assertEqual(family.interwiki_replacements, {})
        self.assertEqual(family.interwiki_removals, [])

        family.obsolete = {'a': 'b', 'c': None}
        self.assertEqual(family.obsolete, {'a': 'b', 'c': None})
        self.assertEqual(family.interwiki_replacements, {'a': 'b'})
        self.assertEqual(family.interwiki_removals, ['c'])

    def test_obsolete_readonly(self):
        """Test obsolete result not updatable."""
        family = Family.load('test')
        self.assertRaisesRegex(
            TypeError,
            self.FAMILY_TYPEERROR_RE,
            family.obsolete.update,
            {})
        self.assertRaisesRegex(
            TypeError,
            self.FAMILY_TYPEERROR_RE,
            family.obsolete.__setitem__,
            'a',
            'b')

    def test_WikimediaFamily_obsolete_readonly(self):
        """Test WikimediaFamily obsolete is readonly."""
        family = Family.load('test')
        self.assertRaisesRegex(
            TypeError,
            self.FROZENSET_TYPEERROR_RE,
            family.__setattr__,
            'obsolete',
            {'a': 'b', 'c': None})


class TestFamilyUrlRegex(PatchingTestCase):

    """Test family URL regex."""

    net = False

    @PatchingTestCase.patched(pywikibot, 'Site')
    def Site(self, code, fam, *args, **kwargs):
        """Own DrySite creator."""
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {})
        self.assertEqual(code, self.current_code)
        self.assertEqual(fam, self.current_family)
        site = DrySite(code, fam, None, None)
        site._siteinfo._cache['general'] = ({'articlepath': self.article_path},
                                            True)
        return site

    def setUp(self):
        """Setup default article path."""
        super(TestFamilyUrlRegex, self).setUp()
        self.article_path = '/wiki/$1'

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

        # Text after $1 is not allowed
        self.assertRaisesRegex(
            ValueError,
            r'Text after the \$1 placeholder is not supported \(T111513\)',
            f.from_url,
            '//vo.wikipedia.org/wiki/$1/foo')

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
            self.current_family = family
            family = Family.load(family)
            for code in family.codes:
                self.current_code = code
                url = ('%s://%s%s/$1' % (family.protocol(code),
                                         family.hostname(code),
                                         family.path(code)))
                # Families can switch off if they want to be detected using URL
                # this applies for test:test (there is test:wikipedia)
                if family._ignore_from_url or code in family._ignore_from_url:
                    self.assertIsNone(family.from_url(url))
                else:
                    self.assertEqual(family.from_url(url), code)


class TestOldFamilyMethod(DeprecationTestCase):

    """Test cases for old site.Family method."""

    UNKNOWNFAMILY_RE = 'Family unknown does not exist'
    net = False

    def test_old_site_family_function(self):
        """Test deprecated Family function with valid families."""
        f = pywikibot.site.Family('species')
        self.assertEqual(f.name, 'species')
        f = pywikibot.site.Family('osm')
        self.assertEqual(f.name, 'osm')
        self.assertOneDeprecationParts('pywikibot.site.Family',
                                       'pywikibot.family.Family.load', 2)

        # @deprecated warning occurs within redirect_func's call
        # invoking the method instead of this test module.
        self._do_test_warning_filename = False

        f = pywikibot.site.Family('i18n', fatal=False)
        self.assertEqual(f.name, 'i18n')
        self.assertDeprecationParts('pywikibot.site.Family',
                                    'pywikibot.family.Family.load')
        self.assertDeprecationParts('fatal argument of pywikibot.family.Family.load')

    def test_old_site_family_function_invalid(self):
        """Test that an invalid family raised UnknownFamily exception."""
        # As assertRaises calls the method, unittest is the module
        # invoking the method instead of this test module.
        self._do_test_warning_filename = False
        self.assertRaisesRegex(
            UnknownFamily,
            self.UNKNOWNFAMILY_RE,
            pywikibot.site.Family,
            'unknown',
            fatal=False)
        self.assertRaisesRegex(
            UnknownFamily,
            self.UNKNOWNFAMILY_RE,
            pywikibot.site.Family,
            'unknown')
        self.assertDeprecationParts('pywikibot.site.Family',
                                    'pywikibot.family.Family.load')
        self.assertDeprecationParts('fatal argument of pywikibot.family.Family.load')


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
