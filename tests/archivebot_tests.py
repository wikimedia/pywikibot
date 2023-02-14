#!/usr/bin/env python3
"""Tests for archivebot scripts."""
#
# (C) Pywikibot team, 2014-2023
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress
from datetime import datetime

import pywikibot
from pywikibot.exceptions import Error
from pywikibot.textlib import TimeStripper
from scripts import archivebot
from tests.aspects import TestCase


THREADS = {
    'als': 4, 'ar': 1, 'bar': 0, 'bg': 0, 'bjn': 1, 'bs': 0, 'ca': 5, 'ckb': 2,
    'cs': 0, 'de': 1, 'en': 25, 'eo': 2, 'es': 13, 'fa': 2, 'fr': 25, 'frr': 2,
    'hi': 0, 'hr': 2, 'hu': 5, 'id': 3, 'it': 25, 'ja': 4, 'la': 0, 'lt': 1,
    'nl': 9, 'nn': 0, 'no': 0, 'pdc': 25, 'pfl': 3, 'pl': 8, 'pt': 0, 'ro': 1,
    'ru': 20, 'scn': 2, 'simple': 1, 'sr': 0, 'sv': 5, 'th': 1, 'tr': 7,
    'ug': 0, 'uk': 1, 'uz': 1, 'vi': 1, 'zh': 4, 'zh-yue': 2,
}

THREADS_WITH_UPDATED_FORMAT = {
    'eo': 1, 'pdc': 1,
}


class TestArchiveBotFunctionsWithSites(TestCase):

    """Test functions dependent to sites in archivebot."""

    sites = {
        'enwiki': {
            'family': 'wikipedia',
            'code': 'en',
        },
        'frwikt': {
            'family': 'wiktionary',
            'code': 'fr',
        },
        'jawiki': {
            'family': 'wikipedia',
            'code': 'ja',
        }
    }

    def test_str2localized_duration_English(self):
        """Test English localizations of duration."""
        site = self.get_site('enwiki')
        self.assertEqual(
            archivebot.str2localized_duration(site, '0s'), '0 seconds')
        self.assertEqual(
            archivebot.str2localized_duration(site, '1d'), '1 day')
        self.assertEqual(
            archivebot.str2localized_duration(site, '10h'), '10 hours')

    def test_str2localized_duration_French(self):
        """Test French localizations of duration."""
        site = self.get_site('frwikt')
        self.assertEqual(
            archivebot.str2localized_duration(site, '10d'), '10 jours')
        self.assertEqual(archivebot.str2localized_duration(site, '1y'), '1 an')

    def test_str2localized_duration_Japanese(self):
        """Test Japanese localizations of duration."""
        site = self.get_site('jawiki')
        self.assertEqual(
            archivebot.str2localized_duration(site, '4000s'), '4000 秒')


class TestArchiveBotFunctions(TestCase):

    """Test functions in archivebot."""

    net = False

    def test_str2size(self):
        """Test for parsing the shorthand notation of sizes."""
        self.assertEqual(archivebot.str2size('0'), (0, 'B'))
        self.assertEqual(archivebot.str2size('3000'), (3000, 'B'))
        self.assertEqual(archivebot.str2size('4 K'), (4096, 'B'))
        self.assertEqual(archivebot.str2size('1 M'), (1_048_576, 'B'))
        self.assertEqual(archivebot.str2size('2T'), (2, 'T'))
        self.assertEqual(archivebot.str2size('2 000'), (2000, 'B'))
        self.assertEqual(archivebot.str2size('2 000B'), (2000, 'B'))
        self.assertEqual(archivebot.str2size('2 000 B'), (2000, 'B'))

    def test_str2size_failures(self):
        """Test for rejecting of invalid shorthand notation of sizes."""
        with self.assertRaises(archivebot.MalformedConfigError):
            archivebot.str2size('4 KK')
        with self.assertRaises(archivebot.MalformedConfigError):
            archivebot.str2size('K4')
        with self.assertRaises(archivebot.MalformedConfigError):
            archivebot.str2size('4X')
        with self.assertRaises(archivebot.MalformedConfigError):
            archivebot.str2size('1 234 56')
        with self.assertRaises(archivebot.MalformedConfigError):
            archivebot.str2size('1234 567')


class TestArchiveBot(TestCase):

    """Test archivebot script on 40+ Wikipedia sites."""

    family = 'wikipedia'
    sites = {code: {'family': 'wikipedia', 'code': code} for code in THREADS}

    cached = True
    expected_failures = ['ar', 'scn', 'th']

    def test_archivebot(self, code=None):
        """Test archivebot for one site."""
        site = self.get_site(code)
        page = pywikibot.Page(site, 'user talk:xqt')
        talk = archivebot.DiscussionPage(page, None)
        self.assertIsInstance(talk.archives, dict)
        self.assertIsInstance(talk.archived_threads, int)
        self.assertTrue(talk.archiver is None)
        self.assertIsInstance(talk.header, str)
        self.assertIsInstance(talk.timestripper, TimeStripper)

        self.assertIsInstance(talk.threads, list)
        self.assertGreaterEqual(
            len(talk.threads), THREADS[code],
            '{} Threads found on {},\n{} or more expected'
            .format(len(talk.threads), talk, THREADS[code]))

        for thread in talk.threads:
            with self.subTest(thread=thread.title,
                              content=thread.content[-72:]):
                self.assertIsInstance(thread, archivebot.DiscussionThread)
                self.assertIsInstance(thread.title, str)
                self.assertIsInstance(thread.ts, TimeStripper)
                self.assertEqual(thread.ts, talk.timestripper)
                self.assertIsInstance(thread.code, str)
                self.assertEqual(thread.code, talk.timestripper.site.code)
                self.assertIsInstance(thread.content, str)
                self.assertIsInstance(thread.timestamp, datetime)

    # FIXME: see TestArchiveBotAfterDateUpdate()
    # 'ar': Uses Arabic acronym for TZ
    # 'eo': changed month name setting in wiki from Sep to sep
    #       Localisation updates from https://translatewiki.net.
    #       Change-Id: I3d9b14ae3a5d77fea9694ef113b0180e5677c39e
    #       ref: mediawiki languages/i18n/eo.json
    #       for new entries it should work
    # 'pdc': changed month name setting in wiki over time (?)
    #   in old posts in talk page, February is "Feb.", site message gives
    #   <message name="feb" xml:space="preserve">Han.</message>.
    #   for new entries it should work
    # 'th': year is 2552 while regex assumes 19..|20.., might be fixed


class TestArchiveBotAfterDateUpdate(TestCase):

    """
    Test archivebot script on failures on Wikipedia sites.

    If failure is due to updated date format on wiki, test pages with
    new format only.
    """

    family = 'wikipedia'
    sites = {code: {'family': 'wikipedia', 'code': code}
             for code in THREADS_WITH_UPDATED_FORMAT}

    cached = True

    def test_archivebot(self, code=None):
        """Test archivebot for one site."""
        site = self.get_site(code)
        page = pywikibot.Page(site, 'user talk:mpaa')
        talk = archivebot.DiscussionPage(page, None)
        self.assertIsInstance(talk.archives, dict)
        self.assertIsInstance(talk.archived_threads, int)
        self.assertTrue(talk.archiver is None)
        self.assertIsInstance(talk.header, str)
        self.assertIsInstance(talk.timestripper, TimeStripper)

        self.assertIsInstance(talk.threads, list)
        self.assertGreaterEqual(
            len(talk.threads), THREADS_WITH_UPDATED_FORMAT[code],
            '{} Threads found on {},\n{} or more expected'
            .format(len(talk.threads), talk,
                    THREADS_WITH_UPDATED_FORMAT[code]))

        for thread in talk.threads:
            with self.subTest(thread=thread.title,
                              content=thread.content[-72:]):
                self.assertIsInstance(thread, archivebot.DiscussionThread)
                self.assertIsInstance(thread.title, str)
                self.assertIsInstance(thread.ts, TimeStripper)
                self.assertEqual(thread.ts, talk.timestripper)
                self.assertIsInstance(thread.code, str)
                self.assertEqual(thread.code, talk.timestripper.site.code)
                self.assertIsInstance(thread.content, str)
                self.assertIsInstance(thread.timestamp, datetime)


class TestDiscussionPageObject(TestCase):

    """Test DiscussionPage object."""

    cached = True
    family = 'wikipedia'
    code = 'test'

    def load_page(self, title: str):
        """Load the given page."""
        page = pywikibot.Page(self.site, title)
        tmpl = pywikibot.Page(self.site, 'User:MiszaBot/config')
        archiver = archivebot.PageArchiver(page=page, template=tmpl, salt='')
        page = archivebot.DiscussionPage(page, archiver)
        page.load_page()
        self.page = page

    def testTwoThreadsWithCommentedOutThread(self):
        """Test recognizing two threads and ignoring a commented out thread.

        Talk:For-pywikibot-archivebot must have::

         {{User:MiszaBot/config
         |archive = Talk:Main_Page/archive
         |algo = old(30d)
         }}
         <!-- normal comments -->
         == A ==
         foo bar
         <!--
         == Z ==
         foo bar bar
         -->
         == B ==
         foo bar bar bar
        """
        self.load_page('Talk:For-pywikibot-archivebot')
        self.assertEqual([x.title for x in self.page.threads], ['A', 'B'])

    def testThreadsWithSubsections(self):
        """Test recognizing threads with subsections.

        Talk:For-pywikibot-archivebot/subsections must have::

         {{User:MiszaBot/config
         |archive = Talk:Main_Page/archive
         |algo = old(30d)
         }}
         = Front matter =
         placeholder
         == A ==
         foo bar
         === A1 ===
         foo bar bar
         ==== A11 ====
         foo
         == B ==
         foo bar bar bar
        """
        self.load_page('Talk:For-pywikibot-archivebot/testcase2')
        self.assertEqual([x.title for x in self.page.threads], ['A', 'B'])

    def test_is_full_method(self):
        """Test DiscussionPage.is_full method."""
        self.load_page('Talk:For-pywikibot-archivebot')
        page = self.page
        self.assertEqual(page.archiver.maxsize, 2_096_128)
        self.assertEqual(page.size(), 181)
        self.assertTrue(page.is_full((100, 'B')))
        page.full = False
        self.assertFalse(page.is_full((1000, 'B')))
        page.full = False
        self.assertFalse(page.is_full((3, 'T')))
        page.full = False
        self.assertTrue(page.is_full((2, 'T')))
        self.assertTrue(page.is_full((3, 'T')))  # page.full is kept
        page.full = False
        page.archiver.maxsize = 100
        self.assertTrue(page.is_full((1000, 'B')))  # maxsize is used


class TestPageArchiverObject(TestCase):

    """Test PageArchiver object."""

    cached = True
    family = 'wikipedia'
    code = 'test'

    def testLoadConfigInTemplateNamespace(self):
        """Test loading of config with TEMPLATE_PAGE in Template ns.

        Talk:For-pywikibot-archivebot-01 must have::

            {{Pywikibot_archivebot
            |archive = Talk:Main_Page/archive
            |algo = old(30d)
            }}
        """
        site = self.get_site()
        page = pywikibot.Page(site, 'Talk:For-pywikibot-archivebot-01')

        # TEMPLATE_PAGE assumed in ns=10 if ns is not explicit.
        tmpl_with_ns = pywikibot.Page(site, 'Template:Pywikibot_archivebot')
        tmpl_without_ns = pywikibot.Page(site, 'Pywikibot_archivebot', ns=10)

        try:
            archivebot.PageArchiver(page, tmpl_with_ns, '')
        except Error as e:  # pragma: no cover
            self.fail(f'PageArchiver() raised {e}!')

        try:
            archivebot.PageArchiver(page, tmpl_without_ns, '')
        except Error as e:  # pragma: no cover
            self.fail(f'PageArchiver() raised {e}!')

    def testLoadConfigInOtherNamespace(self):
        """Test loading of config with TEMPLATE_PAGE not in Template ns.

        Talk:For-pywikibot-archivebot must have::

            {{User:MiszaBot/config
            |archive = Talk:Main_Page/archive
            |algo = old(30d)
            }}
        """
        site = self.get_site()
        page = pywikibot.Page(site, 'Talk:For-pywikibot-archivebot')

        tmpl_with_ns = pywikibot.Page(site, 'User:MiszaBot/config', ns=10)
        tmpl_without_ns = pywikibot.Page(site, 'MiszaBot/config', ns=10)

        # TEMPLATE_PAGE assumed in ns=10 if ns is not explicit.
        try:
            archivebot.PageArchiver(page, tmpl_with_ns, '')
        except Error as e:  # pragma: no cover
            self.fail(f'PageArchiver() raised {e}!')

        with self.assertRaises(archivebot.MissingConfigError):
            archivebot.PageArchiver(page, tmpl_without_ns, '')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
