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


class TestStarList(TestCase):

    """Test starlist."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def test_basic(self):
        """Test adding text before {{linkfa}} without parameters."""
        page = pywikibot.Page(self.site, 'foo')
        (text, newtext, always) = add_text(
            page, 'bar', putText=False,
            oldTextGiven='foo\n{{linkfa}}')
        self.assertEqual(
            'foo\n{{linkfa}}\nbar',
            newtext)

    def test_with_params(self):
        """Test adding text before {{linkfa|...}}."""
        page = pywikibot.Page(self.site, 'foo')
        (text, newtext, always) = add_text(
            page, 'bar', putText=False,
            oldTextGiven='foo\n{{linkfa|...}}')
        self.assertEqual(
            'foo\nbar\n\n{{linkfa|...}}\n',
            newtext)


if __name__ == "__main__":
    unittest.main()
