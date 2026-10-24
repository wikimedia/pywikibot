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
from scripts.solve_disambiguation import (
    DisambiguationRobot,
    ReferringPageGeneratorWithIgnore,
)
from tests.aspects import TestCase


class TestReferringPageGenerator(TestCase):

    """Test streaming and the minimum eligible reference count."""

    family = 'wikipedia'
    code = 'de'
    dry = True

    def test_streaming(self) -> None:
        """Yield the first reference without consuming the remaining ones."""
        page = pywikibot.Page(self.site, 'Disambiguation')
        ignored = pywikibot.Page(self.site, 'Primary')
        ref = pywikibot.Page(self.site, 'Article')

        def references():
            yield ignored
            yield ref
            self.fail(
                'References were consumed before yielding the first page')

        with patch('scripts.solve_disambiguation.ignore_title', {}), \
                patch.object(page, 'getReferences',
                             return_value=references()) as get_refs, \
                patch('scripts.solve_disambiguation.PrimaryIgnoreManager'
                      '.isIgnored', side_effect=lambda page: page == ignored):
            gen = iter(ReferringPageGeneratorWithIgnore(page, main_only=True))
            self.assertEqual(next(gen), ref)
            get_refs.assert_called_once_with(with_template_inclusion=False,
                                             namespaces=0)
            gen.close()

    def test_minimum_after_filtering(self) -> None:
        """Buffer eligible pages only, and skip if the minimum is unmet."""
        page = pywikibot.Page(self.site, 'Disambiguation')
        refs = [
            pywikibot.Page(self.site, title)
            for title in ('Ignored', 'Primary', 'First', 'Second', 'Third')]
        consumed = []

        def references():
            for ref in refs:
                consumed.append(ref)
                yield ref

        with patch('scripts.solve_disambiguation.ignore_title',
                   {'wikipedia': {'de': ['Ignored']}}), \
                patch.object(page, 'getReferences',
                             side_effect=lambda **kwargs: references()), \
                patch('scripts.solve_disambiguation.PrimaryIgnoreManager'
                      '.isIgnored', side_effect=lambda ref: ref == refs[1]):
            gen = iter(ReferringPageGeneratorWithIgnore(page, minimum=2))
            self.assertEqual(next(gen), refs[2])
            self.assertEqual(consumed, refs[:4])
            self.assertEqual(list(gen), refs[3:])

            self.assertEqual(
                list(ReferringPageGeneratorWithIgnore(page, minimum=4)), [])


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
