#!/usr/bin/env python3
#
# (C) Pywikibot team, 2015-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the patrol script."""
from __future__ import annotations

import unittest
from contextlib import suppress
from unittest.mock import patch

from scripts.patrol import PatrolBot
from tests.aspects import DefaultSiteTestCase


DUMMY_PAGE_TUPLES = """
This is some text above the entries:

== Header ==
* [[User:Test 1]]: [[Page 1]], [[Page 2]]
* [[User:Test_2]]: [[Page 2]], [[Page 4]], [[Page 6]]

== Others ==
* [[User:Prefixed]]: [[Special:PrefixIndex/Page 1]],
                     [[Special:PREFIXINDEX/Page 2]]

== More test 1 ==
* [[User:Test_1]]: [[Page 3]]
"""


class TestPatrolBot(DefaultSiteTestCase):

    """Test the PatrolBot class."""

    dry = True

    def setUp(self) -> None:
        """Create a bot dummy instance."""
        super().setUp()
        self.bot = PatrolBot(self.site)

    def test_parse_page_tuples(self) -> None:
        """Test parsing the page tuples from a dummy text."""
        tuples = self.bot.parse_page_tuples(DUMMY_PAGE_TUPLES)
        for gen_user in (1, 2):
            user = f'Test {gen_user}'
            self.assertIn(user, tuples)
            self.assertEqual(tuples[user], {f'Page {i * gen_user}'
                                            for i in range(1, 4)})
        self.assertIn('Prefixed', tuples)
        self.assertEqual(tuples['Prefixed'], {'Page 1', 'Page 2'})
        self.assertEqual(self.bot.parse_page_tuples('[[link]]'), {})

    def test_in_list(self) -> None:
        """Test the method which returns whether a page is in the set."""
        # Return True if there is an exact match
        self.assertTrue(self.bot.in_list({'Foo', 'Foobar'}, 'Foo'))
        self.assertTrue(self.bot.in_list({'Foo', 'Foobar'}, 'Foobar'))
        self.assertFalse(self.bot.in_list({'Foo', 'Foobar'}, 'Bar'))

        # Return True if an entry starts with the title if there is no
        # exact match
        self.assertTrue(self.bot.in_list({'Foo', 'Foobar'}, 'Foob'))
        self.assertTrue(self.bot.in_list({'Foo', 'Foobar'}, 'Foobarz'))
        self.assertTrue(self.bot.in_list({'Foo', 'Foobar', 'Bar'}, 'Barz'))
        self.assertFalse(self.bot.in_list({'Foobar', 'Bar'}, 'Foo'))

        # '' returns True if there is no exact match
        self.assertTrue(self.bot.in_list({''}, 'Foo'))
        self.assertTrue(self.bot.in_list({'', 'Foobar'}, 'Foo'))
        self.assertTrue(self.bot.in_list({'', 'Foo'}, 'Foo'))

    def _treat_page(self, patrol_result):
        """Treat a whitelisted page and return the info mock."""
        page = {
            'user': 'Test user',
            'rcid': 1,
            'title': 'Page 1',
            'ns': 0,
        }
        self.bot.last_rcid = 1
        self.bot.whitelist = {'Test user': {'Page 1'}}

        with patch.object(
            self.bot.site, 'patrol', return_value=iter(patrol_result)
        ) as patrol, patch('pywikibot.info') as info:
            self.bot.treat(page)

        patrol.assert_called_once_with(1)
        return info

    def test_treat_reports_successful_patrol(self) -> None:
        """Test that a successful patrol is reported."""
        info = self._treat_page([{'rcid': 1}])
        info.assert_called_once_with(
            'Patrolled Page 1 (rcid 1) by user Test user')

    def test_treat_does_not_report_disabled_patrol(self) -> None:
        """Test that a disabled patrol is not reported as successful."""
        info = self._treat_page([])
        info.assert_not_called()


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
