# -*- coding: utf-8  -*-
"""Tests for the family module."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

from pywikibot.family import Family
from pywikibot.exceptions import Error

from tests.aspects import (
    unittest,
    TestCase,
)


class TestFamily(TestCase):

    """Test cases for Family methods."""

    net = False

    def setUp(self):
        super(TestCase, self).setUp()

    def tearDown(self):
        super(TestCase, self).tearDown()

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
        family = Family.load('wikipedia', fatal=False)
        other = 'wikipedia'
        self.assertEqual(family, other)
        self.assertFalse(family != other)

    def test_ne_family_with_string_repr_different_family(self):
        """Test that Family and string with different name are not equal."""
        family = Family.load('wikipedia', fatal=False)
        other = 'wikisource'
        self.assertNotEqual(family, other)
        self.assertFalse(family == other)

    def test_eq_family_with_string_repr_not_existing_family(self):
        """Test that Family and string with different name are not equal."""
        family = Family.load('wikipedia', fatal=False)
        other = 'unknown'
        self.assertRaises(Error, family.__eq__, other)

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
