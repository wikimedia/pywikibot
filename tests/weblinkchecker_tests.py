#!/usr/bin/env python3
"""Tests for the weblinkchecker script."""
#
# (C) Pywikibot team, 2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest
from contextlib import suppress

import pywikibot
from scripts.weblinkchecker import WeblinkCheckerRobot
from tests.aspects import TestCase


class TestWeblinkchecker(TestCase):

    """Test cases for weblinkchecker."""

    family = 'wikipedia'
    code = 'test'

    def test_different_uri_schemes(self) -> None:
        """Test different uri schemes on test page."""
        site = self.get_site('wikipedia:test')
        page = pywikibot.Page(site, 'User:DerIch27/weblink test')
        generator = [page]
        bot = WeblinkCheckerRobot(site=site, generator=generator)
        bot.run()
        self.assertEqual(1, bot.counter['read'])


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
