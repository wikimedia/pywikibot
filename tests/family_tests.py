# -*- coding: utf-8  -*-
"""Tests for the family module."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot.family import Family
from pywikibot.exceptions import UnknownFamily

import pywikibot.site

from tests.aspects import (
    unittest,
    TestCase,
    DeprecationTestCase,
)


class TestFamily(TestCase):

    """Test cases for Family methods."""

    net = False

    def test_family_load_valid(self):
        """Test that a family can be loaded via Family.load."""
        for name in pywikibot.config.family_files:
            f = Family.load(name)
            self.assertIsInstance(f.langs, dict)
            self.assertNotEqual(f.langs, {})
            # There is one inconsistency
            if f.name == 'wikimediachapter' and name == 'wikimedia':
                continue
            self.assertEqual(f.name, name)

    def test_family_load_invalid(self):
        """Test that an invalid family raised UnknownFamily exception."""
        self.assertRaises(UnknownFamily, Family.load, 'unknown')

    def test_eq_different_families_by_name(self):
        """Test that two Family with same name are equal."""
        family_1 = Family()
        family_2 = Family()
        family_1.name = 'a'
        family_2.name = 'a'
        self.assertNotEqual(id(family_1), id(family_2))
        self.assertEqual(family_1, family_2)

    def test_eq_different_families_by_id(self):
        """Test that two Family with no name attribute are not equal."""
        family_1 = Family()
        family_2 = Family()
        family_1.name = 'a'
        del family_2.name
        self.assertNotEqual(id(family_1), id(family_2))
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
        self.assertRaises(UnknownFamily, family.__eq__, other)

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
        family = Family()
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
        self.assertRaises(TypeError, family.obsolete.update, {})
        self.assertRaises(TypeError, family.obsolete.__setitem__, 'a', 'b')

    def test_WikimediaFamily_obsolete_readonly(self):
        """Test WikimediaFamily obsolete is readonly."""
        family = Family.load('test')
        self.assertRaises(TypeError, family.__setattr__, 'obsolete',
                          {'a': 'b', 'c': None})


class TestFamilyUrlRegex(TestCase):

    """Test family URL regex."""

    net = False

    def test_get_regex_wikipedia_precise(self):
        """Test the family regex is optimal."""
        f = Family.load('wikipedia')
        regex = f._get_regex_all()

        self.assertTrue(regex.startswith('(?:\/\/|https\:\/\/)('))
        self.assertIn('vo\.wikipedia\.org', regex)
        self.assertTrue(regex.endswith(')(?:\/w\/index\.php\/?|\/wiki\/)'))

    def test_from_url_wikipedia_extra(self):
        """Test various URLs against wikipedia regex."""
        f = Family.load('wikipedia')

        prefix = 'https://vo.wikipedia.org'

        self.assertEqual(f.from_url(prefix + '/wiki/'), 'vo')
        self.assertEqual(f.from_url(prefix + '/w/index.php'), 'vo')
        self.assertEqual(f.from_url(prefix + '/w/index.php/'), 'vo')
        self.assertEqual(f.from_url(prefix + '/w/index.php?title=$1'), 'vo')

        self.assertEqual(f.from_url(prefix + '/wiki/$1'), 'vo')
        self.assertEqual(f.from_url('//vo.wikipedia.org/wiki/$1'), 'vo')
        self.assertEqual(f.from_url('//vo.wikipedia.org/wiki/$1/foo'), 'vo')
        self.assertEqual(f.from_url(prefix + '/w/index.php/$1'), 'vo')
        self.assertEqual(f.from_url('//vo.wikipedia.org/wiki/$1'), 'vo')
        self.assertEqual(f.from_url('//vo.wikipedia.org/wiki/$1/foo'), 'vo')

        # wrong protocol
        self.assertIsNone(f.from_url('http://vo.wikipedia.org/wiki/$1'))
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
            family = Family.load(family)
            # Test family does not respond to from_url due to overlap
            # with Wikipedia family.
            if family.name == 'test':
                continue
            for code in family.langs:
                url = ('%s://%s%s$1' % (family.protocol(code),
                                        family.hostname(code),
                                        family.path(code)))
                self.assertEqual(family.from_url(url), code)


class TestOldFamilyMethod(DeprecationTestCase):

    """Test cases for old site.Family method."""

    net = False

    def test_old_site_family_function(self):
        """Test deprecated Family function with valid families."""
        f = pywikibot.site.Family('species')
        self.assertEqual(f.name, 'species')
        f = pywikibot.site.Family('osm')
        self.assertEqual(f.name, 'osm')
        self.assertDeprecation(
            'pywikibot.site.Family is deprecated, use pywikibot.family.Family.load instead.')

        # @deprecated warning occurs within redirect_func's call
        # invoking the method instead of this test module.
        self._do_test_warning_filename = False

        f = pywikibot.site.Family('i18n', fatal=False)
        self.assertEqual(f.name, 'i18n')
        self.assertDeprecation(
            'pywikibot.site.Family is deprecated, use pywikibot.family.Family.load instead.')
        self.assertDeprecation('fatal argument of pywikibot.family.Family.load is deprecated.')

    def test_old_site_family_function_invalid(self):
        """Test that an invalid family raised UnknownFamily exception."""
        # As assertRaises calls the method, unittest is the module
        # invoking the method instead of this test module.
        self._do_test_warning_filename = False
        self.assertRaises(UnknownFamily, pywikibot.site.Family, 'unknown',
                          fatal=False)
        self.assertRaises(UnknownFamily, pywikibot.site.Family, 'unknown')
        self.assertDeprecation(
            'pywikibot.site.Family is deprecated, use pywikibot.family.Family.load instead.')
        self.assertDeprecation('fatal argument of pywikibot.family.Family.load is deprecated.')


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
