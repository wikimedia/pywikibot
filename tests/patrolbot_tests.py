# -*- coding: utf-8 -*-
"""Tests for the patrol script."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#
try:
    from scripts import patrol
except ImportError:
    patrol = None  # if mwparserfromhell is not installed

from tests.aspects import require_modules, unittest, DefaultDrySiteTestCase

DUMMY_PAGE_TUPLES = """
This is some text above the entries:

== Header ==
* [[User:Test 1]]: [[Page 1]], [[Page 2]]
* [[User:Test_2]]: [[Page 2]], [[Page 4]], [[Page 6]]

== Others ==
* [[User:Prefixed]]: [[Special:PrefixIndex/Page 1]], [[Special:PREFIXINDEX/Page 2]]

== More test 1 ==
* [[User:Test_1]]: [[Page 3]]
"""


@require_modules('mwparserfromhell')
class TestPatrolBot(DefaultDrySiteTestCase):

    """Test the PatrolBot class."""

    def setUp(self):
        """Create a bot dummy instance."""
        super(TestPatrolBot, self).setUp()
        self.bot = patrol.PatrolBot(self.site)

    def test_parse_page_tuples(self):
        """Test parsing the page tuples from a dummy text."""
        tuples = self.bot.parse_page_tuples(DUMMY_PAGE_TUPLES)
        for gen_user in (1, 2):
            user = 'Test {0}'.format(gen_user)
            self.assertIn(user, tuples)
            self.assertEqual(tuples[user], ['Page {0}'.format(i * gen_user)
                                            for i in range(1, 4)])
        self.assertIn('Prefixed', tuples)
        self.assertEqual(tuples['Prefixed'], ['Page 1', 'Page 2'])
        self.assertEqual(self.bot.parse_page_tuples('[[link]]'), {})

    def test_in_list(self):
        """Test the method which returns whether a page is in the list."""
        # Return the title if there is an exact match
        self.assertEqual(self.bot.in_list(['Foo', 'Foobar'], 'Foo'), 'Foo')
        self.assertEqual(self.bot.in_list(['Foo', 'Foobar'], 'Foobar'), 'Foobar')

        # Return the first entry which starts with the title if there is no
        # exact match
        self.assertEqual(self.bot.in_list(['Foo', 'Foobar'], 'Foob'), 'Foo')
        self.assertEqual(self.bot.in_list(['Foo', 'Foobar'], 'Foobarz'), 'Foo')
        self.assertEqual(self.bot.in_list(['Foo', 'Foobar', 'Bar'], 'Barz'), 'Bar')

        # '' returns .* if there is no exact match
        self.assertEqual(self.bot.in_list([''], 'Foo'), '.*')
        self.assertEqual(self.bot.in_list(['', 'Foobar'], 'Foo'), '.*')
        self.assertEqual(self.bot.in_list(['', 'Foo'], 'Foo'), 'Foo')


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
