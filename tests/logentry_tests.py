# -*- coding: utf-8  -*-
"""Test logentries module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import datetime
import sys

import pywikibot
from pywikibot.logentries import LogEntryFactory
from pywikibot.tools import MediaWikiVersion

from tests.aspects import (
    unittest, MetaTestCaseClass, TestCase, DeprecationTestCase
)
from tests.utils import add_metaclass

if sys.version_info[0] > 2:
    unicode = str


class TestLogentriesBase(TestCase):

    """
    Base class for log entry tests.

    It uses the German Wikipedia for a current representation of the log entries
    and the test Wikipedia for the future representation. It also tests on a
    wiki with MW 1.19 or older to check that it can still read the older format.
    It currently uses lyricwiki which as of this commit uses 1.19.24.
    """

    sites = {
        'tewp': {
            'family': 'wikipedia',
            'code': 'test'
        },
        'dewp': {
            'family': 'wikipedia',
            'code': 'de'
        },
        'old': {
            'family': 'lyricwiki',
            'code': 'en'
        }
    }

    def _get_logentry(self, logtype):
        """Retrieve a single log entry."""
        if self.site_key == 'old':
            # This is an assertion as the tests don't make sense with newer
            # MW versions and otherwise it might not be visible that the test
            # isn't run on an older wiki.
            self.assertLess(MediaWikiVersion(self.site.version()),
                            MediaWikiVersion('1.20'))
        return next(iter(self.site.logevents(logtype=logtype, total=1)))


class TestLogentriesMeta(MetaTestCaseClass):

    """Test meta class for TestLogentries."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def test_method(logtype):

            def test_logevent(self, key):
                """Test a single logtype entry."""
                logentry = self._get_logentry(logtype)
                self.assertEqual(logtype, logentry._expectedType)
                if key == 'old':
                    self.assertNotIn('params', logentry.data)
                else:
                    self.assertNotIn(logentry.type(), logentry.data)
                self.assertIsInstance(logentry.action(), unicode)
                self.assertIsInstance(logentry.comment(), unicode)
                self.assertIsInstance(logentry.logid(), int)
                self.assertIsInstance(logentry.ns(), int)
                self.assertIsInstance(logentry.pageid(), int)
                self.assertIsInstance(logentry.timestamp(), pywikibot.Timestamp)
                if 'title' in logentry.data:  # title may be missing
                    self.assertIsInstance(logentry.title(), pywikibot.Page)
                self.assertEqual(logentry.type(), logtype)
                self.assertIsInstance(logentry.user(), unicode)
                self.assertGreaterEqual(logentry.logid(), 0)
                self.assertGreaterEqual(logentry.ns(), -2)
                self.assertGreaterEqual(logentry.pageid(), 0)
            return test_logevent

        # create test methods for package messages processed by unittest
        for logtype in LogEntryFactory._logtypes:
            test_name = str('test_%sEntry' % logtype.title())
            dct[test_name] = test_method(logtype)

        return super(TestLogentriesMeta, cls).__new__(cls, name, bases, dct)


@add_metaclass
class TestLogentries(TestLogentriesBase):

    """Test general LogEntry properties."""

    __metaclass__ = TestLogentriesMeta


class TestLogentryParams(TestLogentriesBase):

    """Test LogEntry properties specific to their action."""

    def test_BlockEntry(self, key):
        """Test BlockEntry methods."""
        # only 'block' entries can be tested
        for logentry in self.site.logevents(logtype='block', total=5):
            if logentry.action() == 'block':
                self.assertIsInstance(logentry.flags(), list)
                # Check that there are no empty strings
                self.assertTrue(all(logentry.flags()))
                if logentry.expiry() is not None:
                    self.assertIsInstance(logentry.expiry(), pywikibot.Timestamp)
                    self.assertIsInstance(logentry.duration(), datetime.timedelta)
                    self.assertEqual(logentry.timestamp() + logentry.duration(),
                                     logentry.expiry())
                else:
                    self.assertIsNone(logentry.duration())
                break

    def test_RightsEntry(self, key):
        """Test RightsEntry methods."""
        logentry = self._get_logentry('rights')
        self.assertIsInstance(logentry.oldgroups, list)
        self.assertIsInstance(logentry.newgroups, list)

    def test_MoveEntry(self, key):
        """Test MoveEntry methods."""
        logentry = self._get_logentry('move')
        self.assertIsInstance(logentry.target_ns, pywikibot.site.Namespace)
        self.assertEqual(logentry.target_page.namespace(),
                         logentry.target_ns.id)
        self.assertIsInstance(logentry.target_title, unicode)
        self.assertIsInstance(logentry.target_page, pywikibot.Page)
        self.assertIsInstance(logentry.suppressedredirect(), bool)

    def test_PatrolEntry(self, key):
        """Test PatrolEntry methods."""
        logentry = self._get_logentry('patrol')
        self.assertIsInstance(logentry.current_id, int)
        self.assertIsInstance(logentry.previous_id, int)
        self.assertIsInstance(logentry.auto, bool)


class TestDeprecatedMethods(TestLogentriesBase, DeprecationTestCase):

    """Test cases for deprecated logentry methods."""

    def test_MoveEntry(self, key):
        """Test deprecated MoveEntry methods."""
        logentry = self._get_logentry('move')
        self.assertIsInstance(logentry.new_ns(), int)
        self.assertEqual(logentry.new_title(), logentry.target_page)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
