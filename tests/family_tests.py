# -*- coding: utf-8  -*-
"""Tests for the family module."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
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
            'pywikibot.site.Family is DEPRECATED, use pywikibot.family.Family.load instead.')

        f = pywikibot.site.Family('i18n', fatal=False)
        self.assertEqual(f.name, 'i18n')
        self.assertDeprecation(
            'pywikibot.site.Family is DEPRECATED, use pywikibot.family.Family.load instead.')
        self.assertDeprecation('fatal argument of pywikibot.family.Family.load is deprecated.')

    def test_old_site_family_function_invalid(self):
        """Test that an invalid family raised UnknownFamily exception."""
        self.assertRaises(UnknownFamily, pywikibot.site.Family, 'unknown',
                          fatal=False)
        self.assertRaises(UnknownFamily, pywikibot.site.Family, 'unknown')
        self.assertDeprecation(
            'pywikibot.site.Family is DEPRECATED, use pywikibot.family.Family.load instead.')
        self.assertDeprecation('fatal argument of pywikibot.family.Family.load is deprecated.')


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
