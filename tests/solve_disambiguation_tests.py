#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the solve_disambiguation script."""
from __future__ import annotations

import unittest
from contextlib import suppress
from unittest.mock import patch

import pywikibot
from scripts.solve_disambiguation import DisambiguationRobot
from tests.aspects import TestCase


class TestDisambiguationRobot(TestCase):

    """Test the disambiguation bot."""

    family = 'wikipedia'
    code = 'de'
    dry = True

    def setUp(self) -> None:
        """Create a bot for each test."""
        super().setUp()
        self.bot = DisambiguationRobot(site=self.site, generator=[])
        self.bot.setup()

    def _assert_replacement(self, source: str, replacement: str,
                            expected: str) -> None:
        """Assert the replacement produced by the bot."""
        self.bot.opt.pos = [replacement]
        disamb_page = pywikibot.Page(self.site, 'Rasenmähen')
        ref_page = pywikibot.Page(self.site, 'Beispiel')
        with patch.object(ref_page, 'get', return_value=source), \
                patch.object(ref_page, 'put') as put, \
                patch.object(self.bot, 'setSummaryMessage'), \
                patch('scripts.solve_disambiguation.ShowPageOption'), \
                patch('pywikibot.input_choice',
                      return_value=('', replacement)):
            result = self.bot.treat_disamb_only(ref_page, disamb_page)

        self.assertEqual(result, 'done')
        put.assert_called_once()
        self.assertEqual(put.call_args.args[0], expected)

    def test_replacement_section(self) -> None:
        """Test replacing a link and its section."""
        self._assert_replacement(
            '[[Rasenmähen#Rasenmähen|Rasenmähen]]',
            'Mähen#Rasenmähen',
            '[[Mähen#Rasenmähen|Rasenmähen]]',
        )

    def test_different_replacement_section(self) -> None:
        """Test that the replacement section overrides the old section."""
        self._assert_replacement(
            '[[Rasenmähen#Alt|Rasenmähen]]',
            'Mähen#Neu',
            '[[Mähen#Neu|Rasenmähen]]',
        )

    def test_source_section(self) -> None:
        """Test preserving the source section when none replaces it."""
        self._assert_replacement(
            '[[Rasenmähen#Alt|Rasenmähen]]',
            'Mähen',
            '[[Mähen#Alt|Rasenmähen]]',
        )


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
