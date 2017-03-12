# -*- coding: utf-8 -*-
"""Tests for scripts/interwikidata.py."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals, absolute_import

__version__ = '$Id$'

import pywikibot

from pywikibot import Link

from scripts import interwikidata

from tests.aspects import unittest, SiteAttributeTestCase


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
            'family': 'wiktionary',
            'code': 'en',
        },
    }

    def test_main(self):
        """Test main function interwikidata.py."""
        # The main function should return False when no generator is defined.
        self.assertFalse(interwikidata.main())

    def test_iw_bot(self):
        """Test IWBot class."""
        page = pywikibot.Page(self.en, 'User:Ladsgroup')
        text = page.get()

        # The page looks as excpected.
        self.assertEqual(len(page.langlinks()), 1)
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
        self.assertRaises(ValueError, DummyBot, generator=[wt_page], site=self.wt)

        fa_wiktionary = pywikibot.Site('fa', 'wiktionary')
        self.assertRaisesRegex(
            ValueError,
            r'wiktionary:fa does not have a data repository, '
            r'use interwiki\.py instead.',
            interwikidata.IWBot,
            generator=[pywikibot.Page(fa_wiktionary, 'User:Dalba')],
            site=fa_wiktionary,
        )


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
