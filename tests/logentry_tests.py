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

from tests.aspects import (
    unittest, MetaTestCaseClass, TestCase, DeprecationTestCase
)

if sys.version_info[0] > 2:
    unicode = str


def get_logentry(site, logtype):
    """Global method to retriev a single log entry."""
    return next(iter(site.logevents(logtype=logtype, total=1)))


class TestLogentriesMeta(MetaTestCaseClass):

    """Test meta class for TestLogentries."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        cls.site = pywikibot.Site('de', 'wikipedia')

        def test_method(logtype):

            def test_logevent(self):
                """Test a single logtype entry."""
                logentry = get_logentry(cls.site, logtype)
                self.assertEqual(logtype, logentry._expectedType)
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

        return super(MetaTestCaseClass, cls).__new__(cls, name, bases, dct)


class TestLogentries(TestCase):

    """Test TestLogentries processed by unittest."""

    __metaclass__ = TestLogentriesMeta


class TestLogentryParams(TestCase):

    """Test Logentry params."""

    family = 'wikipedia'
    code = 'de'

    def test_BlockEntry(self):
        """Test BlockEntry methods."""
        logentry = get_logentry(self.site, 'block')
        if logentry.action() == 'block':
            self.assertIsInstance(logentry.flags(), list)
        if logentry.expiry() is not None:
            self.assertIsInstance(logentry.expiry(), pywikibot.Timestamp)
            self.assertIsInstance(logentry.duration(), datetime.timedelta)

    def test_RightsEntry(self):
        """Test MoveEntry methods."""
        logentry = get_logentry(self.site, 'rights')
        self.assertIsInstance(logentry.oldgroups, list)
        self.assertIsInstance(logentry.newgroups, list)

    def test_MoveEntry(self):
        """Test MoveEntry methods."""
        logentry = get_logentry(self.site, 'move')
        self.assertIsInstance(logentry.target_ns, pywikibot.site.Namespace)
        self.assertEqual(logentry.target_page.namespace(),
                         logentry.target_ns.id)
        self.assertIsInstance(logentry.target_title, unicode)
        self.assertIsInstance(logentry.target_page, pywikibot.Page)
        self.assertIsInstance(logentry.suppressedredirect(), bool)

    def test_PatrolEntry(self):
        """Test MoveEntry methods."""
        logentry = get_logentry(self.site, 'patrol')
        self.assertIsInstance(logentry.current_id, int)
        self.assertIsInstance(logentry.previous_id, int)
        self.assertIsInstance(logentry.auto, bool)


class TestDeprecatedMethods(DeprecationTestCase):

    """Test cases for deprecated logentry methods."""

    family = 'wikipedia'
    code = 'de'

    def test_MoveEntry(self):
        """Test MoveEntry methods."""
        logentry = get_logentry(self.site, 'move')
        self.assertIsInstance(logentry.new_ns(), int)
        self.assertEqual(logentry.new_title(), logentry.target_page)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
