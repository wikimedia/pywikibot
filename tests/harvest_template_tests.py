#!/usr/bin/env python3
"""Tests for scripts/harvest_template.py."""
#
# (C) Pywikibot team, 2022-2023
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot import ItemPage, WbTime
from scripts.harvest_template import HarvestRobot
from tests.aspects import ScriptMainTestCase


class TestHarvestRobot(ScriptMainTestCase):

    """Test HarvestRobot."""

    family = 'wikipedia'
    code = 'cs'

    def test_template_link_target(self):
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

    def test_handle_time(self):
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


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
