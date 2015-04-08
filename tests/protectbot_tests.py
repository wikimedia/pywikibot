# -*- coding: utf-8  -*-
"""Tests for scripts/protect.py."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import pywikibot
import pywikibot.page

from scripts import protect

from tests.aspects import unittest, ScriptMainTestCase


class TestProtectionBot(ScriptMainTestCase):

    """Test ProtectionBot protect/unprotect capabilities."""

    family = 'test'
    code = 'test'

    sysop = True
    write = True

    def test_protect(self):
        """Test ProtectionBot protect/unprotect on the test wiki."""
        site = self.get_site()
        protect.main('-page:User:Sn1per/ProtectTest1', '-always',
                     '-unprotect', '-summary=Pywikibot protect.py unit tests')
        page = pywikibot.Page(site, 'User:Sn1per/ProtectTest1')
        self.assertEqual(len(list(page.protection())), 0)
        protect.main('-page:User:Sn1per/ProtectTest1', '-always',
                     '-default', '-summary=Pywikibot protect.py unit tests')
        page = pywikibot.Page(site, 'User:Sn1per/ProtectTest1')
        self.assertEqual(len(list(page.protection())), 2)

    def test_summary(self):
        """Test automatic (un)protection summary on the test wiki."""
        site = self.get_site()
        protect.main('-cat:Pywikibot Protect Test', '-always',
                     '-default')
        protect.main('-cat:Pywikibot Protect Test', '-always',
                     '-unprotect')
        protect.main('-cat:Pywikibot Protect Test', '-always',
                     '-default')
        page = pywikibot.Page(site, 'User:Sn1per/ProtectTest2')
        rev = list(page.revisions())
        self.assertEqual(
            rev[1].comment,
            'Removed protection from "[[User:Sn1per/ProtectTest2]]": Bot: '
            'Unprotecting all pages from category Pywikibot Protect Test')
        self.assertEqual(
            rev[0].comment,
            'Protected "[[User:Sn1per/ProtectTest2]]": Bot: '
            'Protecting all pages from category Pywikibot Protect Test '
            '([Edit=Allow only administrators] (indefinite) [Move=Allow only '
            'administrators] (indefinite))')

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
