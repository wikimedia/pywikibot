# -*- coding: utf-8  -*-
"""Tests for scripts/delete.py."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import pywikibot
import pywikibot.page

from scripts import delete

from tests.aspects import unittest, ScriptMainTestCase


class TestDeletionBotWrite(ScriptMainTestCase):

    """Test deletionbot script."""

    family = 'test'
    code = 'test'

    sysop = True
    write = True

    def test_delete(self):
        """Test deletionbot on the test wiki."""
        site = self.get_site()
        cat = pywikibot.Category(site, 'Pywikibot Delete Test')
        delete.main('-cat:Pywikibot_Delete_Test', '-always')
        self.assertEqual(len(list(cat.members())), 0)
        delete.main('-page:User:Unicodesnowman/DeleteTest1', '-always',
                    '-undelete', '-summary=pywikibot unit tests')
        delete.main('-page:User:Unicodesnowman/DeleteTest2', '-always',
                    '-undelete', '-summary=pywikibot unit tests')
        self.assertEqual(len(list(cat.members())), 2)

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

    """Test deletionbot as a user (not sysop)."""

    family = 'test'
    code = 'test'

    user = True
    write = True

    def test_delete_mark(self):
        site = self.get_site()
        if site.username(sysop=True):
            raise unittest.SkipTest('can\'t test mark with sysop account')

        p1 = pywikibot.Page(site, 'User:Unicodesnowman/DeleteMark')
        if not p1.exists():
            p1.text = 'foo'
            p1.save('unit test', botflag=True)
        delete.main('-page:User:Unicodesnowman/DeleteMark', '-always',
                    '-summary=pywikibot unit test. Do NOT actually delete.')
        self.assertEqual(p1.get(force=True), '{{delete|1=pywikibot unit test. '
                         'Do NOT actually delete.}}\nfoo')
        p1.text = 'foo'
        p1.save('unit test', botflag=True)


class TestDeletionBot(ScriptMainTestCase):

    """Test deletionbot with patching to make it non-write."""

    family = 'test'
    code = 'test'

    cached = True

    delete_args = []
    undelete_args = []

    def setUp(self):
        self._original_delete = pywikibot.Page.delete
        self._original_undelete = pywikibot.Page.undelete
        pywikibot.Page.delete = delete_dummy
        pywikibot.Page.undelete = undelete_dummy
        super(TestDeletionBot, self).setUp()

    def tearDown(self):
        pywikibot.Page.delete = self._original_delete
        pywikibot.Page.undelete = self._original_undelete
        super(TestDeletionBot, self).tearDown()

    def test_dry(self):
        delete.main('-page:Main Page', '-always', '-summary:foo')
        self.assertEqual(self.delete_args, ['[[Main Page]]', 'foo', False, True])
        delete.main('-page:FoooOoOooO', '-always', '-summary:foo', '-undelete')
        self.assertEqual(self.undelete_args, ['[[FoooOoOooO]]', 'foo'])


def delete_dummy(self, reason, prompt, mark):
    TestDeletionBot.delete_args = [self.title(asLink=True), reason, prompt, mark]


def undelete_dummy(self, reason):
    TestDeletionBot.undelete_args = [self.title(asLink=True), reason]


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
