#!/usr/bin/env python3
"""Tests for the site module."""
#
# (C) Pywikibot team, 2008-2026
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import pickle
import random
import threading
import time
import unittest
from collections.abc import Iterable, Mapping
from contextlib import suppress

import pywikibot
from pywikibot import config
from pywikibot.exceptions import (
    APIError,
    Error,
    IsNotRedirectPageError,
    NoPageError,
    PageInUseError,
    UnknownExtensionError,
    UnknownSiteError,
)
from tests.aspects import (
    AlteredDefaultSiteTestCase,
    DefaultDrySiteTestCase,
    DefaultSiteTestCase,
    DeprecationTestCase,
    PatchingTestCase,
    TestCase,
    WikimediaDefaultSiteTestCase,
)
from tests.basepage import BasePageLoadRevisionsCachingTestBase


class TestSiteObject(DefaultSiteTestCase):

    """Test cases for Site methods."""

    cached = True

    def test_pickle_ability(self) -> None:
        """Test pickle ability."""
        mysite = self.get_site()
        mysite_str = pickle.dumps(mysite, protocol=config.pickle_protocol)
        mysite_pickled = pickle.loads(mysite_str)
        self.assertEqual(mysite, mysite_pickled)

    def test_repr(self) -> None:
        """Test __repr__."""
        code = self.site.family.obsolete.get(self.code) or self.code
        expect = f"Site('{code}', '{self.family}')"
        reprs = repr(self.site)
        self.assertEndsWith(reprs, expect)

    def test_constructors(self) -> None:
        """Test cases for site constructors."""
        test_dict = {
            'alswiki': 'wikipedia:als',  # see T345036
            'commonswiki': 'commons:commons',
            'dewikinews': 'wikinews:de',
            'enwiki': 'wikipedia:en',
            'eswikisource': 'wikisource:es',
            'metawiki': 'meta:meta',
            'roa_rupwiki': 'wikipedia:roa-rup',  # see T345036
            'sourceswiki': 'wikisource:mul',  # see T226960
            'test2wiki': 'wikipedia:test2',  # see T225729
            'testwiki': 'wikipedia:test',  # see T225729, T228300
            'testwikidatawiki': 'wikidata:test',
            'ukwikivoyage': 'wikivoyage:uk',
            'wikidatawiki': 'wikidata:wikidata',
        }
        if isinstance(self.site.family, pywikibot.family.WikimediaFamily):
            site = self.site
        else:
            site = None
        for dbname, sitename in test_dict.items():
            with self.subTest(dbname=dbname):
                self.assertIs(
                    pywikibot.site.APISite.fromDBName(dbname, site),
                    pywikibot.Site(sitename))

    def test_codes_property(self) -> None:
        """Test cases for codes property and related methods."""
        mysite = self.get_site()
        codes = mysite.codes
        self.assertIsInstance(codes, set)
        self.assertIn(mysite.code, codes)
        self.assertIsInstance(mysite.obsolete, bool)
        ipf = mysite.interwiki_putfirst()
        if ipf:  # no languages use this anymore, keep it for foreign families
            self.assertIsInstance(ipf, list)  # pragma: no cover
        else:
            self.assertIsNone(ipf)

        for item in mysite.validLanguageLinks():
            self.assertIn(item, codes)
            self.assertIsNone(self.site.namespaces.lookup_name(item))

    def test_namespace_methods(self) -> None:
        """Test cases for methods manipulating namespace names."""
        mysite = self.get_site()
        ns = mysite.namespaces
        self.assertIsInstance(ns, Mapping)
        # built-in namespaces always present
        self.assertIsInstance(mysite.ns_normalize('project'), str)

        for ns_id in range(-2, 16):
            with self.subTest(namespace_id=ns_id):
                self.assertIn(ns_id, ns)

        for key in ns:
            all_ns = mysite.namespace(key, True)
            with self.subTest(namespace=key):
                self.assertIsInstance(key, int)
                self.assertIsInstance(mysite.namespace(key), str)
                self.assertNotIsInstance(all_ns, str)
                self.assertIsInstance(all_ns, Iterable)

            for item in all_ns:
                with self.subTest(namespace=key, item=item):
                    self.assertIsInstance(item, str)

        for val in ns.values():
            with self.subTest(value=val):
                self.assertIsInstance(val, Iterable)
            for name in val:
                with self.subTest(value=val, name=name):
                    self.assertIsInstance(name, str)

    def test_user_attributes_return_types(self) -> None:
        """Test returned types of user attributes."""
        mysite = self.get_site()
        self.assertIsInstance(mysite.logged_in(), bool)
        self.assertIsInstance(mysite.userinfo, dict)

    def test_messages(self) -> None:
        """Test MediaWiki: messages."""
        mysite = self.get_site()
        for msg in ('about', 'aboutpage', 'aboutsite', 'accesskey-n-portal'):
            with self.subTest(message=msg, lang=mysite.lang):
                self.assertTrue(mysite.has_mediawiki_message(msg))
                self.assertIsInstance(mysite.mediawiki_message(msg), str)
                self.assertEqual(
                    mysite.mediawiki_message(msg),
                    mysite.mediawiki_message(msg, lang=mysite.lang))

            with self.subTest(message=msg, lang='de'):
                self.assertTrue(mysite.has_mediawiki_message(msg, lang='de'))
                self.assertIsInstance(mysite.mediawiki_message(msg, lang='de'),
                                      str)

        with self.subTest(message='nosuchmessage'):
            self.assertFalse(mysite.has_mediawiki_message('nosuchmessage'))
            with self.assertRaises(KeyError):
                mysite.mediawiki_message('nosuchmessage')

        msg = ('about', 'aboutpage')
        with self.subTest(messages=msg):
            about_msgs = self.site.mediawiki_messages(msg)
            self.assertIsInstance(mysite.mediawiki_messages(msg), dict)
            self.assertTrue(mysite.mediawiki_messages(msg))
            self.assertLength(about_msgs, 2)
            self.assertIn(msg[0], about_msgs)

        months = ['january', 'february', 'march', 'april', 'may_long',
                  'june', 'july', 'august', 'september', 'october',
                  'november', 'december']
        codes = sorted(mysite.family.codes)
        lang1, lang2 = codes[0], codes[-1]
        with self.subTest(messages='months', lang1=lang1, lang2=lang2):
            self.assertLength(mysite.mediawiki_messages(months, lang1), 12)
            self.assertLength(mysite.mediawiki_messages(months, lang2), 12)
            familyname = mysite.family.name
            if lang1 not in (lang2, familyname) and lang2 != familyname:
                self.assertNotEqual(mysite.mediawiki_messages(months, lang1),
                                    mysite.mediawiki_messages(months, lang2))

        with self.subTest(messages='Test messages order'):
            msg = mysite.mediawiki_messages(months, 'en')
            self.assertIsInstance(msg, dict)
            self.assertLength(msg, 12)
            self.assertEqual([key.title() for key in msg][5:],
                             list(msg.values())[5:])
            self.assertEqual(list(msg), months)

        # mediawiki_messages must be given a list; using a string will split it
        with self.subTest(messages='about'), self.assertRaises(KeyError):
            self.site.mediawiki_messages('about')

        msg = ('nosuchmessage1', 'about', 'aboutpage', 'nosuchmessage')
        with self.subTest(messages=msg):
            self.assertFalse(mysite.has_all_mediawiki_messages(msg))
            with self.assertRaises(KeyError):
                mysite.mediawiki_messages(msg)

        with self.subTest(test='server_time'):
            self.assertIsInstance(mysite.server_time(), pywikibot.Timestamp)
            ts = mysite.getcurrenttimestamp()
            self.assertIsInstance(ts, str)
            self.assertRegex(
                ts, r'(19|20)\d\d[0-1]\d[0-3]\d[0-2]\d[0-5]\d[0-5]\d')

        with self.subTest(test='months_names'):
            self.assertIsInstance(mysite.months_names, list)
            self.assertLength(mysite.months_names, 12)
            for month in mysite.months_names:
                self.assertIsInstance(month, tuple)
                self.assertLength(month, 2)

        with self.subTest(test='list_to_text'):
            self.assertEqual(mysite.list_to_text(('pywikibot',)), 'pywikibot')

    def test_english_specific_methods(self) -> None:
        """Test Site methods using English specific inputs and outputs."""
        mysite = self.get_site()
        if mysite.lang != 'en':
            self.skipTest(
                f'English-specific tests not valid on {mysite}')

        self.assertEqual(mysite.months_names[4], ('May', 'May'))
        self.assertEqual(mysite.list_to_text(('Pride', 'Prejudice')),
                         'Pride and Prejudice')
        self.assertEqual(mysite.list_to_text(('This', 'that', 'the other')),
                         'This, that and the other')

    def test_page_methods(self) -> None:
        """Test ApiSite methods for getting page-specific info."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        self.assertIsInstance(mysite.page_restrictions(mainpage), dict)
        self.assertIsInstance(mysite.page_can_be_edited(mainpage), bool)
        self.assertIsInstance(mysite.page_isredirect(mainpage), bool)
        if mysite.page_isredirect(mainpage):
            self.assertIsInstance(mysite.getredirtarget(mainpage),
                                  pywikibot.Page)
        else:
            with self.assertRaises(IsNotRedirectPageError):
                mysite.getredirtarget(mainpage)
        a = list(mysite.preloadpages([mainpage]))
        self.assertLength(a, int(mainpage.exists()))
        if a:
            self.assertEqual(a[0], mainpage)

    def test_maxlimit(self) -> None:
        """Test maxlimit property."""
        limit = self.site.maxlimit
        self.assertIsInstance(limit, int)
        self.assertIn(limit, [10, 50, 500, 5000])

    def test_ratelimit(self) -> None:
        """Test ratelimit method."""
        actions = ('edit', 'move', 'purge', 'invalid')
        if self.site.logged_in():
            groups = ['user', 'unknown', 'noratelimit']
        else:
            groups = ['ip', 'unknown']
            self.assertFalse(self.site.has_right('noratelimit'))
        for action in actions:
            with self.subTest(action=action):
                limit = self.site.ratelimit(action)
                self.assertIn(limit.group, groups)
                self.assertEqual(limit.seconds / limit.hits, limit.delay)
                self.assertEqual(
                    1 / limit.delay if limit.seconds else float('inf'),
                    limit.ratio)
                if limit.group == 'unknown':
                    self.assertEqual(limit.hits, self.site.maxlimit)
                    self.assertEqual(limit.seconds, config.put_throttle)


class TestLockingPage(DefaultSiteTestCase):

    """Test cases for lock/unlock a page within threads."""

    cached = True

    def worker(self) -> None:
        """Lock a page, wait few seconds and unlock the page."""
        page = pywikibot.Page(self.site, 'Foo')
        page.site.lock_page(page=page, block=True)
        wait = random.randint(1, 25) / 10
        time.sleep(wait)
        page.site.unlock_page(page=page)

    def test_threads_locking_page(self) -> None:
        """Test lock_page and unlock_page methods for multiple threads."""
        # Start few threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=self.worker, daemon=True)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join(15)  # maximum wait time for all threads

            with self.subTest(name=thread.name):
                # Check whether a timeout happened.
                # In that case is_alive() is True
                self.assertFalse(thread.is_alive(),
                                 'test page is still locked')

    def test_lock_page(self) -> None:
        """Test the site.lock_page() and site.unlock_page() method."""
        site = self.get_site()
        p1 = pywikibot.Page(site, 'Foo')

        site.lock_page(page=p1, block=True)
        with self.assertRaises(PageInUseError):
            site.lock_page(page=p1, block=False)
        site.unlock_page(page=p1)
        # verify it's unlocked
        site.lock_page(page=p1, block=False)
        site.unlock_page(page=p1)


class SiteUserTestCase(DefaultSiteTestCase, DeprecationTestCase):

    """Test site method using a user."""

    login = True

    def test_methods(self) -> None:
        """Test user related methods."""
        mysite = self.get_site()
        self.assertIsInstance(mysite.is_blocked(), bool)
        self.assertIsInstance(mysite.has_right('edit'), bool)
        self.assertFalse(mysite.has_right('nonexistent_right'))
        self.assertIsInstance(mysite.has_group('bots'), bool)
        self.assertFalse(mysite.has_group('nonexistent_group'))
        for grp in ('user', 'autoconfirmed', 'bot', 'sysop', 'nosuchgroup'):
            self.assertIsInstance(mysite.has_group(grp), bool)
        for rgt in ('read', 'edit', 'move', 'delete', 'rollback', 'block',
                    'nosuchright'):
            self.assertIsInstance(mysite.has_right(rgt), bool)

    def test_logevents(self) -> None:
        """Test the site.logevents() method."""
        mysite = self.get_site()
        for entry in mysite.logevents(user=mysite.user(), total=3):
            self.assertEqual(entry.user(), mysite.user())


class SiteSysopTestCase(DefaultSiteTestCase):

    """Test site method using a sysop account."""

    rights = 'delete'

    def test_methods(self) -> None:
        """Test sysop related methods."""
        mysite = self.get_site()
        self.assertIsInstance(mysite.is_blocked(), bool)
        self.assertIsInstance(mysite.has_right('edit'), bool)
        self.assertFalse(mysite.has_right('nonexistent_right'))
        self.assertIsInstance(mysite.has_group('bots'), bool)
        self.assertFalse(mysite.has_group('nonexistent_group'))
        self.assertTrue(mysite.has_right(self.rights))

    def test_deletedrevs(self) -> None:
        """Test the site.deletedrevs() method."""
        mysite = self.get_site()
        if not mysite.has_right('deletedhistory'):
            self.skipTest(
                "You don't have permission to view the deleted revisions "
                f'on {mysite}.')
        mainpage = self.get_mainpage()
        gen = mysite.deletedrevs(total=10, titles=mainpage)

        for dr in gen:
            break
        else:
            self.skipTest(
                f'{mainpage} contains no deleted revisions.')
        self.assertLessEqual(len(dr['revisions']), 10)
        for rev in dr['revisions']:
            self.assertIsInstance(rev, dict)

        with self.subTest(start='2008-10-11T01:02:03Z', reverse=False):
            for item in mysite.deletedrevs(start='2008-10-11T01:02:03Z',
                                           titles=mainpage, total=5):
                for rev in item['revisions']:
                    self.assertIsInstance(rev, dict)
                    self.assertLessEqual(rev['timestamp'],
                                         '2008-10-11T01:02:03Z')

        with self.subTest(end='2008-04-01T02:03:04Z', reverse=False):
            for item in mysite.deletedrevs(end='2008-04-01T02:03:04Z',
                                           titles=mainpage, total=5):
                for rev in item['revisions']:
                    self.assertIsInstance(rev, dict)
                    self.assertGreaterEqual(rev['timestamp'],
                                            '2008-10-11T02:03:04Z')

        with self.subTest(start='2008-10-11T03:05:07Z', reverse=True):
            for item in mysite.deletedrevs(start='2008-10-11T03:05:07Z',
                                           titles=mainpage, total=5,
                                           reverse=True):
                for rev in item['revisions']:
                    self.assertIsInstance(rev, dict)
                    self.assertGreaterEqual(rev['timestamp'],
                                            '2008-10-11T03:05:07Z')

        with self.subTest(end='2008-10-11T04:06:08Z', reverse=True):
            for item in mysite.deletedrevs(end='2008-10-11T04:06:08Z',
                                           titles=mainpage, total=5,
                                           reverse=True):
                for rev in item['revisions']:
                    self.assertIsInstance(rev, dict)
                    self.assertLessEqual(rev['timestamp'],
                                         '2008-10-11T04:06:08Z')

        with self.subTest(start='2008-10-13T11:59:59Z',
                          end='2008-10-13T00:00:01Z',
                          reverse=False):
            for item in mysite.deletedrevs(start='2008-10-13T11:59:59Z',
                                           end='2008-10-13T00:00:01Z',
                                           titles=mainpage, total=5):
                for rev in item['revisions']:
                    self.assertIsInstance(rev, dict)
                    self.assertLessEqual(rev['timestamp'],
                                         '2008-10-13T11:59:59Z')
                    self.assertGreaterEqual(rev['timestamp'],
                                            '2008-10-13T00:00:01Z')

        with self.subTest(start='2008-10-15T06:00:01Z',
                          end='2008-10-15T23:59:59Z',
                          reverse=True):
            for item in mysite.deletedrevs(start='2008-10-15T06:00:01Z',
                                           end='2008-10-15T23:59:59Z',
                                           titles=mainpage, total=5,
                                           reverse=True):
                for rev in item['revisions']:
                    self.assertIsInstance(rev, dict)
                    self.assertLessEqual(rev['timestamp'],
                                         '2008-10-15T23:59:59Z')
                    self.assertGreaterEqual(rev['timestamp'],
                                            '2008-10-15T06:00:01Z')

        # start earlier than end
        with self.subTest(start='2008-09-03T00:00:01Z',
                          end='2008-09-03T23:59:59Z',
                          reverse=False), self.assertRaises(AssertionError):
            gen = mysite.deletedrevs(titles=mainpage,
                                     start='2008-09-03T00:00:01Z',
                                     end='2008-09-03T23:59:59Z', total=5)
            next(gen)

        # reverse: end earlier than start
        with self.subTest(start='2008-09-03T23:59:59Z',
                          end='2008-09-03T00:00:01Z',
                          reverse=True), self.assertRaises(AssertionError):
            gen = mysite.deletedrevs(titles=mainpage,
                                     start='2008-09-03T23:59:59Z',
                                     end='2008-09-03T00:00:01Z', total=5,
                                     reverse=True)
            next(gen)

    def test_alldeletedrevisions(self) -> None:
        """Test the site.alldeletedrevisions() method."""
        mysite = self.get_site()
        myuser = mysite.user()
        if not mysite.has_right('deletedhistory'):
            self.skipTest(
                "You don't have permission to view the deleted revisions "
                f'on {mysite}.')
        prop = ['ids', 'timestamp', 'flags', 'user', 'comment']
        gen = mysite.alldeletedrevisions(total=10, prop=prop)

        for data in gen:
            break
        else:
            self.skipTest(f'{myuser} does not have deleted edits.')
        self.assertIn('revisions', data)
        for drev in data['revisions']:
            for key in ('revid', 'timestamp', 'user', 'comment'):
                self.assertIn(key, drev)

        with self.subTest(start='2008-10-11T01:02:03Z', reverse=False,
                          prop=prop):
            for item in mysite.alldeletedrevisions(
                start='2008-10-11T01:02:03Z',
                user=myuser,
                total=5
            ):
                for drev in item['revisions']:
                    self.assertIsInstance(drev, dict)
                    self.assertLessEqual(drev['timestamp'],
                                         '2008-10-11T01:02:03Z')

        with self.subTest(start='2008-10-11T01:02:03Z', reverse=True,
                          prop=prop):
            for item in mysite.alldeletedrevisions(
                start='2008-10-11T01:02:03Z',
                user=myuser,
                total=5
            ):
                for drev in item['revisions']:
                    self.assertIsInstance(drev, dict)
                    self.assertGreaterEqual(drev['timestamp'],
                                            '2008-10-11T01:02:03Z')

        # start earlier than end
        with self.subTest(start='2008-09-03T00:00:01Z',
                          end='2008-09-03T23:59:59Z',
                          reverse=False,
                          prop=prop), self.assertRaises(AssertionError):
            gen = mysite.alldeletedrevisions(start='2008-09-03T00:00:01Z',
                                             end='2008-09-03T23:59:59Z',
                                             total=5)
            next(gen)

        # reverse: end earlier than start
        with self.subTest(start='2008-09-03T23:59:59Z',
                          end='2008-09-03T00:00:01Z',
                          reverse=True,
                          prop=prop), self.assertRaises(AssertionError):
            gen = mysite.alldeletedrevisions(start='2008-09-03T23:59:59Z',
                                             end='2008-09-03T00:00:01Z',
                                             total=5, reverse=True)
            next(gen)


class TestSiteSysopWrite(TestCase):

    """Test site methods that require writing rights."""

    family = 'wikipedia'
    code = 'test'

    write = True
    rights = 'delete,deleterevision,protect'

    def test_protect(self) -> None:
        """Test the site.protect() method."""
        site = self.get_site()
        p1 = pywikibot.Page(site, 'User:Unicodesnowman/ProtectTest')

        r = site.protect(protections={'edit': 'sysop',
                                      'move': 'autoconfirmed'},
                         page=p1,
                         reason='Pywikibot unit test')
        self.assertIsNone(r)
        self.assertEqual(site.page_restrictions(page=p1),
                         {'edit': ('sysop', 'infinite'),
                          'move': ('autoconfirmed', 'infinite')})

        expiry = pywikibot.Timestamp.fromISOformat('2050-01-01T00:00:00Z')
        site.protect(protections={'edit': 'sysop', 'move': 'autoconfirmed'},
                     page=p1,
                     expiry=expiry,
                     reason='Pywikibot unit test')

        self.assertEqual(site.page_restrictions(page=p1),
                         {'edit': ('sysop', '2050-01-01T00:00:00Z'),
                          'move': ('autoconfirmed', '2050-01-01T00:00:00Z')})

        site.protect(protections={'edit': '', 'move': ''},
                     page=p1,
                     reason='Pywikibot unit test')
        self.assertEqual(site.page_restrictions(page=p1), {})

    def test_protect_alt(self) -> None:
        """Test the site.protect() method, works around T78522."""
        site = self.get_site()
        p1 = pywikibot.Page(site, 'User:Unicodesnowman/ProtectTest')

        r = site.protect(protections={'edit': 'sysop',
                                      'move': 'autoconfirmed'},
                         page=p1,
                         reason='Pywikibot unit test')
        self.assertIsNone(r)
        self.assertEqual(site.page_restrictions(page=p1),
                         {'edit': ('sysop', 'infinite'),
                          'move': ('autoconfirmed', 'infinite')})

        p1 = pywikibot.Page(site, 'User:Unicodesnowman/ProtectTest')
        expiry = pywikibot.Timestamp.fromISOformat('2050-01-01T00:00:00Z')
        site.protect(protections={'edit': 'sysop', 'move': 'autoconfirmed'},
                     page=p1,
                     expiry=expiry,
                     reason='Pywikibot unit test')

        self.assertEqual(site.page_restrictions(page=p1),
                         {'edit': ('sysop', '2050-01-01T00:00:00Z'),
                          'move': ('autoconfirmed', '2050-01-01T00:00:00Z')})

        p1 = pywikibot.Page(site, 'User:Unicodesnowman/ProtectTest')
        site.protect(protections={'edit': '', 'move': ''},
                     page=p1,
                     reason='Pywikibot unit test')
        self.assertEqual(site.page_restrictions(page=p1), {})

    def test_protect_exception(self) -> None:
        """Test that site.protect() throws an exception for invalid args."""
        site = self.get_site()
        page = pywikibot.Page(site, 'User:Unicodesnowman/ProtectTest')

        with self.subTest(test='anInvalidType'), \
            self.assertRaisesRegex(APIError,
                                   'Invalid protection type "anInvalidType"'):
            site.protect(protections={'anInvalidType': 'sysop'},
                         page=page, reason='Pywikibot unit test')

        with self.subTest(test='anInvalidLevel'), \
                self.assertRaisesRegex(Error, 'Invalid protection level'):
            site.protect(protections={'edit': 'anInvalidLevel'},
                         page=page, reason='Pywikibot unit test')

    def test_delete(self) -> None:
        """Test the site.delete() and site.undelete() methods."""
        site = self.get_site()
        p = pywikibot.Page(site, 'User:Unicodesnowman/DeleteTestSite')
        # Verify state
        if not p.exists():
            site.undelete(p, 'pywikibot unit tests')

        site.delete(p, reason='pywikibot unit tests')
        with self.assertRaises(NoPageError):
            p.get(force=True)

        site.undelete(p, 'pywikibot unit tests',
                      revisions=['2014-12-21T06:07:47Z',
                                 '2014-12-21T06:07:31Z'])

        revs = list(p.revisions())
        self.assertLength(revs, 2)
        self.assertEqual(revs[0].revid, 219995)
        self.assertEqual(revs[1].revid, 219994)

        site.delete(p, reason='pywikibot unit tests')
        site.undelete(p, 'pywikibot unit tests')
        revs = list(p.revisions())
        self.assertGreater(len(revs), 2)

    def test_revdel_page(self) -> None:
        """Test deleting and undeleting page revisions."""
        site = self.get_site()
        # Verify state
        site.deleterevs('revision', ids=[219993, 219994], hide='',
                        show='content|comment|user',
                        reason='pywikibot unit tests')

        # Single revision
        site.deleterevs('revision', '219994', hide='user',
                        reason='pywikibot unit tests')

        p1 = pywikibot.Page(site, 'User:Unicodesnowman/DeleteTestSite')
        revs = list(p1.revisions())
        for rev in revs:
            if rev['revid'] != 219994:
                continue
            self.assertTrue(rev['userhidden'])

        # Multiple revisions
        site.deleterevs('revision', '219993|219994', hide='comment',
                        reason='pywikibot unit tests')

        p2 = pywikibot.Page(site, 'User:Unicodesnowman/DeleteTestSite')
        revs = list(p2.revisions())
        for rev in revs:
            if rev['revid'] != 219994:
                continue
            self.assertTrue(rev['userhidden'])
            self.assertTrue(rev['commenthidden'])

        # Concurrently show and hide
        site.deleterevs('revision', ['219993', '219994'], hide='user|content',
                        show='comment', reason='pywikibot unit tests')

        p3 = pywikibot.Page(site, 'User:Unicodesnowman/DeleteTestSite')
        revs = list(p3.revisions())
        for rev in revs:
            if rev['revid'] == 219993:
                self.assertTrue(rev['userhidden'])
            elif rev['revid'] == 219994:
                self.assertFalse(rev['commenthidden'])

        # Cleanup
        site.deleterevs('revision', [219993, 219994],
                        show='content|comment|user',
                        reason='pywikibot unit tests')

    @unittest.expectedFailure  # T367309
    def test_revdel_file(self) -> None:
        """Test deleting and undeleting file revisions."""
        site = pywikibot.Site('test')

        # Verify state
        site.deleterevs('oldimage', [20210314184415, 20210314184430],
                        show='content|comment|user',
                        reason='pywikibot unit tests',
                        target='File:T276726.png')

        # Single revision
        site.deleterevs('oldimage', '20210314184415', hide='user', show='',
                        reason='pywikibot unit tests',
                        target='File:T276726.png')

        ts1 = pywikibot.Timestamp(2021, 3, 14, 18, 43, 57)
        ts2 = pywikibot.Timestamp(2021, 3, 14, 18, 44, 17)

        fp1 = pywikibot.FilePage(site, 'File:T276726.png')
        site.loadimageinfo(fp1, history=True)
        for v in fp1._file_revisions.values():
            if v['timestamp'] == ts1:
                self.assertHasAttr(v, 'userhidden')

        # Multiple revisions
        site.deleterevs('oldimage', '20210314184415|20210314184430',
                        hide='comment', reason='pywikibot unit tests',
                        target='File:T276726.png')

        fp2 = pywikibot.FilePage(site, 'File:T276726.png')
        site.loadimageinfo(fp2, history=True)
        for v in fp2._file_revisions.values():
            if v['timestamp'] in (ts1, ts2):
                self.assertHasAttr(v, 'commenthidden')

        # Concurrently show and hide
        site.deleterevs('oldimage', ['20210314184415', '20210314184430'],
                        hide='user|content', show='comment',
                        reason='pywikibot unit tests',
                        target='File:T276726.png')

        fp3 = pywikibot.FilePage(site, 'File:T276726.png')
        site.loadimageinfo(fp3, history=True)
        for v in fp3._file_revisions.values():
            if v['timestamp'] in (ts1, ts2):
                self.assertNotHasAttr(v, 'commenthidden')
                self.assertNotHasAttr(v, 'userhidden')
                self.assertNotHasAttr(v, 'filehidden')

        # Cleanup
        site.deleterevs('oldimage', [20210314184415, 20210314184430],
                        show='content|comment|user',
                        reason='pywikibot unit tests',
                        target='File:T276726.png')

    def test_delete_oldimage(self) -> None:
        """Test deleting and undeleting specific versions of files."""
        site = self.get_site()
        fp = pywikibot.FilePage(site, 'File:T276725.png')

        # Verify state
        gen = site.filearchive(start='T276725.png', end='T276725.pngg')
        fileid = None

        for filearchive in gen:
            fileid = filearchive['id']
            break

        if fileid is not None:
            site.undelete(fp, 'pywikibot unit tests', fileids=[fileid])

        # Delete the older version of file
        hist = fp.get_file_history()
        ts = pywikibot.Timestamp(2021, 3, 8, 2, 38, 57)
        oldimageid = hist[ts]['archivename']

        site.delete(fp, 'pywikibot unit tests', oldimage=oldimageid)

        # Undelete the older revision of file
        gen = site.filearchive(start='T276725.png', end='T276725.pngg')
        fileid = None

        for filearchive in gen:
            fileid = filearchive['id']
            break

        self.assertIsNotNone(fileid)

        site.undelete(fp, 'pywikibot unit tests', fileids=[fileid])


class TestRollbackPage(PatchingTestCase):

    """Test rollbackpage site method."""

    family = 'wikipedia'
    code = 'test'
    login = True

    @staticmethod
    @PatchingTestCase.patched(pywikibot.data.api.Request, '_simulate')
    def _simulate(self, action):
        """Patch api.Request._simulate. Note: self is the Request instance."""
        if action == 'rollback':
            result = {
                'title': self._params['title'][0].title(),
                'summary': self._params.get('summary',
                                            ['Rollback simulation'])[0],
                'last_revid': 381070,
            }
            return {action: result}

        if action and config.simulate and self.write:
            result = {'result': 'Success', 'nochange': ''}
            return {action: result}

        return None

    @classmethod
    def setUpClass(cls):
        """Use sandbox page for tests."""
        super().setUpClass()
        cls.page = pywikibot.Page(cls.site, 'Sandbox')

    def setUp(self):
        """Patch has_right method."""
        super().setUp()
        self.patch(self.site, 'has_right', lambda right: True)

    def test_missing_rights(self):
        """Test missing rollback right."""
        self.patch(self.site, 'has_right', lambda right: False)
        with self.assertRaisesRegex(
            Error,
            rf'User "{self.site.user()}" does not have required user right'
            ' "rollback" on site'
        ):
            self.site.rollbackpage(self.page, pageid=4711)

    def test_exceptions(self):
        """Test rollback exceptions."""
        with self.assertRaisesRegex(
            ValueError,
            "The parameters 'page' and 'pageid' cannot be used together"
        ):
            self.site.rollbackpage(self.page, pageid=4711)

        with self.assertRaisesRegex(
            ValueError,
            r"One of parameters 'page' or 'pageid' is required\."
        ):
            self.site.rollbackpage()

        with self.assertRaisesRegex(
                NoPageError, r"Page -1 \(pageid\) doesn't exist\."):
            self.site.rollbackpage(pageid=-1)

    def test_rollback_simulation(self):
        """Test rollback in simulate mode."""
        result = self.site.rollbackpage(self.page)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['title'], self.page.title())
        self.assertEqual(result['last_revid'], 381070)
        self.assertEqual(result['summary'], 'Rollback simulation')
        result = self.site.rollbackpage(self.page, summary='Rollback test')
        self.assertEqual(result['summary'], 'Rollback test')


class TestUsernameInUsers(DefaultSiteTestCase):

    """Test that the user account can be found in users list."""

    login = True
    cached = True

    def test_username_in_users(self) -> None:
        """Test the site.users() method with bot username."""
        mysite = self.get_site()
        us = list(mysite.users(mysite.user()))
        self.assertLength(us, 1)
        self.assertIsInstance(us[0], dict)


class TestSiteExtensions(WikimediaDefaultSiteTestCase):

    """Test cases for Site extensions."""

    cached = True

    def test_extensions(self) -> None:
        """Test Extensions."""
        mysite = self.get_site()
        # test automatically getting extensions cache
        if 'extensions' in mysite.siteinfo:
            del mysite.siteinfo._cache['extensions']
        self.assertTrue(mysite.has_extension('Disambiguator'))

        # test case-sensitivity
        self.assertFalse(mysite.has_extension('disambiguator'))

        self.assertFalse(mysite.has_extension('ThisExtensionDoesNotExist'))


class TestSiteLoadRevisionsCaching(BasePageLoadRevisionsCachingTestBase,
                                   DefaultSiteTestCase):

    """Test site.loadrevisions() caching."""

    def setup_page(self) -> None:
        """Set up test page."""
        self._page = self.get_mainpage(force=True)

    def test_page_text(self) -> None:
        """Test site.loadrevisions() with Page.text."""
        self._test_page_text()


class TestCommonsSite(TestCase):

    """Test cases for Site methods on Commons."""

    family = 'commons'
    code = 'commons'

    cached = True

    def test_interwiki_forward(self) -> None:
        """Test interwiki forward."""
        self.site = self.get_site()
        self.mainpage = pywikibot.Page(pywikibot.Link('Main Page', self.site))
        # test pagelanglinks on commons,
        # which forwards interwikis to wikipedia
        ll = next(self.site.pagelanglinks(self.mainpage))
        self.assertIsInstance(ll, pywikibot.Link)
        self.assertEqual(ll.site.family.name, 'wikipedia')


class TestWiktionarySite(TestCase):

    """Test Site Object on English Wiktionary."""

    family = 'wiktionary'
    code = 'en'

    cached = True

    def test_namespace_case(self) -> None:
        """Test namespace case."""
        site = self.get_site()

        main_namespace = site.namespaces[0]
        self.assertEqual(main_namespace.case, 'case-sensitive')
        user_namespace = site.namespaces[2]
        self.assertEqual(user_namespace.case, 'first-letter')


class TestNonEnglishWikipediaSite(TestCase):

    """Test Site Object on Nynorsk Wikipedia."""

    family = 'wikipedia'
    code = 'nn'

    cached = True

    def test_namespace_aliases(self) -> None:
        """Test namespace aliases."""
        site = self.get_site()

        namespaces = site.namespaces
        image_namespace = namespaces[6]
        self.assertEqual(image_namespace.custom_name, 'Fil')
        self.assertEqual(image_namespace.canonical_name, 'File')
        self.assertEqual(str(image_namespace), ':File:')
        self.assertEqual(image_namespace.custom_prefix(), ':Fil:')
        self.assertEqual(image_namespace.canonical_prefix(), ':File:')
        self.assertEqual(sorted(image_namespace.aliases), ['Bilde', 'Image'])
        self.assertLength(image_namespace, 4)

        self.assertIsEmpty(namespaces[1].aliases)
        self.assertLength(namespaces[4].aliases, 1)
        self.assertEqual(namespaces[4].aliases[0], 'WP')
        self.assertIn('WP', namespaces[4])


class TestUploadEnabledSite(TestCase):

    """Test Site.is_uploaddisabled."""

    sites = {
        'wikidatatest': {
            'family': 'wikidata',
            'code': 'test',
            'disabled': True,
        },
        'wikipediatest': {
            'family': 'wikipedia',
            'code': 'test',
            'disabled': False,
        }
    }

    login = True

    def test_is_uploaddisabled(self, key) -> None:
        """Test is_uploaddisabled()."""
        site = self.get_site(key)
        self.assertEqual(site.is_uploaddisabled(), self.sites[key]['disabled'])


class TestSametitleSite(TestCase):

    """Test APISite.sametitle on sites with known behaviour."""

    sites = {
        'enwp': {
            'family': 'wikipedia',
            'code': 'en',
        },
        'dewp': {
            'family': 'wikipedia',
            'code': 'de',
        },
        'enwt': {
            'family': 'wiktionary',
            'code': 'en',
        }
    }

    def test_enwp(self) -> None:
        """Test sametitle for enwp."""
        self.assertTrue(self.get_site('enwp').sametitle('Foo', 'foo'))
        self.assertFalse(self.get_site('enwp').sametitle(
            'Template:Test template', 'Template:Test Template'))

    def test_dewp(self) -> None:
        """Test sametitle for dewp."""
        site = self.get_site('dewp')
        self.assertTrue(site.sametitle('Foo', 'foo'))
        self.assertTrue(site.sametitle('Benutzer:Foo', 'User:Foo'))
        self.assertTrue(site.sametitle('Benutzerin:Foo', 'User:Foo'))
        self.assertTrue(site.sametitle('Benutzerin:Foo', 'Benutzer:Foo'))

    def test_enwt(self) -> None:
        """Test sametitle for enwt."""
        self.assertFalse(self.get_site('enwt').sametitle('Foo', 'foo'))

    def test_general(self, code) -> None:
        """Test sametitle."""
        site = self.get_site(code)
        self.assertTrue(site.sametitle('File:Foo', 'Image:Foo'))
        self.assertTrue(site.sametitle(':Foo', 'Foo'))
        self.assertFalse(site.sametitle('User:Foo', 'Foo'))
        self.assertFalse(site.sametitle('User:Foo', 'Project:Foo'))

        self.assertTrue(site.sametitle('Namespace:', 'Namespace:'))

        self.assertFalse(site.sametitle('Invalid:Foo', 'Foo'))
        self.assertFalse(site.sametitle('Invalid1:Foo', 'Invalid2:Foo'))
        self.assertFalse(site.sametitle('Invalid:Foo', ':Foo'))
        self.assertFalse(site.sametitle('Invalid:Foo', 'Invalid:foo'))


class TestLinktrails(TestCase):

    """Test linktrail method."""

    family = 'wikipedia'
    code = 'test'

    def test_has_linktrail(self) -> None:
        """Verify that every code has a linktrail.

        Test all smallest wikis and the others randomly.
        """
        size = 20
        small_wikis = self.site.family.languages_by_size[-size:]
        great_wikis = self.site.family.languages_by_size[:-size]
        great_wikis = random.sample(great_wikis, size)
        # Also test for 'hr' which failed due to T378787
        for code in {'hr', *small_wikis, *great_wikis}:
            site = pywikibot.Site(code, self.family)
            with self.subTest(site=site):
                self.assertIsInstance(site.linktrail(), str)

    def test_linktrails(self) -> None:
        """Test special linktrails.

        This is a subset of the old `family.linktrails` dict.
        """
        linktrails = {
            'ami': '',
            'bug': '[a-z]*',
            'ca': "(?:[a-zàèéíòóúç·ïü]|'(?!'))*",
            'da': '[a-zæøå]*',
            'ext': '[a-záéíóúñ]*',
            'fa': '[ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیآأئؤة‌]*',
            'gu': '[઀-૿]*',
            'he': '[a-zא-ת]*',
            'ii': '',
            'jv': '[a-z]*',
            'kaa': "(?:[a-zıʼ’“»]|'(?!'))*",
            'lez': '[a-zабвгдеёжзийклмнопрстуфхцчшщъыьэюяӀ]*',
            'mai': '[a-zऀ-ॣ०-꣠-ꣿ]*',
            'nds-nl': '[a-zäöüïëéèà]*',
            'or': '[a-z଀-୿]*',
            'pt': '[áâãàéêẽçíòóôõq̃úüűũa-z]*',
            'qu': '[a-záéíóúñ]*',
            'roa-rup': '[a-zăâîşţșțĂÂÎŞŢȘȚ]*',
            'sa': '[a-zऀ-ॣ०-꣠-ꣿ]*',
            'te': '[ఁ-౯]*',
            'uz': '[a-zʻʼ“»]*',
            'vec': '[a-zàéèíîìóòúù]*',
            'wuu': '',
            'xmf': '[a-zაბგდევზთიკლმნოპჟრსტუფქღყშჩცძწჭხჯჰ“»]*',
            'yi': '[a-zא-ת]*',
            'zh': ''
        }
        for code, linktrail in linktrails.items():
            site = pywikibot.Site(code, self.family)
            with self.subTest(site=site):
                self.assertEqual(site.linktrail(), linktrail)


class TestSingleCodeFamilySite(DefaultDrySiteTestCase):

    """Test single code family sites."""

    family = 'i18n'
    code = 'i18n'

    def test_twn(self) -> None:
        """Test translatewiki.net."""
        url = 'translatewiki.net'
        site = self.get_site()
        self.assertEqual(site.code, 'i18n')
        self.assertIsInstance(site.namespaces, Mapping)
        self.assertFalse(site.obsolete)
        self.assertEqual(site.hostname(), url)
        for code in 'en', 'i18n', 'translatewiki':
            self.assertEqual(site.family.hostname(code), url)


class TestSubdomainFamilySite(TestCase):

    """Test subdomain family site."""

    code = 'en'
    family = 'wowwiki'

    def test_wow(self) -> None:
        """Test wowwiki.fandom.com."""
        url = 'wowwiki-archive.fandom.com'
        site = self.site
        self.assertEqual(site.hostname(), url)
        self.assertEqual(site.code, 'en')
        self.assertIsInstance(site.namespaces, Mapping)
        self.assertFalse(site.obsolete)
        self.assertEqual(site.family.hostname('en'), url)

        with self.assertRaises(KeyError):
            site.family.hostname('wow')
        with self.assertRaises(KeyError):
            site.family.hostname('wowwiki')
        with self.assertRaises(UnknownSiteError):
            pywikibot.Site('wowwiki')
        with self.assertRaises(UnknownSiteError):
            pywikibot.Site('ceb', 'wowwiki')


class TestProductionAndTestSite(AlteredDefaultSiteTestCase):

    """Test site without other production sites in its family."""

    sites = {
        'commons': {
            'family': 'commons',
            'code': 'commons',
        },
        'beta': {
            'family': 'commons',
            'code': 'beta',
        },
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata',
        },
        'wikidatatest': {
            'family': 'wikidata',
            'code': 'test',
        },
    }

    def test_commons(self) -> None:
        """Test Wikimedia Commons."""
        site = self.get_site('commons')
        self.assertEqual(site.hostname(), 'commons.wikimedia.org')
        self.assertEqual(site.code, 'commons')
        self.assertIsInstance(site.namespaces, Mapping)
        self.assertFalse(site.obsolete)

        with self.assertRaises(KeyError):
            site.family.hostname('en')

        pywikibot.config.family = 'commons'
        pywikibot.config.mylang = 'de'

        site2 = pywikibot.Site('beta')
        self.assertEqual(site2.hostname(),
                         'commons.wikimedia.beta.wmcloud.org')
        self.assertEqual(site2.code, 'beta')
        self.assertFalse(site2.obsolete)

        with self.assertRaises(UnknownSiteError):
            pywikibot.Site()

    def test_wikidata(self) -> None:
        """Test Wikidata family, with sites for test and production."""
        site = self.get_site('wikidata')
        self.assertEqual(site.hostname(), 'www.wikidata.org')
        self.assertEqual(site.code, 'wikidata')
        self.assertIsInstance(site.namespaces, Mapping)
        self.assertFalse(site.obsolete)

        with self.assertRaises(KeyError):
            site.family.hostname('en')

        pywikibot.config.family = 'wikidata'
        pywikibot.config.mylang = 'en'

        site2 = pywikibot.Site('test')
        self.assertEqual(site2.hostname(), 'test.wikidata.org')
        self.assertEqual(site2.code, 'test')

        # Languages can't be used due to T71255
        with self.assertRaises(UnknownSiteError):
            pywikibot.Site('en', 'wikidata')


class TestSiteProofreadinfo(DefaultSiteTestCase):

    """Test proofreadinfo information."""

    sites = {
        'en-ws': {
            'family': 'wikisource',
            'code': 'en',
        },
        'en-wp': {
            'family': 'wikipedia',
            'code': 'en',
        },
    }

    cached = True

    def test_cache_proofreadinfo_on_site_with_proofreadpage(self) -> None:
        """Test Site._cache_proofreadinfo()."""
        site = self.get_site('en-ws')
        ql_res = {0: 'Without text', 1: 'Not proofread', 2: 'Problematic',
                  3: 'Proofread', 4: 'Validated'}

        site._cache_proofreadinfo()
        self.assertEqual(site.namespaces[106], site.proofread_index_ns)
        self.assertEqual(site.namespaces[104], site.proofread_page_ns)
        self.assertEqual(site.proofread_levels, ql_res)
        self.assertEqual(site.namespaces[106], site.proofread_index_ns)
        del site._proofread_page_ns  # Check that property reloads.
        self.assertEqual(site.namespaces[104], site.proofread_page_ns)

    def test_cache_proofreadinfo_on_site_without_proofreadpage(self) -> None:
        """Test Site._cache_proofreadinfo()."""
        site = self.get_site('en-wp')
        with self.assertRaises(UnknownExtensionError):
            site._cache_proofreadinfo()
        with self.assertRaises(UnknownExtensionError):
            site.proofread_index_ns
        with self.assertRaises(UnknownExtensionError):
            site.proofread_page_ns
        with self.assertRaises(UnknownExtensionError):
            site.proofread_levels


class TestPropertyNames(DefaultSiteTestCase):

    """Test Special:PagesWithProp method."""

    sites = {
        'en-ws': {
            'family': 'wikisource',
            'code': 'en',
        },
        'de-wp': {
            'family': 'wikipedia',
            'code': 'de',
        },
    }

    cached = True

    def test_get_property_names(self, key) -> None:
        """Test get_property_names method."""
        mysite = self.get_site(key)
        pnames = mysite.get_property_names()
        self.assertIsInstance(pnames, list)
        for item in (
            'archivedtalk',
            'defaultsort',
            'disambiguation',
            'displaytitle',
            'expectedUnconnectedPage',
            'expectunusedcategory',
            'expectunusedtemplate',
            'forcetoc',
            'graph-data-sources',
            'hiddencat',
            'index',
            'newsectionlink',
            'noeditsection',
            'nogallery',
            'noindex',
            'nonewsectionlink',
            'notoc',
            'templatedata',
            'toc',
            'unexpectedUnconnectedPage',
            'wikibase-badge-Q17437796',
            'wikibase-badge-Q17437798',
            'wikibase-badge-Q70894304',
            'wikibase_item',
        ):
            with self.subTest(item=item):
                self.assertIn(item, pnames)


class TestPageFromWikibase(DefaultSiteTestCase):

    """Test page_from_repository method."""

    sites = {
        'it-wb': {
            'family': 'wikibooks',
            'code': 'it',
            'result': 'Hello world',
        },
        'de-wp': {
            'family': 'wikipedia',
            'code': 'de',
            'result': 'Hallo-Welt-Programm',
        },
        'en-wp': {
            'family': 'wikipedia',
            'code': 'en',
            'result': '"Hello, World!" program',
        },
    }

    ITEM = 'Q131303'

    def test_page_from_repository(self, key) -> None:
        """Validate page_from_repository."""
        site = self.get_site(key)
        page = site.page_from_repository(self.ITEM)
        self.assertIsInstance(page, pywikibot.Page)
        self.assertEqual(page.title(), self.sites[key]['result'])

    def test_page_from_repository_none(self) -> None:
        """Validate page_from_repository return NoneType."""
        site = pywikibot.Site('pdc', 'wikipedia')
        page = site.page_from_repository(self.ITEM)
        self.assertIsNone(page)


class TestCategoryFromWikibase(DefaultSiteTestCase):

    """Test page_from_repository method."""

    sites = {
        'it-ws': {
            'family': 'wikisource',
            'code': 'it',
            'result': 'Categoria:2016',
        },
        'de-wp': {
            'family': 'wikipedia',
            'code': 'de',
            'result': 'Kategorie:2016',
        },
        'en-wp': {
            'family': 'wikipedia',
            'code': 'en',
            'result': 'Category:2016',
        },
    }

    ITEM = 'Q6939656'

    def test_page_from_repository(self, key) -> None:
        """Validate page_from_repository."""
        site = self.get_site(key)
        page = site.page_from_repository(self.ITEM)
        self.assertIsInstance(page, pywikibot.Category)
        self.assertEqual(page.title(), self.sites[key]['result'])

    def test_page_from_repository_none(self) -> None:
        """Validate page_from_repository return NoneType."""
        site = pywikibot.Site('pdc', 'wikipedia')
        page = site.page_from_repository(self.ITEM)
        self.assertIsNone(page)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
