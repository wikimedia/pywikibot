# -*- coding: utf-8 -*-
"""Test logentries module."""
#
# (C) Pywikibot team, 2015-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import datetime

import pywikibot

from pywikibot.logentries import LogEntryFactory
from pywikibot.tools import (
    MediaWikiVersion,
    UnicodeType as unicode,
)

from tests import unittest_print
from tests.aspects import (
    unittest, MetaTestCaseClass, TestCase, DeprecationTestCase
)
from tests.utils import add_metaclass


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
            'code': 'test',
            'target': 'Main Page on wheels',
        },
        'dewp': {
            'family': 'wikipedia',
            'code': 'de',
            'target': 'Hauptseite',
        },
        'old': {
            'family': 'lyricwiki',
            'code': 'en',
            'target': None,
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

    def _test_logevent(self, logtype):
        """Test a single logtype entry."""
        logentry = self._get_logentry(logtype)
        if logtype in LogEntryFactory.logtypes:
            self.assertEqual(logentry._expectedType, logtype)
        else:
            self.assertIsNone(logentry._expectedType)
        if self.site_key == 'old':
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
            if logtype == 'block' and logentry.isAutoblockRemoval:
                self.assertIsInstance(logentry.page(), int)
            else:
                self.assertIsInstance(logentry.page(), pywikibot.Page)
        else:
            self.assertRaises(KeyError, logentry.page)
        self.assertEqual(logentry.type(), logtype)
        self.assertIsInstance(logentry.user(), unicode)
        self.assertGreaterEqual(logentry.logid(), 0)
        self.assertGreaterEqual(logentry.ns(), -2)
        self.assertGreaterEqual(logentry.pageid(), 0)


class TestLogentriesMeta(MetaTestCaseClass):

    """Test meta class for TestLogentries."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def test_method(logtype):
            def test_logevent(self, key):
                """Test a single logtype entry."""
                self._test_logevent(logtype)

            return test_logevent

        # create test methods for the support logtype classes
        for logtype in LogEntryFactory.logtypes:
            cls.add_method(dct, 'test_%sEntry' % logtype.title(),
                           test_method(logtype))

        return super(TestLogentriesMeta, cls).__new__(cls, name, bases, dct)


@add_metaclass
class TestLogentries(TestLogentriesBase):

    """Test general LogEntry properties."""

    __metaclass__ = TestLogentriesMeta


class TestSimpleLogentries(TestLogentriesBase):

    """Test logentry classes without special classes."""

    def test_simple_entries(self, key):
        """Test those entries which don't have an extra LogEntry subclass."""
        # Unfortunately it's not possible to use the metaclass to create a
        # bunch of test methods for this too as the site instances haven't been
        # initialized yet.
        available_types = set(self.site._paraminfo.parameter(
            'query+logevents', 'type')['type'])
        for simple_type in available_types - set(LogEntryFactory.logtypes):
            if not simple_type:
                # paraminfo also reports an empty string as a type
                continue
            try:
                self._test_logevent(simple_type)
            except StopIteration:
                unittest_print(
                    'Unable to test "{0}" on "{1}" because there are no log '
                    'entries with that type.'.format(simple_type, key))


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

    def test_moved_target(self, key):
        """Test moved_target method."""
        # main page was moved around
        mainpage = self.get_mainpage(self.site)
        if self.sites[key]['target'] is None:
            raise unittest.SkipTest('No moved target')
        target = mainpage.moved_target()
        self.assertIsInstance(target, pywikibot.Page)
        self.assertEqual(target.title(),
                         self.sites[key]['target'])
        # main page was moved back again, we test it.
        self.assertEqual(mainpage, target.moved_target())

    def test_moved_target_fail_old(self):
        """Test moved_target method failing on older wiki."""
        site = self.get_site('old')
        with self.assertRaises(pywikibot.NoMoveTarget):
            self.get_mainpage(site).moved_target()

    def test_moved_target_fail_de(self):
        """Test moved_target method failing on de-wiki."""
        page = pywikibot.Page(self.get_site('dewp'), 'Main Page')
        with self.assertRaises(pywikibot.NoMoveTarget):
            page.moved_target()


class TestDeprecatedMethods(TestLogentriesBase, DeprecationTestCase):

    """Test cases for deprecated logentry methods."""

    def test_MoveEntry(self, key):
        """Test deprecated MoveEntry methods."""
        logentry = self._get_logentry('move')
        self.assertIsInstance(logentry.new_ns(), int)
        self.assertOneDeprecationParts('pywikibot.logentries.MoveEntry.new_ns',
                                       'target_ns.id')

        self.assertEqual(logentry.new_title(), logentry.target_page)
        self.assertOneDeprecationParts(
            'pywikibot.logentries.MoveEntry.new_title', 'target_page')

    def test_LogEntry_title(self, key):
        """Test title and page return the same instance."""
        # Request multiple log entries in the hope that one might have no
        # title entry
        for logentry in self.site.logevents(total=5):
            if 'title' in logentry.data:  # title may be missing
                self.assertIsInstance(logentry.title(), pywikibot.Page)
                self.assertIs(logentry.title(), logentry.page())
                self.assertOneDeprecation(count=2)
            else:
                self.assertRaises(KeyError, logentry.title)
                self.assertOneDeprecation()

    def test_getMovedTarget(self, key):
        """Test getMovedTarget method."""
        # main page was moved around
        if self.sites[key]['target'] is None:
            raise unittest.SkipTest('No moved target')
        mainpage = self.get_mainpage(self.site)
        target = mainpage.getMovedTarget()
        self.assertIsInstance(target, pywikibot.Page)
        self.assertEqual(target.title(),
                         self.sites[key]['target'])
        # main page was moved back again, we test it.
        self.assertEqual(mainpage, target.getMovedTarget())

        self.assertOneDeprecationParts(
            'pywikibot.page.BasePage.getMovedTarget', 'moved_target()', 2)

    def test_moved_target_fail_old(self):
        """Test getMovedTarget method failing on older wiki."""
        site = self.get_site('old')
        with self.assertRaises(pywikibot.NoPage):
            self.get_mainpage(site).getMovedTarget()

        self.assertOneDeprecationParts('pywikibot.page.BasePage.getMovedTarget',
                                       'moved_target()')

    def test_moved_target_fail_de(self):
        """Test getMovedTarget method failing on de-wiki."""
        page = pywikibot.Page(self.get_site('dewp'), 'Main Page')
        with self.assertRaises(pywikibot.NoPage):
            page.getMovedTarget()

        self.assertOneDeprecationParts('pywikibot.page.BasePage.getMovedTarget',
                                       'moved_target()')


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
