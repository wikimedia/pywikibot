#!/usr/bin/env python3
"""Tests for scripts/interwikidata.py."""
#
# (C) Pywikibot team, 2015-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest
from contextlib import suppress
from typing import Any

import pywikibot
from pywikibot import Link
from scripts import interwikidata
from tests.aspects import AlteredDefaultSiteTestCase, SiteAttributeTestCase
from tests.utils import empty_sites


class DummyBot(interwikidata.IWBot):

    """A dummy bot to prevent editing in production wikis."""

    def put_current(self, *args: Any, **kwargs: Any) -> bool:
        """Prevent editing."""
        raise NotImplementedError

    def create_item(self) -> pywikibot.ItemPage:
        """Prevent creating items."""
        raise NotImplementedError

    def try_to_add(self) -> None:
        """Prevent adding sitelinks to items."""
        return


class TestInterwikidataBot(AlteredDefaultSiteTestCase, SiteAttributeTestCase):

    """Test Interwikidata."""

    sites = {
        'en': {
            'family': 'wikipedia',
            'code': 'en',
        },
        'fa': {
            'family': 'wikipedia',
            'code': 'fa',
        },
        'wt': {
            'family': 'wikitech',
            'code': 'en',
        },
    }

    def test_main(self, key) -> None:
        """Test main function interwikidata.py."""
        site = self.get_site(key)
        pywikibot.config.family = site.family
        pywikibot.config.mylang = site.code

        if site.has_data_repository:
            with empty_sites():
                # The main function return None.
                self.assertIsNone(interwikidata.main())
        else:
            with empty_sites(), self.assertRaisesRegex(
                ValueError,
                    r'[a-z}+:[a-z_-]+ does not have a data repository, use '
                    r'interwiki\.py instead\.'):
                interwikidata.main()

    def test_iw_bot(self) -> None:
        """Test IWBot class."""
        page = pywikibot.Page(self.en, 'User:Ladsgroup')
        text = page.get()

        # The page looks as expected.
        self.assertLength(page.langlinks(), 1)
        iw_link = page.langlinks()[0]
        self.assertIsInstance(iw_link, Link)
        self.assertEqual(iw_link.canonical_title(), 'کاربر:Ladsgroup')
        self.assertEqual(iw_link.site, self.fa)

        repo = self.en.data_repository()
        bot = DummyBot(generator=[page], site=self.en, ignore_ns=True)
        bot.run()

        # Repo and site should not change during a run.
        self.assertEqual(bot.repo, repo)
        self.assertEqual(bot.site, self.en)

        # Test iwlangs method.
        self.assertIn(self.fa, bot.iwlangs)
        self.assertEqual(Link.fromPage(bot.iwlangs[self.fa]), iw_link)

        page2 = pywikibot.Page(self.en, 'User:Ladsgroup')
        self.assertEqual(page2.get(), text)

        self.assertFalse(bot.handle_complicated())

    def test_without_repo(self) -> None:
        """Test throwing error when site does not have a data repo."""
        wt_page = pywikibot.Page(self.wt, 'User:Ladsgroup')
        with self.assertRaises(ValueError):
            DummyBot(generator=[wt_page],
                     site=self.wt)

        with self.assertRaisesRegex(
                ValueError, 'wikitech:en does not have a data repository.'):
            interwikidata.IWBot(
                generator=[pywikibot.Page(self.wt, 'User:Dalba')],
                site=self.wt)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
