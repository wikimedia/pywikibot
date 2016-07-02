# -*- coding: utf-8 -*-
"""Test add_text bot module."""
#
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import pywikibot

from scripts.add_text import add_text

from tests.aspects import unittest, TestCase


class TestAdding(TestCase):

    """Test adding text."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def test_basic(self):
        """Test adding text."""
        page = pywikibot.Page(self.site, 'foo')
        (text, newtext, always) = add_text(
            page, 'bar', putText=False,
            oldTextGiven='foo\n{{linkfa}}')
        self.assertEqual(
            'foo\n{{linkfa}}\nbar',
            newtext)

    def test_with_category(self):
        """Test adding text before categories."""
        page = pywikibot.Page(self.site, 'foo')
        (text, newtext, always) = add_text(
            page, 'bar', putText=False,
            oldTextGiven='foo\n[[Category:Foo]]')
        self.assertEqual(
            'foo\nbar\n\n[[Category:Foo]]',
            newtext)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
