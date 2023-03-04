#!/usr/bin/env python3
"""Tests for scripts/delete.py."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

import pywikibot
from scripts import delete
from tests.aspects import ScriptMainTestCase
from tests.utils import empty_sites


class TestDeletionBotWrite(ScriptMainTestCase):

    """Test deletionbot script."""

    family = 'wikipedia'
    code = 'test'

    rights = 'undelete'
    write = True

    def test_delete(self):
        """Test deletionbot on the test wiki."""
        site = self.get_site()
        cat = pywikibot.Category(site, 'Pywikibot Delete Test')
        delete.main('-cat:Pywikibot_Delete_Test', '-always')
        self.assertIsEmpty(list(cat.members()))
        delete.main('-page:User:Unicodesnowman/DeleteTest1', '-always',
                    '-undelete', '-summary=pywikibot unit tests')
        delete.main('-page:User:Unicodesnowman/DeleteTest2', '-always',
                    '-undelete', '-summary=pywikibot unit tests')
        self.assertLength(list(cat.members()), 2)

    def test_undelete_existing(self):
        """Test undeleting an existing page."""
        site = self.get_site()
        p1 = pywikibot.Page(site, 'User:Unicodesnowman/ExistingPage')
        if not p1.exists():
            p1.text = 'pywikibot unit test page'
            p1.save('unit test', botflag=True)
        delete.main('-page:User:Unicodesnowman/ExistingPage', '-always',
                    '-undelete', '-summary=pywikibot unit tests')


class TestDeletionBotUser(ScriptMainTestCase):

    """Test deletionbot as a user (no 'deletion' right)."""

    family = 'wikipedia'
    code = 'test'

    write = True

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        super().setUpClass()
        cls.page = pywikibot.Page(cls.site, 'User:Unicodesnowman/DeleteMark')
        if not cls.page.exists():
            cls.save_page()  # pragma: no cover

    @classmethod
    def tearDownClass(cls):
        """Tear down test class."""
        cls.save_page()
        super().tearDownClass()

    @classmethod
    def save_page(cls):
        """Reset the test page content."""
        cls.page.text = 'Pywikibot deletion test.'
        cls.page.save('Pywikibot unit test', botflag=True)

    def test_delete_mark(self):
        """Test marking User:Unicodesnowman/DeleteMark for deletion."""
        delete.main('-page:User:Unicodesnowman/DeleteMark', '-always',
                    '-summary:pywikibot unit test. Do NOT actually delete.')
        text = self.page.get(force=True)
        self.assertEqual(
            text,
            '{{delete|1=pywikibot unit test. Do NOT actually delete.}}\n'
            'Pywikibot deletion test.')


class TestDeletionBot(ScriptMainTestCase):

    """Test deletionbot with patching to make it non-write."""

    family = 'wikipedia'
    code = 'test'

    cached = True
    login = True

    delete_args = []
    undelete_args = []

    def setUp(self):
        """Set up unit test."""
        self._original_delete = pywikibot.Page.delete
        self._original_undelete = pywikibot.Page.undelete
        pywikibot.Page.delete = delete_dummy
        pywikibot.Page.undelete = undelete_dummy
        super().setUp()

    def tearDown(self):
        """Tear down unit test."""
        pywikibot.Page.delete = self._original_delete
        pywikibot.Page.undelete = self._original_undelete
        super().tearDown()

    def test_dry(self):
        """Test dry run of bot."""
        with empty_sites():
            delete.main('-page:Main Page', '-always', '-summary:foo')
            self.assertEqual(self.delete_args,
                             ['[[Main Page]]', 'foo', False, True, True])
        with empty_sites():
            delete.main(
                '-page:FoooOoOooO', '-always', '-summary:foo', '-undelete')
            self.assertEqual(self.undelete_args, ['[[FoooOoOooO]]', 'foo'])


def delete_dummy(self, reason, prompt, mark, automatic_quit):
    """Dummy delete method."""
    TestDeletionBot.delete_args = [self.title(as_link=True), reason, prompt,
                                   mark, automatic_quit]
    return 0


def undelete_dummy(self, reason):
    """Dummy undelete method."""
    TestDeletionBot.undelete_args = [self.title(as_link=True), reason]


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
