# -*- coding: utf-8  -*-
"""
Tests for several scripts.
"""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import pywikibot
import pywikibot.page
from tests.utils import unittest, PywikibotTestCase

THREADS = {
    'als': 4, 'ar': 1, 'bar': 0, 'bg': 0, 'bjn': 1, 'bs': 0, 'ca': 5, 'ckb': 2,
    'cs': 0, 'de': 7, 'en': 25, 'eo': 1, 'es': 13, 'fa': 2, 'fr': 25, 'frr': 2,
    'hi': 0, 'hr': 2, 'hu': 5, 'id': 3, 'it': 25, 'ja': 4, 'la': 0, 'lt': 1,
    'nl': 9, 'nn': 0, 'no': 0, 'pdc': 25, 'pfl': 3, 'pl': 8, 'pt': 0, 'ro': 1,
    'ru': 20, 'scn': 2, 'simple': 1, 'sr': 0, 'sv': 5, 'th': 1, 'tr': 7,
    'ug': 0, 'uk': 1, 'uz': 1, 'vi': 1, 'zh': 4, 'zh-yue': 2,
}


class TestArchiveBotMeta(type):

    """Test meta class"""

    def __new__(cls, name, bases, dct):
        """create the new class"""

        def test_method(code):

            def test_archivebot(self):
                """Test archivebot for one site"""
                site = pywikibot.Site(code, 'wikipedia')
                page = pywikibot.Page(site, 'user talk:xqt')
                talk = archivebot.DiscussionPage(page, None)
                self.assertTrue(isinstance(talk.archives, dict))
                self.assertTrue(isinstance(talk.archived_threads, int))
                self.assertTrue(talk.archiver is None)
                self.assertTrue(isinstance(talk.header, basestring))
                self.assertTrue(isinstance(talk.timestripper, TimeStripper))

                self.assertTrue(isinstance(talk.threads, list))
                self.assertGreaterEqual(
                    len(talk.threads), THREADS[code],
                    u'%d Threads found on %s,\n%d or more expected'
                    % (len(talk.threads), talk, THREADS[code]))

                for thread in talk.threads:
                    self.assertTrue(isinstance(thread,
                                               archivebot.DiscussionThread))
                    self.assertTrue(isinstance(thread.title, basestring))
                    self.assertTrue(isinstance(thread.now, datetime))
                    self.assertTrue(thread.now == talk.now)
                    self.assertTrue(isinstance(thread.ts, TimeStripper))
                    self.assertTrue(thread.ts == talk.timestripper)
                    self.assertTrue(isinstance(thread.code, basestring))
                    self.assertEqual(thread.code, talk.timestripper.site.code)
                    self.assertTrue(isinstance(thread.content, basestring))
                    self.assertTrue(isinstance(thread.timestamp, datetime))

            return test_archivebot

        # setUp class
        from datetime import datetime
        from scripts import archivebot
        from pywikibot.textlib import TimeStripper

        # create test methods processed by unittest
        for code in THREADS:
            test_name = "test_wikipedia_" + code

            if code in ['ar', 'ckb', 'fa', 'pdc', 'th']:
                # expected failures - should be fixed
                # 'ar', 'ckb', 'fa': no digits in date, regex does not match
                # 'pdc': changed month name setting in wiki over time (?)
                #   in old posts in talk page, February is "Feb.", site message gives
                #   <message name="feb" xml:space="preserve">Han.</message>.
                #   for new entries it should work
                # 'th': year is 2552 while regex assumes 19..|20.., might be fixed
                dct[test_name] = unittest.expectedFailure(test_method(code))
            else:
                dct[test_name] = test_method(code)
            dct[test_name].__name__ = test_name
        return type.__new__(cls, name, bases, dct)


class TestArchiveBot(PywikibotTestCase):

    """Test archivebot script"""

    __metaclass__ = TestArchiveBotMeta


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
