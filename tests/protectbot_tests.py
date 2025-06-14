#!/usr/bin/env python3
"""Tests for scripts/protect.py."""
#
# (C) Pywikibot team, 2014-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest
from contextlib import suppress

import pywikibot
from scripts import protect
from tests.aspects import ScriptMainTestCase


class TestProtectionBot(ScriptMainTestCase):

    """Test ProtectionBot protect/unprotect capabilities."""

    family = 'wikipedia'
    code = 'test'
    rights = 'protect'
    write = True

    def test_protect(self) -> None:
        """Test ProtectionBot protect/unprotect on the test wiki."""
        site = self.get_site()
        protect.main('-page:User:Sn1per/ProtectTest1', '-always', '-unprotect',
                     '-summary:Pywikibot protect.py unit tests')
        page = pywikibot.Page(site, 'User:Sn1per/ProtectTest1')
        self.assertIsEmpty(list(page.protection()))
        protect.main('-page:User:Sn1per/ProtectTest1', '-always', '-default',
                     '-summary:Pywikibot protect.py unit tests')
        page = pywikibot.Page(site, 'User:Sn1per/ProtectTest1')
        self.assertLength(list(page.protection()), 2)

    def test_summary(self) -> None:
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

        self.maxDiff = None
        comment = rev[0].comment
        self.assertTrue(comment.startswith(
            'Protected "[[User:Sn1per/ProtectTest2]]": Bot: '
            'Protecting all pages from category Pywikibot Protect Test'
        ))
        # the order may change, see T367259
        for ptype in ('Edit', 'Move'):
            self.assertIn(f'[{ptype}=Allow only administrators] (indefinite)',
                          comment)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
