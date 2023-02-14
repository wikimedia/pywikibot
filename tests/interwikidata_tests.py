#!/usr/bin/env python3
"""Tests for scripts/interwikidata.py."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

import pywikibot
from pywikibot import Link
from scripts import interwikidata
from tests.aspects import SiteAttributeTestCase
from tests.utils import empty_sites


class DummyBot(interwikidata.IWBot):

    """A dummy bot to prevent editing in production wikis."""

    def put_current(self):
        """Prevent editing."""
        return False

    def create_item(self):
        """Prevent creating items."""
        return False

    def try_to_add(self):
        """Prevent adding sitelinks to items."""
        return None


class TestInterwikidataBot(SiteAttributeTestCase):

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

    def test_main(self):
        """Test main function interwikidata.py."""
        # The main function should return False when no generator is defined.
        with empty_sites():
            self.assertFalse(interwikidata.main())

    def test_iw_bot(self):
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

    def test_without_repo(self):
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


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
