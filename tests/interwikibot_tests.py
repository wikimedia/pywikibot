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
from unittest.mock import Mock

import pywikibot
from scripts import interwiki
from tests.aspects import DrySite, PatchingTestCase, TestCase


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


class TestReplaceLinks(TestCase):

    """Tests for replacing interwiki links."""

    dry = True
    sites = {
        'local': {'family': 'wikipedia', 'code': 'en'},
        'foreign': {'family': 'commons', 'code': 'commons'},
    }

    def test_foreign_family_link(self) -> None:
        """Test removing a link to a non-forwarded family."""
        local_site = self.get_site('local')
        page = pywikibot.Page(local_site, 'Test page')
        page._langlinks = set()
        foreign_page = pywikibot.Page(
            self.get_site('foreign'), 'File:Test.jpg')
        pages = {page.site: page, foreign_page.site: foreign_page}

        subject = interwiki.Subject.__new__(interwiki.Subject)
        subject.conf = interwiki.InterwikiBotConfig()
        subject.conf.quiet = True
        subject._fetch_text = Mock(return_value='Test page content')

        self.assertFalse(subject.replaceLinks(page, pages))
        self.assertEqual(pages,
                         {page.site: page, foreign_page.site: foreign_page})


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
