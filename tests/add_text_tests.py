"""Test add_text bot module."""
#
# (C) Pywikibot team, 2016-2021
#
# Distributed under the terms of the MIT license.
#
import unittest

import pywikibot

from scripts.add_text import add_text, get_text

from tests.aspects import TestCase


class TestAdding(TestCase):

    """Test adding text."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def setUp(self):
        """Setup test."""
        super().setUp()
        self.page = pywikibot.Page(self.site, 'foo')

    def test_basic(self):
        """Test adding text."""
        (_, newtext, _) = add_text(
            self.page, 'bar', putText=False,
            oldTextGiven='foo\n{{linkfa}}')
        self.assertEqual(
            'foo\n{{linkfa}}\nbar',
            newtext)

    def test_with_category(self):
        """Test adding text before categories."""
        (_, newtext, _) = add_text(
            self.page, 'bar', putText=False,
            oldTextGiven='foo\n[[Category:Foo]]')
        self.assertEqual(
            'foo\nbar\n\n[[Category:Foo]]',
            newtext)

    def test_get_text(self):
        """Test get_text with given text."""
        self.assertEqual(get_text(self.page, 'foo', False), 'foo')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
