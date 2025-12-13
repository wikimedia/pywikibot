#!/usr/bin/env python3
"""Test fixing redirects bot module."""
#
# (C) Pywikibot team, 2018-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest

import pywikibot
from scripts.fixing_redirects import FixingRedirectBot
from tests.aspects import TestCase


class TestFixingRedirects(TestCase):

    """Test fixing redirects."""

    family = 'wikipedia'
    code = 'en'

    def test_disabled(self) -> None:
        """Test disabled parts of fixing redirects."""
        bot = FixingRedirectBot()
        text = ('<!--[[Template:Doc]]--><source>[[Template:Doc]]</source>'
                '[[:cs:Template:Dokumentace]][[#Documentation]]')
        linked = pywikibot.Page(self.site, 'Template:Doc')
        target = pywikibot.Page(self.site, 'Template:Documentation')
        new_text = bot.replace_links(text, linked, target)
        self.assertEqual(text, new_text)


if __name__ == '__main__':
    unittest.main()
