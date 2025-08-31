#!/usr/bin/env python3
"""Tests for scripts/delete.py."""
#
# (C) Pywikibot team, 2014-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest
from contextlib import suppress
from unittest.mock import patch

import pywikibot
from scripts import delete
from tests.aspects import DefaultSiteTestCase, ScriptMainTestCase
from tests.utils import empty_sites


class TestDeletionBotWrite(ScriptMainTestCase):

    """Test deletionbot script."""

    family = 'wikipedia'
    code = 'test'

    rights = 'undelete'
    write = True

    def test_delete(self) -> None:
        """Test deletionbot on the test wiki."""
        site = self.get_site()
        cat = pywikibot.Category(site, 'Pywikibot Delete Test')
        delete.main('-cat:Pywikibot_Delete_Test', '-always')
        self.assertIsEmpty(list(cat.members()))
        delete.main('-page:User:Unicodesnowman/DeleteTest1', '-always',
                    '-undelete', '-summary:pywikibot unit tests')
        delete.main('-page:User:Unicodesnowman/DeleteTest2', '-always',
                    '-undelete', '-summary:pywikibot unit tests')
        self.assertLength(list(cat.members()), 2)

    def test_undelete_existing(self) -> None:
        """Test undeleting an existing page."""
        site = self.get_site()
        p1 = pywikibot.Page(site, 'User:Unicodesnowman/ExistingPage')
        if not p1.exists():  # pragma: no cover
            p1.text = 'pywikibot unit test page'
            p1.save('unit test')
        delete.main('-page:User:Unicodesnowman/ExistingPage', '-always',
                    '-undelete', '-summary:pywikibot unit tests')


class TestDeletionBotUser(ScriptMainTestCase):

    """Test deletionbot as a user (no 'deletion' right)."""

    family = 'wikipedia'
    code = 'test'

    write = True

    @classmethod
    def setUpClass(cls) -> None:
        """Set up test class."""
        super().setUpClass()
        cls.page = pywikibot.Page(cls.site, 'User:Unicodesnowman/DeleteMark')
        if not cls.page.exists():
            cls.save_page()  # pragma: no cover

    @classmethod
    def tearDownClass(cls) -> None:
        """Tear down test class."""
        cls.save_page()
        super().tearDownClass()

    @classmethod
    def save_page(cls) -> None:
        """Reset the test page content."""
        cls.page.text = 'Pywikibot deletion test.'
        cls.page.save('Pywikibot unit test')

    def test_delete_mark(self) -> None:
        """Test marking User:Unicodesnowman/DeleteMark for deletion."""
        delete.main('-page:User:Unicodesnowman/DeleteMark', '-always',
                    '-summary:pywikibot unit test. Do NOT actually delete.')
        text = self.page.get(force=True)
        self.assertEqual(
            text,
            '{{delete|1=pywikibot unit test. Do NOT actually delete.}}\n'
            'Pywikibot deletion test.')


class TestDeletionBot(DefaultSiteTestCase):

    """Test deletionbot with patching to make it non-write."""

    net = False

    delete_args = []
    undelete_args = []

    @classmethod
    def setUpClass(cls) -> None:
        """Patch APISite.login."""
        patcher = patch.object(pywikibot.site.APISite, 'login')
        cls.addClassCleanup(patcher.stop)
        patcher.start()
        super().setUpClass()

    def setUp(self) -> None:
        """Set up unit test."""
        super().setUp()

        patches = (
            patch.object(pywikibot.Page, 'delete', delete_dummy),
            patch.object(pywikibot.Page, 'undelete', undelete_dummy),
            patch.object(delete.DeletionRobot, 'skip_page',
                         lambda inst, page: False)
        )
        for p in patches:
            self.addCleanup(p.stop)
            p.start()

    def test_dry(self) -> None:
        """Test dry run of bot."""
        with empty_sites():
            delete.main('-page:Main Page', '-always', '-summary:foo')
            self.assertEqual(self.delete_args,
                             ['[[Main Page]]', 'foo', False, True, True])
        with empty_sites():
            delete.main(
                '-page:FoooOoOooO', '-always', '-summary:foo', '-undelete')
            self.assertEqual(self.undelete_args, ['[[FoooOoOooO]]', 'foo'])


def delete_dummy(page_self, reason, prompt, mark, automatic_quit, *,
                 deletetalk=False) -> int:
    """Dummy delete method."""
    TestDeletionBot.delete_args = [page_self.title(as_link=True), reason,
                                   prompt, mark, automatic_quit]
    return 0


def undelete_dummy(page_self, reason) -> None:
    """Dummy undelete method."""
    TestDeletionBot.undelete_args = [page_self.title(as_link=True), reason]


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
