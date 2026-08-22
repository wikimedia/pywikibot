#!/usr/bin/env python3
#
# (C) Pywikibot team, 2025-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the weblinkchecker script."""
from __future__ import annotations

import unittest
from contextlib import suppress
from unittest.mock import MagicMock, patch

import pywikibot
from scripts import weblinkchecker
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


class TestWeblinkcheckerMain(TestCase):

    """Test :func:`weblinkchecker.main`."""

    net = False

    def test_xml_start(self) -> None:
        """Test XML generator creation with optional start values."""
        generator_factory = MagicMock()
        generator_factory.namespaces = [0]
        generator = object()

        with (
            patch.object(weblinkchecker.pywikibot, 'handle_args',
                         side_effect=lambda args: args),
            patch.object(weblinkchecker.pagegenerators, 'GeneratorFactory',
                         return_value=generator_factory),
            patch.object(weblinkchecker, 'XmlDumpPageGenerator',
                         return_value=generator) as xml_generator,
            patch.object(weblinkchecker, 'suggest_help', return_value=True),
        ):
            for args, start in (
                (('-xml:dump.xml',), None),
                (('-xml:dump.xml', '-xmlstart:Start'), 'Start'),
            ):
                with self.subTest(start=start):
                    xml_generator.reset_mock()
                    weblinkchecker.main(*args)
                    xml_generator.assert_called_once_with(
                        'dump.xml', start, generator_factory.namespaces)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
