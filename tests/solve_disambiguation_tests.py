# -*- coding: utf-8 -*-
"""Test solve_disambiguation bot module."""
#
# (C) Pywikibot team, 2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot

from scripts.solve_disambiguation import DisambiguationRobot

from tests.aspects import TestCase, unittest


class TestGettingDisambigLinks(TestCase):
    """Test getting disambiguation links."""

    family = 'wikipedia'
    code = 'en'

    def test_get(self):
        """Test getting disambiguation links."""
        page = pywikibot.Page(self.site, 'foo')
        bot = DisambiguationRobot(None, [], True, False, None, False, False,
                                  minimum=0)
        page.text = '* [[Link1]]\n* [[Link2]]'
        newlinks = bot.get_disambiguation_links(page)
        links = ['Link1', 'Link2']
        self.assertEqual(newlinks, links)

    def test_get_without_templates(self):
        """Test excluding links from disamb_templates."""
        page = pywikibot.Page(self.site, 'foo')
        bot = DisambiguationRobot(None, [], True, False, None, False, False,
                                  minimum=0)
        page.text = '* [[Link1]]\n{{Disambig}}'
        newlinks = bot.get_disambiguation_links(page)
        links = ['Link1']
        self.assertEqual(newlinks, links)


if __name__ == '__main__':
    unittest.main()
