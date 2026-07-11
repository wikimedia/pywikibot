#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for scripts/interwiki.py."""
from __future__ import annotations

import unittest
from contextlib import suppress

import pywikibot
from scripts import interwiki
from tests.aspects import DrySite, PatchingTestCase


class TestIwConfig(PatchingTestCase):

    """Tests for InterwikiBotConfig."""

    family = 'wikipedia'
    code = 'test'
    dry = True

    @PatchingTestCase.patched(pywikibot, 'Site')
    def Site(self, *args, **kwargs):  # noqa: N802
        """Own DrySite creator."""
        code = self.site.code
        fam = self.site.family
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {})
        site = DrySite(code, fam, None)
        return site

    def test_hint_options(self) -> None:
        """Test -hint and -hintfile options."""
        iwc = interwiki.InterwikiBotConfig()
        self.assertIsInstance(iwc.hints, list)
        self.assertIsEmpty(iwc.hints)
        iwc.readOptions('-hintfile:tests/data/pagelist-brackets.txt')
        self.assertLength(iwc.hints, 5)
        for option in '-hint:foo -hint:bar -hint:baz'.split():
            iwc.readOptions(option)
        self.assertLength(iwc.hints, 8)

    def test_ignore_option(self) -> None:
        """Test -ignore and -ignorefile options."""
        iwc = interwiki.InterwikiBotConfig()
        self.assertIsInstance(iwc.ignore, list)
        self.assertIsEmpty(iwc.ignore)
        iwc.readOptions('-ignorefile:tests/data/pagelist-lines.txt')
        self.assertLength(iwc.ignore, 5)
        iwc.readOptions('-ignore:Foo,Bar,Baz')
        self.assertLength(iwc.ignore, 8)

    def test_skipfile_option(self) -> None:
        """Test -skipfile options."""
        iwc = interwiki.InterwikiBotConfig()
        self.assertIsInstance(iwc.skip, set)
        self.assertIsEmpty(iwc.skip)
        iwc.readOptions('-skipfile:tests/data/pagelist-lines.txt')
        self.assertLength(iwc.skip, 5)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
