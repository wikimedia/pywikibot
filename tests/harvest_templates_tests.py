#!/usr/bin/python3
"""Tests for scripts/harvest_template.py."""
#
# (C) Pywikibot team, 2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot import ItemPage
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
                target = HarvestRobot.template_link_target(dummy_item, link)
                self.assertIsInstance(target, ItemPage)
                self.assertEqual(target.title(), item)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
