#!/usr/bin/python3
"""Test logentries module."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import datetime
import unittest
from contextlib import suppress

import pywikibot
from pywikibot.exceptions import HiddenKeyError, NoMoveTargetError
from pywikibot.family import AutoFamily
from pywikibot.logentries import (
    LogEntryFactory,
    OtherLogEntry,
    UserTargetLogEntry,
)
from tests import unittest_print
from tests.aspects import MetaTestCaseClass, TestCase
from tests.utils import skipping


class TestLogentriesBase(TestCase):

    """
    Base class for log entry tests.

    It uses the German Wikipedia for a current representation of the
    log entries and the test Wikipedia for the future representation.
    It also tests on a wiki with MW < 1.25 to check that it can still
    read the older format. It currently uses portalwiki which as of this
    commit uses 1.23.16.
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
        'enwow': {
            'family': 'wowwiki',
            'code': 'en',
            'target': None,
        },
        'old': {
            'family': AutoFamily('portalwiki',
                                 'https://theportalwiki.com/wiki/Main_Page'),
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
            self.assertLess(self.site.mw_version, '1.25')

        with skipping(StopIteration,
                      msg='No entry found for {!r}'.format(logtype)):
            le = next(self.site.logevents(logtype=logtype, total=1))
        return le

    def _test_logevent(self, logtype):
        """Test a single logtype entry."""
        logentry = self._get_logentry(logtype)
        self.assertIn(logtype, logentry.__class__.__name__.lower())
        self.assertEqual(logentry._expected_type, logtype)

        if logtype not in LogEntryFactory._logtypes:
            self.assertIsInstance(logentry, OtherLogEntry)

        if self.site_key == 'old':
            self.assertNotIn('params', logentry.data)
        else:
            self.assertNotIn(logentry.type(), logentry.data)

        self.assertIsInstance(logentry.action(), str)

        try:
            self.assertIsInstance(logentry.comment(), str)
            self.assertIsInstance(logentry.user(), str)
            self.assertEqual(logentry.user(), logentry['user'])
        except HiddenKeyError as e:
            self.assertRegex(
                str(e),
                r"Log entry \([^)]+\) has a hidden '\w+' key and you "
                r"don't have permission to view it")
        except KeyError as e:
            self.assertRegex(str(e), "Log entry ([^)]+) has no 'comment' key")
        else:
            self.assertEqual(logentry.comment(), logentry['comment'])

        self.assertIsInstance(logentry.logid(), int)
        self.assertIsInstance(logentry.timestamp(), pywikibot.Timestamp)

        if 'title' in logentry.data:  # title may be missing
            self.assertIsInstance(logentry.ns(), int)
            self.assertIsInstance(logentry.pageid(), int)

            # test new UserDict style
            self.assertEqual(logentry.data['title'], logentry['title'])
            self.assertEqual(logentry.ns(), logentry['ns'])
            self.assertEqual(logentry.pageid(), logentry['pageid'])

            self.assertGreaterEqual(logentry.ns(), -2)
            self.assertGreaterEqual(logentry.pageid(), 0)
            if logtype == 'block' and logentry.isAutoblockRemoval:
                self.assertIsInstance(logentry.page(), int)
            elif isinstance(logentry, UserTargetLogEntry):
                self.assertIsInstance(logentry.page(), pywikibot.User)
            elif logtype == 'upload':
                self.assertIsInstance(logentry.page(), pywikibot.FilePage)
            else:
                self.assertIsInstance(logentry.page(), pywikibot.Page)
        else:
            with self.assertRaises(KeyError):
                logentry.page()

        self.assertEqual(logentry.type(), logtype)
        self.assertGreaterEqual(logentry.logid(), 0)

        # test new UserDict style
        self.assertEqual(logentry.type(), logentry['type'])
        self.assertEqual(logentry.logid(), logentry['logid'])


class TestLogentriesMeta(MetaTestCaseClass):

    """Test meta class for TestLogentries."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def test_method(logtype):
            def test_logevent(self, key):
                """Test a single logtype entry."""
                site = self.sites[key]['site']
                if logtype not in site.logtypes:
                    self.skipTest('{}: "{}" logtype not available on {}.'
                                  .format(key, logtype, site))
                self._test_logevent(logtype)

            return test_logevent

        # create test methods for the support logtype classes
        for logtype in LogEntryFactory._logtypes:
            cls.add_method(dct, 'test_{}Entry'.format(logtype.title()),
                           test_method(logtype))

        return super().__new__(cls, name, bases, dct)


class TestLogentries(TestLogentriesBase, metaclass=TestLogentriesMeta):

    """Test general LogEntry properties."""


class TestSimpleLogentries(TestLogentriesBase):

    """Test logentry classes without special classes."""

    def test_simple_entries(self, key):
        """Test those entries which don't have an extra LogEntry subclass."""
        # Unfortunately it's not possible to use the metaclass to create a
        # bunch of test methods for this too as the site instances haven't
        # been initialized yet.
        for simple_type in (self.site.logtypes
                            - set(LogEntryFactory._logtypes)):
            if not simple_type:
                # paraminfo also reports an empty string as a type
                continue
            try:
                self._test_logevent(simple_type)
            except StopIteration:
                unittest_print(
                    'Unable to test "{}" on "{}" because there are no log '
                    'entries with that type.'.format(simple_type, key))


class TestLogentryParams(TestLogentriesBase):

    """Test LogEntry properties specific to their action."""

    def test_block_entry(self, key):
        """Test BlockEntry methods."""
        # only 'block' entries can be tested
        for logentry in self.site.logevents(logtype='block', total=5):
            if logentry.action() == 'block':
                self.assertIsInstance(logentry.flags(), list)
                # Check that there are no empty strings
                for flag in logentry.flags():
                    self.assertIsInstance(flag, str)
                    self.assertNotEqual(flag, '')
                if logentry.expiry() is not None:
                    self.assertIsInstance(logentry.expiry(),
                                          pywikibot.Timestamp)
                    self.assertIsInstance(logentry.duration(),
                                          datetime.timedelta)
                    self.assertEqual(
                        logentry.timestamp() + logentry.duration(),
                        logentry.expiry())
                else:
                    self.assertIsNone(logentry.duration())
                break

    def test_rights_entry(self, key):
        """Test RightsEntry methods."""
        logentry = self._get_logentry('rights')
        self.assertIsInstance(logentry.oldgroups, list)
        self.assertIsInstance(logentry.newgroups, list)

    def test_move_entry(self, key):
        """Test MoveEntry methods."""
        logentry = self._get_logentry('move')
        self.assertIsInstance(logentry.target_ns, pywikibot.site.Namespace)
        self.assertEqual(logentry.target_page.namespace(),
                         logentry.target_ns.id)
        self.assertIsInstance(logentry.target_title, str)
        self.assertIsInstance(logentry.target_page, pywikibot.Page)
        self.assertIsInstance(logentry.suppressedredirect(), bool)

    def test_patrol_entry(self, key):
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
            self.skipTest('No moved target')
        target = mainpage.moved_target()
        self.assertIsInstance(target, pywikibot.Page)
        self.assertEqual(target.title(),
                         self.sites[key]['target'])
        # main page was moved back again, we test it.
        self.assertEqual(mainpage, target.moved_target())

    def test_moved_target_fail_old(self):
        """Test moved_target method failing on older wiki."""
        site = self.get_site('old')
        with self.assertRaises(NoMoveTargetError):
            self.get_mainpage(site).moved_target()

    def test_moved_target_fail_de(self):
        """Test moved_target method failing on de-wiki."""
        page = pywikibot.Page(self.get_site('dewp'), 'Main Page')
        with self.assertRaises(NoMoveTargetError):
            page.moved_target()

    def test_thanks_page(self, key):
        """Test Thanks page method return type."""
        if not self.site.has_extension('Thanks'):
            self.skipTest('Thanks extension not available.')
        logentry = self._get_logentry('thanks')
        self.assertIsInstance(logentry.page(), pywikibot.User)

    def test_equality(self):
        """Test equality of LogEntry instances."""
        site = self.get_site('dewp')
        other_site = self.get_site('tewp')
        gen1 = site.logevents(reverse=True, total=2)
        gen2 = site.logevents(reverse=True, total=2)
        le1 = next(gen1)
        le2 = next(gen2)
        le3 = next(other_site.logevents(reverse=True, total=1))
        le4 = next(gen1)
        le5 = next(gen2)
        self.assertEqual(le1, le2)
        self.assertFalse(le1 != le2)  # noqa: H204
        self.assertNotEqual(le1, le3)
        self.assertNotEqual(le1, site)
        self.assertIsInstance(le4, OtherLogEntry)
        self.assertIsInstance(le5, OtherLogEntry)
        self.assertEqual(type(le4), type(le5))


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
