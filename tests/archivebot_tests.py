# -*- coding: utf-8  -*-
"""Tests for archivebot scripts."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from datetime import datetime

import pywikibot
import pywikibot.page

from pywikibot.textlib import TimeStripper
from pywikibot.tools import StringTypes as basestring

from scripts import archivebot

from tests.aspects import unittest, TestCase

THREADS = {
    'als': 4, 'ar': 1, 'bar': 0, 'bg': 0, 'bjn': 1, 'bs': 0, 'ca': 5, 'ckb': 2,
    'cs': 0, 'de': 1, 'en': 25, 'eo': 2, 'es': 13, 'fa': 2, 'fr': 25, 'frr': 2,
    'hi': 0, 'hr': 2, 'hu': 5, 'id': 3, 'it': 25, 'ja': 4, 'la': 0, 'lt': 1,
    'nl': 9, 'nn': 0, 'no': 0, 'pdc': 25, 'pfl': 3, 'pl': 8, 'pt': 0, 'ro': 1,
    'ru': 20, 'scn': 2, 'simple': 1, 'sr': 0, 'sv': 5, 'th': 1, 'tr': 7,
    'ug': 0, 'uk': 1, 'uz': 1, 'vi': 1, 'zh': 4, 'zh-yue': 2,
}


class TestArchiveBot(TestCase):

    """Test archivebot script on 40+ Wikipedia sites."""

    family = 'wikipedia'
    sites = dict([(code, {'family': 'wikipedia', 'code': code})
                 for code in THREADS])

    cached = True

    def test_archivebot(self, code=None):
        """Test archivebot for one site."""
        site = self.get_site(code)
        if code != 'de':  # bug T69663
            page = pywikibot.Page(site, 'user talk:xqt')
        else:
            page = pywikibot.Page(site, 'user talk:ladsgroup')
        talk = archivebot.DiscussionPage(page, None)
        self.assertIsInstance(talk.archives, dict)
        self.assertIsInstance(talk.archived_threads, int)
        self.assertTrue(talk.archiver is None)
        self.assertIsInstance(talk.header, basestring)
        self.assertIsInstance(talk.timestripper, TimeStripper)

        self.assertIsInstance(talk.threads, list)
        self.assertGreaterEqual(
            len(talk.threads), THREADS[code],
            u'%d Threads found on %s,\n%d or more expected'
            % (len(talk.threads), talk, THREADS[code]))

        for thread in talk.threads:
            self.assertIsInstance(thread, archivebot.DiscussionThread)
            self.assertIsInstance(thread.title, basestring)
            self.assertIsInstance(thread.now, datetime)
            self.assertEqual(thread.now, talk.now)
            self.assertIsInstance(thread.ts, TimeStripper)
            self.assertEqual(thread.ts, talk.timestripper)
            self.assertIsInstance(thread.code, basestring)
            self.assertEqual(thread.code, talk.timestripper.site.code)
            self.assertIsInstance(thread.content, basestring)
            try:
                self.assertIsInstance(thread.timestamp, datetime)
            except AssertionError:
                if thread.code not in self.expected_failures:
                    pywikibot.output('code %s: %s' % (thread.code, thread.content))
                raise

    expected_failures = ['ar', 'eo', 'pdc', 'th']
    # FIXME:
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


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
