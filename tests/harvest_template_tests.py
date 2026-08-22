#!/usr/bin/env python3
#
# (C) Pywikibot team, 2022-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for scripts/harvest_template.py."""
from __future__ import annotations

import unittest
from contextlib import suppress
from unittest.mock import call, patch

from pywikibot import ItemPage, WbTime, pagegenerators
from scripts import harvest_template
from scripts.harvest_template import HarvestRobot
from tests.aspects import ScriptMainTestCase, TestCase


class TestHarvestMain(TestCase):

    """Test :func:`harvest_template.main`."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def test_default_generator_with_filter(self) -> None:
        """Test that filters do not suppress the default generator."""
        factory = pagegenerators.GeneratorFactory(site=self.site)
        with (
            patch.object(harvest_template.pywikibot, 'handle_args',
                         side_effect=lambda args: args),
            patch.object(harvest_template.pg, 'GeneratorFactory',
                         return_value=factory),
            patch.object(factory, 'handle_arg',
                         wraps=factory.handle_arg) as handle_arg,
            patch.object(harvest_template, 'HarvestRobot') as bot,
        ):
            harvest_template.main(
                '-template:Foo', '-namespace:0', 'field', 'P1')

        self.assertIn(call('-transcludes:Foo'), handle_arg.call_args_list)
        bot.return_value.run.assert_called_once_with()

    def test_explicit_generator_suppresses_default(self) -> None:
        """Test that a source option suppresses the default generator."""
        factory = pagegenerators.GeneratorFactory(site=self.site)
        with (
            patch.object(harvest_template.pywikibot, 'handle_args',
                         side_effect=lambda args: args),
            patch.object(harvest_template.pg, 'GeneratorFactory',
                         return_value=factory),
            patch.object(factory, 'handle_arg',
                         wraps=factory.handle_arg) as handle_arg,
            patch.object(harvest_template, 'HarvestRobot') as bot,
        ):
            harvest_template.main(
                '-template:Foo', '-page:Bar', 'field', 'P1')

        self.assertNotIn(call('-transcludes:Foo'), handle_arg.call_args_list)
        bot.return_value.run.assert_called_once_with()


class TestHarvestRobot(ScriptMainTestCase):

    """Test HarvestRobot."""

    family = 'wikipedia'
    code = 'cs'

    def test_template_link_target(self) -> None:
        """Test template_link_target static method."""
        tests = [
            ('Pes', 'Q144'),
            ('Imaginární číslo', 'Q9165172'),
            ('Sequana', 'Q472766'),
        ]
        for link, item in tests:
            with self.subTest(link=link, item=item):
                dummy_item = ItemPage(self.site.data_repository(), 'Q1')
                target = HarvestRobot.template_link_target(
                    dummy_item, self.site, link)
                self.assertIsInstance(target, ItemPage)
                self.assertEqual(target.title(), item)

    def test_handle_time(self) -> None:
        """Test handle_time method."""
        bot = HarvestRobot('Foo', {}, site=self.site)

        day = WbTime(2022, 7, 18, precision=11, site=bot.repo)
        tests = [
            ('Foo', None),
            ('2022', WbTime(2022, 0, 0, precision=9, site=bot.repo)),
            ('2022-07-18', day),
            ('18. červenec 2022', day),
            ('18. července [[2021|2022]]', None),
            ('[[18. červenec]] 2022', day),
            ('[[18. červenec|18. července]] [[2022]]', day),
            ('[[17. červenec|18. července]] [[2022]]', None),
            ('44 př.&nbsp;n.&nbsp;l.',
             WbTime(-44, 0, 0, precision=9,
                    calendarmodel='http://www.wikidata.org/entity/Q1985786',
                    site=bot.repo)),
        ]
        for text, time in tests:
            with self.subTest(text=text, time=time):
                gen = bot.handle_time(text, self.site)
                out = next(gen, None)
                self.assertEqual(time, out)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
