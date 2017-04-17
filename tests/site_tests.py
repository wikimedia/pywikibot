# -*- coding: utf-8 -*-
"""Tests for the site module."""
#
# (C) Pywikibot team, 2008-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import json
import os
import pickle
import re
import sys

from collections import Iterable, Mapping
from datetime import datetime, timedelta

import pywikibot

from pywikibot import config

from pywikibot.comms import http
from pywikibot.data import api

from pywikibot import async_request, page_put_queue
from pywikibot.tools import (
    MediaWikiVersion,
    PY2,
    StringTypes as basestring,
    UnicodeType as unicode,
)

from tests import unittest_print
from tests.aspects import (
    unittest, TestCase, DeprecationTestCase,
    TestCaseBase,
    DefaultSiteTestCase,
    DefaultDrySiteTestCase,
    WikimediaDefaultSiteTestCase,
    WikidataTestCase,
    DefaultWikidataClientTestCase,
    AlteredDefaultSiteTestCase,
)
from tests.basepage_tests import BasePageLoadRevisionsCachingTestBase
from tests.utils import allowed_failure, allowed_failure_if, entered_loop

if not PY2:
    long = int  # Must be global: T159700


class TokenTestBase(TestCaseBase):

    """Verify token exists before running tests."""

    def setUp(self):
        """Skip test if user does not have token and clear site wallet."""
        super(TokenTestBase, self).setUp()
        mysite = self.get_site()
        ttype = self.token_type
        try:
            token = mysite.tokens[ttype]
        except pywikibot.Error as error_msg:
            self.assertRegex(
                unicode(error_msg),
                "Action '[a-z]+' is not allowed for user .* on .* wiki.")
            self.assertNotIn(self.token_type, self.site.tokens)
            raise unittest.SkipTest(error_msg)

        self.token = token
        self._orig_wallet = self.site.tokens
        self.site.tokens = pywikibot.site.TokenWallet(self.site)

    def tearDown(self):
        """Restore site tokens."""
        self.site.tokens = self._orig_wallet
        super(TokenTestBase, self).tearDown()


class TestSiteObjectDeprecatedFunctions(DefaultSiteTestCase, DeprecationTestCase):

    """Test cases for Site deprecated methods on a live wiki."""

    cached = True

    def test_capitalization(self):
        """Test that the case method is mirroring the siteinfo."""
        self.assertEqual(self.site.case(), self.site.siteinfo['case'])
        self.assertOneDeprecationParts('pywikibot.site.APISite.case',
                                       'siteinfo or Namespace instance')
        self.assertIs(self.site.nocapitalize,
                      self.site.siteinfo['case'] == 'case-sensitive')
        self.assertOneDeprecationParts(
            'pywikibot.site.BaseSite.nocapitalize',
            "APISite.siteinfo['case'] or Namespace.case == 'case-sensitive'")

    def test_live_version(self):
        """Test live_version."""
        mysite = self.get_site()
        ver = mysite.live_version()
        self.assertIsInstance(ver, tuple)
        self.assertTrue(all(isinstance(ver[i], int) for i in (0, 1)))
        self.assertIsInstance(ver[2], basestring)
        self.assertOneDeprecation()

    def test_getcurrenttime(self):
        """Test live_version."""
        self.assertEqual(self.site.getcurrenttime(), self.site.server_time())
        self.assertOneDeprecation()

    def test_siteinfo_normal_call(self):
        """Test calling the Siteinfo without setting dump."""
        if MediaWikiVersion(self.site.version()) < MediaWikiVersion('1.16'):
            raise unittest.SkipTest('requires v1.16+')

        old = self.site.siteinfo('general')
        self.assertIn('time', old)
        self.assertEqual(old, self.site.siteinfo['general'])
        self.assertEqual(self.site.siteinfo('general'), old)
        # Siteinfo always returns copies so it's not possible to directly check
        # if they are the same dict or if they have been rerequested unless the
        # content also changes so force that the content changes
        self.assertNotIn('DUMMY', old)
        self.site.siteinfo._cache['general'][0]['DUMMY'] = 42
        old = self.site.siteinfo('general')
        self.assertIn('DUMMY', old)
        self.assertNotEqual(self.site.siteinfo('general', force=True), old)
        self.assertOneDeprecationParts('Calling siteinfo',
                                       'itself as a dictionary',
                                       4)

    def test_siteinfo_dump(self):
        """Test calling the Siteinfo with dump=True."""
        self.assertIn('statistics', self.site.siteinfo('statistics', dump=True))
        self.assertOneDeprecationParts('Calling siteinfo',
                                       'itself as a dictionary')

    def test_language_method(self):
        """Test if the language method returns the same as the lang property."""
        self.assertEqual(self.site.language(), self.site.lang)
        self.assertOneDeprecation()

    def test_allpages_filterredir_True(self):
        """Test that filterredir set to 'only' is deprecated to True."""
        for page in self.site.allpages(filterredir='only', total=1):
            self.assertTrue(page.isRedirectPage())
        self.assertOneDeprecation()

    def test_allpages_filterredir_False(self):
        """Test that if filterredir's bool is False it's deprecated to False."""
        for page in self.site.allpages(filterredir='', total=1):
            self.assertFalse(page.isRedirectPage())
        self.assertOneDeprecation()

    def test_ns_index(self):
        """Test ns_index."""
        self.assertEqual(self.site.ns_index('MediaWiki'), 8)
        self.assertOneDeprecation()

    def test_namespace_shortcuts(self):
        """Test namespace shortcuts."""
        self.assertEqual(self.site.image_namespace(), self.site.namespace(6))
        self.assertEqual(self.site.mediawiki_namespace(),
                         self.site.namespace(8))
        self.assertEqual(self.site.template_namespace(),
                         self.site.namespace(10))
        self.assertEqual(self.site.category_namespace(),
                         self.site.namespace(14))
        self.assertEqual(self.site.category_namespaces(),
                         list(self.site.namespace(14, all=True)))


class TestSiteDryDeprecatedFunctions(DefaultDrySiteTestCase, DeprecationTestCase):

    """Test cases for Site deprecated methods without a user."""

    def test_namespaces_callable(self):
        """Test that namespaces is callable and returns itself."""
        site = self.get_site()
        self.assertIs(site.namespaces(), site.namespaces)
        self.assertOneDeprecationParts('Calling the namespaces property',
                                       'it directly')

    def test_messages_star(self):
        """Test that fetching all messages is deprecated."""
        # Load all messages and check that '*' is not a valid key.
        self.assertEqual(self.site.mediawiki_messages('*'),
                         {'*': 'dummy entry'})
        self.assertOneDeprecationParts('mediawiki_messages("*")',
                                       'specific messages')
        self.assertEqual(self.site.mediawiki_messages(['hello']),
                         {'hello': 'world'})
        self.assertNoDeprecation()


class TestBaseSiteProperties(TestCase):

    """Test properties for BaseSite."""

    sites = {
        'enwikinews': {
            'family': 'wikinews',
            'code': 'en',
            'result': (),  # To be changed when wikinews will have doc_subpage.
        },
        'enwikibooks': {
            'family': 'wikibooks',
            'code': 'en',
            'result': ('/doc',),
        },
        'enwikiquote': {
            'family': 'wikiquote',
            'code': 'en',
            'result': ('/doc',),
        },
        'enwiktionary': {
            'family': 'wiktionary',
            'code': 'en',
            'result': ('/doc',),
        },
        'enws': {
            'family': 'wikisource',
            'code': 'en',
            'result': ('/doc',),
        },
        'dews': {
            'family': 'wikisource',
            'code': 'de',
            'result': ('/Doku', '/Meta'),
        },
        'commons': {
            'family': 'commons',
            'code': 'commons',
            'result': ('/doc', ),
        },
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata',
            'result': ('/doc', ),
        },
    }

    dry = True

    def test_properties(self, key):
        """Test cases for BaseSite properties."""
        mysite = self.get_site(key)
        self.assertEqual(mysite.doc_subpage, self.sites[key]['result'])


class TestSiteObject(DefaultSiteTestCase):

    """Test cases for Site methods."""

    cached = True

    def testPickleAbility(self):
        """Test pickle ability."""
        mysite = self.get_site()
        mysite_str = pickle.dumps(mysite, protocol=config.pickle_protocol)
        mysite_pickled = pickle.loads(mysite_str)
        self.assertEqual(mysite, mysite_pickled)

    def test_repr(self):
        """Test __repr__."""
        expect = 'Site("{0}", "{1}")'.format(self.code, self.family)
        self.assertStringMethod(str.endswith, repr(self.site), expect)

    def testBaseMethods(self):
        """Test cases for BaseSite methods."""
        mysite = self.get_site()
        self.assertEqual(mysite.family.name, self.family)
        self.assertEqual(mysite.code, self.code)
        self.assertIsInstance(mysite.lang, basestring)
        self.assertEqual(mysite, pywikibot.Site(self.code, self.family))
        self.assertIsInstance(mysite.user(), (basestring, type(None)))
        self.assertEqual(mysite.sitename(),
                         "%s:%s" % (self.family,
                                    self.code))
        self.assertIsInstance(mysite.linktrail(), basestring)
        self.assertIsInstance(mysite.redirect(), basestring)
        try:
            dabcat = mysite.disambcategory()
        except pywikibot.Error as e:
            try:
                self.assertIn('No disambiguation category name found', str(e))
            except AssertionError:
                self.assertIn(
                    'No {repo} qualifier found for disambiguation category '
                    'name in {fam}_family file'.format(
                        repo=mysite.data_repository().family.name,
                        fam=mysite.family.name),
                    str(e))
        else:
            self.assertIsInstance(dabcat, pywikibot.Category)

        foo = unicode(pywikibot.Link("foo", source=mysite))
        if self.site.namespaces[0].case == 'case-sensitive':
            self.assertEqual(foo, '[[foo]]')
        else:
            self.assertEqual(foo, '[[Foo]]')

        self.assertFalse(mysite.isInterwikiLink("foo"))
        self.assertIsInstance(mysite.redirectRegex().pattern, basestring)
        self.assertIsInstance(mysite.category_on_one_line(), bool)
        self.assertTrue(mysite.sametitle("Template:Test", "Template:Test"))
        self.assertTrue(mysite.sametitle("Template: Test", "Template:   Test"))
        self.assertTrue(mysite.sametitle('Test name', 'Test name'))
        self.assertFalse(mysite.sametitle('Test name', 'Test Name'))
        # User, MediaWiki (both since 1.16) and Special are always
        # first-letter (== only first non-namespace letter is case insensitive)
        # See also: https://www.mediawiki.org/wiki/Manual:$wgCapitalLinks
        self.assertTrue(mysite.sametitle("Special:Always", "Special:always"))
        if MediaWikiVersion(mysite.version()) >= MediaWikiVersion('1.16'):
            self.assertTrue(mysite.sametitle('User:Always', 'User:always'))
            self.assertTrue(mysite.sametitle('MediaWiki:Always', 'MediaWiki:always'))

    def testConstructors(self):
        """Test cases for site constructors."""
        if isinstance(self.site.family, pywikibot.family.WikimediaFamily):
            site = self.site
        else:
            site = None
        self.assertEqual(pywikibot.site.APISite.fromDBName('enwiki', site),
                         pywikibot.Site('en', 'wikipedia'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('eswikisource', site),
                         pywikibot.Site('es', 'wikisource'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('dewikinews', site),
                         pywikibot.Site('de', 'wikinews'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('ukwikivoyage', site),
                         pywikibot.Site('uk', 'wikivoyage'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('metawiki', site),
                         pywikibot.Site('meta', 'meta'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('commonswiki', site),
                         pywikibot.Site('commons', 'commons'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('wikidatawiki', site),
                         pywikibot.Site('wikidata', 'wikidata'))

    def testLanguageMethods(self):
        """Test cases for languages() and related methods."""
        mysite = self.get_site()
        langs = mysite.languages()
        self.assertIsInstance(langs, list)
        self.assertIn(mysite.code, langs)
        self.assertIsInstance(mysite.obsolete, bool)
        ipf = mysite.interwiki_putfirst()
        if ipf:  # Not all languages use this
            self.assertIsInstance(ipf, list)
        else:
            self.assertIsNone(ipf)

        for item in mysite.validLanguageLinks():
            self.assertIn(item, langs)
            self.assertIsNone(self.site.namespaces.lookup_name(item))

    def testNamespaceMethods(self):
        """Test cases for methods manipulating namespace names."""
        mysite = self.get_site()
        ns = mysite.namespaces
        self.assertIsInstance(ns, Mapping)
        self.assertTrue(all(x in ns for x in range(0, 16)))
        # built-in namespaces always present
        self.assertIsInstance(mysite.ns_normalize("project"), basestring)
        self.assertTrue(all(isinstance(key, int)
                            for key in ns))
        self.assertTrue(all(isinstance(val, Iterable)
                            for val in ns.values()))
        self.assertTrue(all(isinstance(name, basestring)
                            for val in ns.values()
                            for name in val))
        self.assertTrue(all(isinstance(mysite.namespace(key), basestring)
                            for key in ns))
        self.assertTrue(all(isinstance(mysite.namespace(key, True), Iterable)
                            for key in ns))
        self.assertTrue(all(isinstance(item, basestring)
                            for key in ns
                            for item in mysite.namespace(key, True)))

    def test_user_attributes_return_types(self):
        """Test returned types of user attributes."""
        mysite = self.get_site()
        self.assertIsInstance(mysite.logged_in(), bool)
        self.assertIsInstance(mysite.logged_in(True), bool)
        self.assertIsInstance(mysite.userinfo, dict)

    def test_messages(self):
        """Test MediaWiki: messages."""
        mysite = self.get_site()
        for msg in ('about', 'aboutpage', 'aboutsite', 'accesskey-n-portal'):
            self.assertTrue(mysite.has_mediawiki_message(msg))
            self.assertIsInstance(mysite.mediawiki_message(msg), basestring)
        self.assertFalse(mysite.has_mediawiki_message("nosuchmessage"))
        self.assertRaises(KeyError, mysite.mediawiki_message, "nosuchmessage")

        msg = ('about', 'aboutpage')
        about_msgs = self.site.mediawiki_messages(msg)
        self.assertIsInstance(mysite.mediawiki_messages(msg), dict)
        self.assertTrue(mysite.mediawiki_messages(msg))
        self.assertEqual(len(about_msgs), 2)
        self.assertIn(msg[0], about_msgs)

        # mediawiki_messages must be given a list; using a string will split it
        self.assertRaises(KeyError, self.site.mediawiki_messages, 'about')

        msg = ("nosuchmessage1", "about", "aboutpage", "nosuchmessage")
        self.assertFalse(mysite.has_all_mediawiki_messages(msg))
        self.assertRaises(KeyError, mysite.mediawiki_messages, msg)

        self.assertIsInstance(mysite.server_time(), pywikibot.Timestamp)
        ts = mysite.getcurrenttimestamp()
        self.assertIsInstance(ts, basestring)
        self.assertRegex(ts, r'(19|20)\d\d[0-1]\d[0-3]\d[0-2]\d[0-5]\d[0-5]\d')

        self.assertIsInstance(mysite.months_names, list)
        self.assertEqual(len(mysite.months_names), 12)
        self.assertTrue(all(isinstance(month, tuple)
                            for month in mysite.months_names))
        self.assertTrue(all(len(month) == 2
                            for month in mysite.months_names))

        self.assertEqual(mysite.list_to_text(('pywikibot',)), 'pywikibot')

    def testEnglishSpecificMethods(self):
        """Test Site methods using English specific inputs and outputs."""
        mysite = self.get_site()
        if mysite.lang != 'en':
            raise unittest.SkipTest(
                'English-specific tests not valid on %s' % mysite)

        self.assertEqual(mysite.months_names[4], (u'May', u'May'))
        self.assertEqual(mysite.list_to_text(('Pride', 'Prejudice')), 'Pride and Prejudice')
        self.assertEqual(mysite.list_to_text(('This', 'that', 'the other')),
                         'This, that and the other')

    def testPageMethods(self):
        """Test ApiSite methods for getting page-specific info."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        self.assertIsInstance(mysite.page_exists(mainpage), bool)
        self.assertIsInstance(mysite.page_restrictions(mainpage), dict)
        self.assertIsInstance(mysite.page_can_be_edited(mainpage), bool)
        self.assertIsInstance(mysite.page_isredirect(mainpage), bool)
        if mysite.page_isredirect(mainpage):
            self.assertIsInstance(mysite.getredirtarget(mainpage), pywikibot.Page)
        else:
            self.assertRaises(pywikibot.IsNotRedirectPage,
                              mysite.getredirtarget, mainpage)
        a = list(mysite.preloadpages([mainpage]))
        self.assertEqual(len(a), int(mysite.page_exists(mainpage)))
        if a:
            self.assertEqual(a[0], mainpage)


class TestSiteGenerators(DefaultSiteTestCase):

    """Test cases for Site methods."""

    cached = True

    def test_generator_namespace(self):
        """Test site._generator with namespaces."""
        site = self.get_site()
        gen = site._generator(pywikibot.data.api.PageGenerator,
                              type_arg='backlinks',
                              namespaces=None)
        self.assertNotIn('gblnamespace', gen.request)
        gen = site._generator(pywikibot.data.api.PageGenerator,
                              type_arg='backlinks',
                              namespaces=1)
        self.assertEqual(gen.request['gblnamespace'], [1])

    def testLinkMethods(self):
        """Test site methods for getting links to and from a page."""
        if self.site.family.name == 'wpbeta':
            raise unittest.SkipTest('Test fails on betawiki; T69931')
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        backlinks = set(mysite.pagebacklinks(mainpage, namespaces=[0]))
        # only non-redirects:
        filtered = set(mysite.pagebacklinks(mainpage, namespaces=0,
                                            filterRedirects=False))
        # only redirects:
        redirs = set(mysite.pagebacklinks(mainpage, namespaces=0,
                                          filterRedirects=True))
        # including links to redirect pages (but not the redirects):
        indirect = set(mysite.pagebacklinks(mainpage, namespaces=[0],
                                            followRedirects=True,
                                            filterRedirects=False))
        self.assertEqual(filtered & redirs, set([]))
        self.assertEqual(indirect & redirs, set([]))
        self.assertLessEqual(filtered, indirect)
        self.assertLessEqual(filtered, backlinks)
        self.assertLessEqual(redirs, backlinks)
        self.assertLessEqual(
            backlinks,
            set(self.site.pagebacklinks(mainpage, namespaces=[0, 2])))

        # pagereferences includes both backlinks and embeddedin
        embedded = set(mysite.page_embeddedin(mainpage, namespaces=[0]))
        refs = set(mysite.pagereferences(mainpage, namespaces=[0]))
        self.assertTrue(backlinks.issubset(refs))
        self.assertTrue(embedded.issubset(refs))
        for bl in backlinks:
            self.assertIsInstance(bl, pywikibot.Page)
            self.assertIn(bl, refs)
        for ei in embedded:
            self.assertIsInstance(ei, pywikibot.Page)
            self.assertIn(ei, refs)
        for ref in refs:
            self.assertIn(ref, backlinks | embedded)
        # test embeddedin arguments
        self.assertTrue(embedded.issuperset(
            set(mysite.page_embeddedin(mainpage, filterRedirects=True,
                                       namespaces=[0]))))
        self.assertTrue(embedded.issuperset(
            set(mysite.page_embeddedin(mainpage, filterRedirects=False,
                                       namespaces=[0]))))
        self.assertTrue(embedded.issubset(
            set(mysite.page_embeddedin(mainpage, namespaces=[0, 2]))))
        links = set(mysite.pagelinks(mainpage))
        for pl in links:
            self.assertIsInstance(pl, pywikibot.Page)
        # test links arguments
        # TODO: There have been build failures because the following assertion
        # wasn't true. Bug: T92856
        # Example: https://travis-ci.org/wikimedia/pywikibot-core/jobs/54552081#L505
        namespace_links = set(mysite.pagelinks(mainpage, namespaces=[0, 1]))
        if namespace_links - links:
            unittest_print(
                'FAILURE wrt T92856:\nSym. difference: "{0}"'.format(
                    '", "'.join(
                        '{0}@{1}'.format(link.namespace(),
                                         link.title(withNamespace=False))
                        for link in namespace_links ^ links)))
        self.assertCountEqual(
            set(mysite.pagelinks(mainpage, namespaces=[0, 1])) - links, [])
        for target in mysite.preloadpages(mysite.pagelinks(mainpage,
                                                           follow_redirects=True,
                                                           total=5)):
            self.assertIsInstance(target, pywikibot.Page)
            self.assertFalse(target.isRedirectPage())
        # test pagecategories
        for cat in mysite.pagecategories(mainpage):
            self.assertIsInstance(cat, pywikibot.Category)
            for cm in mysite.categorymembers(cat):
                self.assertIsInstance(cat, pywikibot.Page)
        # test pageimages
        self.assertTrue(all(isinstance(im, pywikibot.FilePage)
                            for im in mysite.pageimages(mainpage)))
        # test pagetemplates
        self.assertTrue(all(isinstance(te, pywikibot.Page)
                            for te in mysite.pagetemplates(mainpage)))
        self.assertTrue(set(mysite.pagetemplates(mainpage)).issuperset(
                        set(mysite.pagetemplates(mainpage, namespaces=[10]))))
        # test pagelanglinks
        for ll in mysite.pagelanglinks(mainpage):
            self.assertIsInstance(ll, pywikibot.Link)
        # test page_extlinks
        self.assertTrue(all(isinstance(el, basestring)
                            for el in mysite.page_extlinks(mainpage)))

    def test_allpages(self):
        """Test the site.allpages() method."""
        mysite = self.get_site()
        fwd = list(mysite.allpages(total=10))
        self.assertLessEqual(len(fwd), 10)
        for page in fwd:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
        rev = list(mysite.allpages(reverse=True, start="Aa", total=12))
        self.assertLessEqual(len(rev), 12)
        for page in rev:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertLessEqual(page.title(), "Aa")
        for page in mysite.allpages(start="Py", total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertGreaterEqual(page.title(), "Py")
        for page in mysite.allpages(prefix="Pre", total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title().startswith("Pre"))
        for page in mysite.allpages(namespace=1, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 1)
        for page in mysite.allpages(filterredir=True, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.isRedirectPage())
        for page in mysite.allpages(filterredir=False, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertFalse(page.isRedirectPage())

    def test_allpages_langlinks_enabled(self):
        """Test allpages with langlinks enabled."""
        mysite = self.get_site()
        for page in mysite.allpages(
                filterlanglinks=True, total=3, namespace=4):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 4)
            self.assertNotEqual(page.langlinks(), [])

    def test_allpages_langlinks_disabled(self):
        """Test allpages with langlinks disabled."""
        mysite = self.get_site()
        for page in mysite.allpages(filterlanglinks=False, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertEqual(page.langlinks(), [])

    def test_allpages_pagesize(self):
        """Test allpages with page maxsize parameter."""
        mysite = self.get_site()
        for page in mysite.allpages(minsize=100, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertGreaterEqual(len(page.text.encode(mysite.encoding())),
                                    100)
        for page in mysite.allpages(maxsize=200, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            if (len(page.text.encode(mysite.encoding())) > 200 and
                    mysite.data_repository() == mysite):
                unittest_print(
                    '{0}.text is > 200 bytes while raw JSON is <= 200'.format(
                        page))
                continue
            self.assertLessEqual(len(page.text.encode(mysite.encoding())),
                                 200)

    def test_allpages_protection(self):
        """Test allpages with protect_type parameter."""
        mysite = self.get_site()
        for page in mysite.allpages(protect_type="edit", total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertIn("edit", page._protection)
        for page in mysite.allpages(protect_type="edit",
                                    protect_level="sysop", total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertIn("edit", page._protection)
            self.assertIn("sysop", page._protection["edit"])

    def testAllLinks(self):
        """Test the site.alllinks() method."""
        if self.site.family.name == 'wsbeta':
            raise unittest.SkipTest('Test fails on betawiki; T69931')

        mysite = self.get_site()
        fwd = list(mysite.alllinks(total=10))
        self.assertLessEqual(len(fwd), 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page) for link in fwd))
        uniq = list(mysite.alllinks(total=10, unique=True))
        self.assertTrue(all(link in uniq for link in fwd))
        for page in mysite.alllinks(start="Link", total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 0)
            self.assertGreaterEqual(page.title(), "Link")
        for page in mysite.alllinks(prefix="Fix", total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title().startswith("Fix"))
        for page in mysite.alllinks(namespace=1, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 1)
        for page in mysite.alllinks(start="From", namespace=4, fromids=True,
                                    total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertGreaterEqual(page.title(withNamespace=False), "From")
            self.assertTrue(hasattr(page, "_fromid"))
        errgen = mysite.alllinks(unique=True, fromids=True)
        self.assertRaises(pywikibot.Error, next, errgen)

    def testAllCategories(self):
        """Test the site.allcategories() method."""
        mysite = self.get_site()
        ac = list(mysite.allcategories(total=10))
        self.assertLessEqual(len(ac), 10)
        self.assertTrue(all(isinstance(cat, pywikibot.Category)
                            for cat in ac))
        for cat in mysite.allcategories(total=5, start="Abc"):
            self.assertIsInstance(cat, pywikibot.Category)
            self.assertGreaterEqual(cat.title(withNamespace=False), "Abc")
        for cat in mysite.allcategories(total=5, prefix="Def"):
            self.assertIsInstance(cat, pywikibot.Category)
            self.assertTrue(cat.title(withNamespace=False).startswith("Def"))
        # Bug T17985 - reverse and start combined; fixed in v 1.14
        for cat in mysite.allcategories(total=5, start="Hij", reverse=True):
            self.assertIsInstance(cat, pywikibot.Category)
            self.assertLessEqual(cat.title(withNamespace=False), "Hij")

    def test_allusers(self):
        """Test the site.allusers() method."""
        mysite = self.get_site()
        au = list(mysite.allusers(total=10))
        self.assertLessEqual(len(au), 10)
        for user in au:
            self.assertIsInstance(user, dict)
            self.assertIn("name", user)
            self.assertIn("editcount", user)
            self.assertIn("registration", user)

    def test_allusers_with_start(self):
        """Test the site.allusers(start=..) method."""
        mysite = self.get_site()
        for user in mysite.allusers(start="B", total=5):
            self.assertIsInstance(user, dict)
            self.assertIn("name", user)
            self.assertGreaterEqual(user["name"], "B")
            self.assertIn("editcount", user)
            self.assertIn("registration", user)

    def test_allusers_with_prefix(self):
        """Test the site.allusers(prefix=..) method."""
        mysite = self.get_site()
        for user in mysite.allusers(prefix="C", total=5):
            self.assertIsInstance(user, dict)
            self.assertIn("name", user)
            self.assertTrue(user["name"].startswith("C"))
            self.assertIn("editcount", user)
            self.assertIn("registration", user)

    def _test_allusers_with_group(self):
        """Test the site.allusers(group=..) method."""
        mysite = self.get_site()
        for user in mysite.allusers(prefix="D", group="bot", total=5):
            self.assertIsInstance(user, dict)
            self.assertIn("name", user)
            self.assertTrue(user["name"].startswith("D"))
            self.assertIn("editcount", user)
            self.assertIn("registration", user)
            self.assertIn('groups' in user)
            self.assertIn('sysop' in user['groups'])

    def testAllImages(self):
        """Test the site.allimages() method."""
        mysite = self.get_site()
        ai = list(mysite.allimages(total=10))
        self.assertLessEqual(len(ai), 10)
        self.assertTrue(all(isinstance(image, pywikibot.FilePage)
                            for image in ai))
        for impage in mysite.allimages(start="Ba", total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertGreaterEqual(impage.title(withNamespace=False), "Ba")
        # Bug T17985 - reverse and start combined; fixed in v 1.14
        for impage in mysite.allimages(start="Da", reverse=True, total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertLessEqual(impage.title(withNamespace=False), "Da")
        for impage in mysite.allimages(prefix="Ch", total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertTrue(impage.title(withNamespace=False).startswith("Ch"))
        for impage in mysite.allimages(minsize=100, total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertGreaterEqual(impage.latest_file_info["size"], 100)
        for impage in mysite.allimages(maxsize=2000, total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertLessEqual(impage.latest_file_info["size"], 2000)

    def test_newfiles(self):
        """Test the site.newfiles() method."""
        my_site = self.get_site()
        the_list = list(my_site.newfiles(total=10))
        self.assertLessEqual(len(the_list), 10)
        self.assertTrue(all(isinstance(tup, tuple) and len(tup) == 4
                            for tup in the_list))
        self.assertTrue(all(isinstance(tup[0], pywikibot.FilePage) for tup in the_list))
        self.assertTrue(all(isinstance(tup[1], pywikibot.Timestamp) for tup in the_list))
        self.assertTrue(all(isinstance(tup[2], unicode) for tup in the_list))
        self.assertTrue(all(isinstance(tup[3], unicode) for tup in the_list))

    def test_longpages(self):
        """Test the site.longpages() method."""
        mysite = self.get_site()
        longpages = list(mysite.longpages(total=10))

        # Make sure each object returned by site.longpages() is
        # a tuple of a Page object and an int
        self.assertTrue(all(isinstance(tup, tuple) and len(tup) == 2) for tup in longpages)
        self.assertTrue(all(isinstance(tup[0], pywikibot.Page) for tup in longpages))
        self.assertTrue(all(isinstance(tup[1], int) for tup in longpages))

    def test_shortpages(self):
        """Test the site.shortpages() method."""
        mysite = self.get_site()
        shortpages = list(mysite.shortpages(total=10))

        # Make sure each object returned by site.shortpages() is
        # a tuple of a Page object and an int
        self.assertTrue(all(isinstance(tup, tuple) and len(tup) == 2) for tup in shortpages)
        self.assertTrue(all(isinstance(tup[0], pywikibot.Page) for tup in shortpages))
        self.assertTrue(all(isinstance(tup[1], int) for tup in shortpages))

    def test_ancientpages(self):
        """Test the site.ancientpages() method."""
        mysite = self.get_site()
        ancientpages = list(mysite.ancientpages(total=10))

        # Make sure each object returned by site.ancientpages() is
        # a tuple of a Page object and a Timestamp object
        self.assertTrue(all(isinstance(tup, tuple) and len(tup) == 2) for tup in ancientpages)
        self.assertTrue(all(isinstance(tup[0], pywikibot.Page) for tup in ancientpages))
        self.assertTrue(all(isinstance(tup[1], pywikibot.Timestamp) for tup in ancientpages))

    def test_unwatchedpages(self):
        """Test the site.unwatchedpages() method."""
        mysite = self.get_site()
        try:
            unwatchedpages = list(mysite.unwatchedpages(total=10))
        except api.APIError as error:
            if error.code in ('specialpage-cantexecute',
                              'gqpspecialpage-cantexecute'):
                # User must have correct permissions to use Special:UnwatchedPages
                raise unittest.SkipTest(error)
            raise

        # Make sure each object returned by site.unwatchedpages() is a Page object
        self.assertTrue(all(isinstance(p, pywikibot.Page) for p in unwatchedpages))

    def testBlocks(self):
        """Test the site.blocks() method."""
        mysite = self.get_site()
        props = ("id", "by", "timestamp", "expiry", "reason")
        bl = list(mysite.blocks(total=10))
        self.assertLessEqual(len(bl), 10)
        for block in bl:
            self.assertIsInstance(block, dict)
            for prop in props:
                self.assertIn(prop, block)
        # timestamps should be in descending order
        timestamps = [block['timestamp'] for block in bl]
        for t in range(1, len(timestamps)):
            self.assertLessEqual(timestamps[t], timestamps[t - 1])

        b2 = list(mysite.blocks(total=10, reverse=True))
        self.assertLessEqual(len(b2), 10)
        for block in b2:
            self.assertIsInstance(block, dict)
            for prop in props:
                self.assertIn(prop, block)
        # timestamps should be in ascending order
        timestamps = [block['timestamp'] for block in b2]
        for t in range(1, len(timestamps)):
            self.assertGreaterEqual(timestamps[t], timestamps[t - 1])

        for block in mysite.blocks(
                starttime=pywikibot.Timestamp.fromISOformat('2008-07-01T00:00:01Z'),
                total=5):
            self.assertIsInstance(block, dict)
            for prop in props:
                self.assertIn(prop, block)
        for block in mysite.blocks(
                endtime=pywikibot.Timestamp.fromISOformat('2008-07-31T23:59:59Z'),
                total=5):
            self.assertIsInstance(block, dict)
            for prop in props:
                self.assertIn(prop, block)
        for block in mysite.blocks(
                starttime=pywikibot.Timestamp.fromISOformat('2008-08-02T00:00:01Z'),
                endtime=pywikibot.Timestamp.fromISOformat("2008-08-02T23:59:59Z"),
                reverse=True, total=5):
            self.assertIsInstance(block, dict)
            for prop in props:
                self.assertIn(prop, block)
        for block in mysite.blocks(
                starttime=pywikibot.Timestamp.fromISOformat('2008-08-03T23:59:59Z'),
                endtime=pywikibot.Timestamp.fromISOformat("2008-08-03T00:00:01Z"),
                total=5):
            self.assertIsInstance(block, dict)
            for prop in props:
                self.assertIn(prop, block)
        # starttime earlier than endtime
        self.assertRaises(pywikibot.Error, mysite.blocks, total=5,
                          starttime=pywikibot.Timestamp.fromISOformat("2008-08-03T00:00:01Z"),
                          endtime=pywikibot.Timestamp.fromISOformat('2008-08-03T23:59:59Z'))
        # reverse: endtime earlier than starttime
        self.assertRaises(pywikibot.Error, mysite.blocks,
                          starttime=pywikibot.Timestamp.fromISOformat("2008-08-03T23:59:59Z"),
                          endtime=pywikibot.Timestamp.fromISOformat('2008-08-03T00:00:01Z'),
                          reverse=True, total=5)
        for block in mysite.blocks(users='80.100.22.71', total=5):
            self.assertIsInstance(block, dict)
            self.assertEqual(block['user'], '80.100.22.71')

    def testExturlusage(self):
        """Test the site.exturlusage() method."""
        mysite = self.get_site()
        url = "www.google.com"
        eu = list(mysite.exturlusage(url, total=10))
        self.assertLessEqual(len(eu), 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page)
                            for link in eu))
        for link in mysite.exturlusage(url, namespaces=[2, 3], total=5):
            self.assertIsInstance(link, pywikibot.Page)
            self.assertIn(link.namespace(), (2, 3))

    def test_lock_page(self):
        """Test the site.lock_page() and site.unlock_page() method."""
        site = self.get_site()
        p1 = pywikibot.Page(site, u'Foo')

        site.lock_page(page=p1, block=True)
        self.assertRaises(pywikibot.site.PageInUse, site.lock_page, page=p1, block=False)
        site.unlock_page(page=p1)
        # verify it's unlocked
        site.lock_page(page=p1, block=False)
        site.unlock_page(page=p1)

    def test_protectedpages_create(self):
        """Test that protectedpages returns protected page titles."""
        if MediaWikiVersion(self.site.version()) < MediaWikiVersion('1.15'):
            raise unittest.SkipTest('requires v1.15+')

        pages = list(self.get_site().protectedpages(type='create', total=10))
        for page in pages:
            self.assertFalse(page.exists())
        self.assertLessEqual(len(pages), 10)

    def test_protectedpages_edit(self):
        """Test that protectedpages returns protected pages."""
        site = self.get_site()
        pages = list(site.protectedpages(type='edit', total=10))
        for page in pages:
            self.assertTrue(page.exists())
            self.assertIn('edit', page.protection())
        self.assertLessEqual(len(pages), 10)

    def test_protectedpages_edit_level(self):
        """Test protectedpages protection level."""
        site = self.get_site()
        levels = set()
        all_levels = site.protection_levels().difference([''])
        for level in all_levels:
            if list(site.protectedpages(type='edit', level=level, total=1)):
                levels.add(level)
        if not levels:
            raise unittest.SkipTest('The site "{0}" has no protected pages in '
                                    'main namespace.'.format(site))
        # select one level which won't yield all pages from above
        level = next(iter(levels))
        if len(levels) == 1:
            # if only one level found, then use any other except that
            level = next(iter(all_levels.difference([level])))
        invalid_levels = all_levels.difference([level])
        pages = list(site.protectedpages(type='edit', level=level, total=10))
        for page in pages:
            self.assertTrue(page.exists())
            self.assertIn('edit', page.protection())
            self.assertEqual(page.protection()['edit'][0], level)
            self.assertNotIn(page.protection()['edit'][0], invalid_levels)
        self.assertLessEqual(len(pages), 10)

    def test_unconnected(self):
        """Test that the ItemPage returned raises NoPage."""
        if not self.site.data_repository():
            raise unittest.SkipTest('Site is not using a Wikibase repository')
        if self.site.hostname() == 'test.wikipedia.org':
            raise unittest.SkipTest('test.wikipedia is misconfigured; T85358')
        cnt = 0
        start_time = datetime.now() - timedelta(minutes=5)
        # Pages which have been connected recently may still be reported as
        # unconnected. So try on an version that is a few minutes older if the
        # tested site appears as a sitelink.
        for page in self.site.unconnected_pages(total=5):
            try:
                item = pywikibot.ItemPage.fromPage(page)
            except pywikibot.NoPage:
                pass
            else:
                revisions = list(item.revisions(total=1, starttime=start_time,
                                                content=True))
                if revisions:
                    sitelinks = json.loads(revisions[0].text)['sitelinks']
                    self.assertNotIn(
                        self.site.dbName(), sitelinks,
                        'Page "{0}" is connected to a Wikibase '
                        'repository'.format(page.title()))
            cnt += 1
        self.assertLessEqual(cnt, 5)

    def test_pages_with_property(self):
        """Test pages_with_property method."""
        if MediaWikiVersion(self.site.version()) < MediaWikiVersion('1.21'):
            raise unittest.SkipTest('requires v1.21+')
        mysite = self.get_site()
        pnames = mysite.get_property_names()
        for item in ('defaultsort', 'disambiguation', 'displaytitle',
                     'hiddencat', 'invalid_property'):
            if item in pnames:
                for page in mysite.pages_with_property(item, total=5):
                    self.assertIsInstance(page, pywikibot.Page)
                    self.assertTrue(mysite.page_exists(page))
                    if item == 'disambiguation':
                        self.assertTrue(page.isDisambig)
            else:
                with self.assertRaises(NotImplementedError):
                    mysite.pages_with_property(item)
                    self.fail(
                        'NotImplementedError not raised for {0}'.format(item))


class TestImageUsage(DefaultSiteTestCase):

    """Test cases for Site.imageusage method."""

    cached = True

    @property
    def imagepage(self):
        """Find an image which is used on a page.

        If there are no images included in pages it'll skip all tests.

        Note: This is not implemented as setUpClass which would be invoked
        while initialising all tests, to reduce chance of an error preventing
        all tests from running.
        """
        if hasattr(self.__class__, '_image_page'):
            return self.__class__._image_page

        mysite = self.get_site()
        for page in mysite.allpages(filterredir=False):
            try:
                imagepage = next(iter(page.imagelinks()))  # 1st image of page
            except StopIteration:
                pass
            else:
                break
        else:
            raise unittest.SkipTest("No images on site {0!r}".format(mysite))

        pywikibot.output(u'site_tests.TestImageUsage found %s on %s'
                         % (imagepage, page))

        self.__class__._image_page = imagepage
        return imagepage

    def test_image_usage(self):
        """Test the site.imageusage() method."""
        mysite = self.get_site()
        imagepage = self.imagepage
        iu = list(mysite.imageusage(imagepage, total=10))
        self.assertLessEqual(len(iu), 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page)
                            for link in iu))

    def test_image_usage_in_namespaces(self):
        """Test the site.imageusage() method with namespaces."""
        mysite = self.get_site()
        imagepage = self.imagepage
        for using in mysite.imageusage(imagepage, namespaces=[3, 4], total=5):
            self.assertIsInstance(using, pywikibot.Page)
            self.assertIn(imagepage, list(using.imagelinks()))

    @allowed_failure_if(os.environ.get('TRAVIS', 'false') == 'true')
    def test_image_usage_in_redirects(self):
        """Test the site.imageusage() method on redirects only."""
        mysite = self.get_site()
        imagepage = self.imagepage
        for using in mysite.imageusage(imagepage, filterredir=True, total=5):
            self.assertIsInstance(using, pywikibot.Page)
            self.assertTrue(using.isRedirectPage())

    def test_image_usage_no_redirect_filter(self):
        """Test the site.imageusage() method with redirects."""
        mysite = self.get_site()
        imagepage = self.imagepage
        for using in mysite.imageusage(imagepage, filterredir=False, total=5):
            self.assertIsInstance(using, pywikibot.Page)
            if using.isRedirectPage():
                unittest_print(
                    '{0} is a redirect, although just non-redirects were '
                    'searched. See also T75120'.format(using))
            self.assertFalse(using.isRedirectPage())


class SiteUserTestCase(DefaultSiteTestCase):

    """Test site method using a user."""

    user = True

    def test_methods(self):
        """Test user related methods."""
        mysite = self.get_site()
        self.assertIsInstance(mysite.is_blocked(), bool)
        self.assertIsInstance(mysite.messages(), bool)
        self.assertIsInstance(mysite.has_right("edit"), bool)
        self.assertFalse(mysite.has_right("nonexistent_right"))
        self.assertIsInstance(mysite.has_group("bots"), bool)
        self.assertFalse(mysite.has_group("nonexistent_group"))
        for grp in ("user", "autoconfirmed", "bot", "sysop", "nosuchgroup"):
            self.assertIsInstance(mysite.has_group(grp), bool)
        for rgt in ("read", "edit", "move", "delete", "rollback", "block",
                    "nosuchright"):
            self.assertIsInstance(mysite.has_right(rgt), bool)

    def testLogEvents(self):
        """Test the site.logevents() method."""
        mysite = self.get_site()
        for entry in mysite.logevents(user=mysite.user(), total=3):
            self.assertEqual(entry.user(), mysite.user())


class TestLogEvents(DefaultSiteTestCase):

    """Test logevents methods."""

    def test_logevents(self):
        """Test logevents method."""
        mysite = self.get_site()
        le = list(mysite.logevents(total=10))
        self.assertLessEqual(len(le), 10)
        self.assertTrue(all(isinstance(entry, pywikibot.logentries.LogEntry)
                            for entry in le))
        for typ in ("block", "protect", "rights", "delete", "upload",
                    "move", "import", "patrol", "merge"):
            for entry in mysite.logevents(logtype=typ, total=3):
                self.assertEqual(entry.type(), typ)

    def test_logevents_mainpage(self):
        """Test logevents method on the main page."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        for entry in mysite.logevents(page=mainpage, total=3):
            self.assertEqual(entry.page().title(), mainpage.title())
            self.assertEqual(entry.page(), mainpage)

    def test_logevents_timestamp(self):
        """Test logevents method."""
        mysite = self.get_site()
        for entry in mysite.logevents(
                start=pywikibot.Timestamp.fromISOformat('2008-09-01T00:00:01Z'), total=5):
            self.assertIsInstance(entry, pywikibot.logentries.LogEntry)
            self.assertLessEqual(str(entry.timestamp()), "2008-09-01T00:00:01Z")
        for entry in mysite.logevents(
                end=pywikibot.Timestamp.fromISOformat('2008-09-02T23:59:59Z'), total=5):
            self.assertIsInstance(entry, pywikibot.logentries.LogEntry)
            self.assertGreaterEqual(str(entry.timestamp()), "2008-09-02T23:59:59Z")
        for entry in mysite.logevents(
                start=pywikibot.Timestamp.fromISOformat('2008-02-02T00:00:01Z'),
                end=pywikibot.Timestamp.fromISOformat("2008-02-02T23:59:59Z"),
                reverse=True, total=5):
            self.assertIsInstance(entry, pywikibot.logentries.LogEntry)
            self.assertTrue(
                "2008-02-02T00:00:01Z" <= str(entry.timestamp()) <= "2008-02-02T23:59:59Z")
        for entry in mysite.logevents(
                start=pywikibot.Timestamp.fromISOformat('2008-02-03T23:59:59Z'),
                end=pywikibot.Timestamp.fromISOformat("2008-02-03T00:00:01Z"),
                total=5):
            self.assertIsInstance(entry, pywikibot.logentries.LogEntry)
            self.assertTrue(
                "2008-02-03T00:00:01Z" <= str(entry.timestamp()) <= "2008-02-03T23:59:59Z")
        # starttime earlier than endtime
        self.assertRaises(pywikibot.Error, mysite.logevents,
                          start=pywikibot.Timestamp.fromISOformat("2008-02-03T00:00:01Z"),
                          end=pywikibot.Timestamp.fromISOformat("2008-02-03T23:59:59Z"), total=5)
        # reverse: endtime earlier than starttime
        self.assertRaises(pywikibot.Error, mysite.logevents,
                          start=pywikibot.Timestamp.fromISOformat("2008-02-03T23:59:59Z"),
                          end=pywikibot.Timestamp.fromISOformat('2008-02-03T00:00:01Z'),
                          reverse=True, total=5)


class TestLogPages(DefaultSiteTestCase, DeprecationTestCase):

    """Test logpages methods."""

    def test_logpages(self):
        """Test the deprecated site.logpages() method."""
        le = list(self.site.logpages(number=10))
        self.assertOneDeprecation()
        self.assertLessEqual(len(le), 10)
        for entry in le:
            self.assertIsInstance(entry, tuple)
            self.assertIsInstance(entry[0], pywikibot.Page)
            self.assertIsInstance(entry[1], basestring)
            self.assertIsInstance(
                entry[2], long if PY2 and entry[2] > sys.maxint else int)
            self.assertIsInstance(entry[3], basestring)

    def test_logpages_dump(self):
        """Test the deprecated site.logpages() method using dump mode."""
        le = list(self.site.logpages(number=10, dump=True))
        self.assertOneDeprecation()
        self.assertLessEqual(len(le), 10)
        for entry in le:
            self.assertIsInstance(entry, dict)
            self.assertIn('title', entry)


class TestRecentChanges(DefaultSiteTestCase):

    """Test recentchanges method."""

    @classmethod
    def setUpClass(cls):
        """Test up test class."""
        super(TestRecentChanges, cls).setUpClass()
        mysite = cls.get_site()
        try:
            # 1st image on main page
            imagepage = next(iter(mysite.allimages()))
        except StopIteration:
            unittest_print('No images on site {0!r}'.format(mysite))
            imagepage = None
        cls.imagepage = imagepage

    def test_basic(self):
        """Test the site.recentchanges() method."""
        mysite = self.site
        rc = list(mysite.recentchanges(total=10))
        self.assertLessEqual(len(rc), 10)
        self.assertTrue(all(isinstance(change, dict)
                            for change in rc))

    def test_time_range(self):
        """Test the site.recentchanges() method with start/end."""
        mysite = self.site
        for change in mysite.recentchanges(
                start=pywikibot.Timestamp.fromISOformat("2008-10-01T01:02:03Z"),
                total=5):
            self.assertIsInstance(change, dict)
            self.assertLessEqual(change['timestamp'], "2008-10-01T01:02:03Z")
        for change in mysite.recentchanges(
                end=pywikibot.Timestamp.fromISOformat('2008-04-01T02:03:04Z'),
                total=5):
            self.assertIsInstance(change, dict)
            self.assertGreaterEqual(change['timestamp'], "2008-10-01T02:03:04Z")
        for change in mysite.recentchanges(
                start=pywikibot.Timestamp.fromISOformat('2008-10-01T03:05:07Z'),
                total=5, reverse=True):
            self.assertIsInstance(change, dict)
            self.assertGreaterEqual(change['timestamp'], "2008-10-01T03:05:07Z")
        for change in mysite.recentchanges(
                end=pywikibot.Timestamp.fromISOformat('2008-10-01T04:06:08Z'),
                total=5, reverse=True):
            self.assertIsInstance(change, dict)
            self.assertLessEqual(change['timestamp'], "2008-10-01T04:06:08Z")
        for change in mysite.recentchanges(
                start=pywikibot.Timestamp.fromISOformat('2008-10-03T11:59:59Z'),
                end=pywikibot.Timestamp.fromISOformat("2008-10-03T00:00:01Z"),
                total=5):
            self.assertIsInstance(change, dict)
            self.assertTrue(
                "2008-10-03T00:00:01Z" <= change['timestamp'] <= "2008-10-03T11:59:59Z")
        for change in mysite.recentchanges(
                start=pywikibot.Timestamp.fromISOformat('2008-10-05T06:00:01Z'),
                end=pywikibot.Timestamp.fromISOformat("2008-10-05T23:59:59Z"),
                reverse=True, total=5):
            self.assertIsInstance(change, dict)
            self.assertTrue(
                "2008-10-05T06:00:01Z" <= change['timestamp'] <= "2008-10-05T23:59:59Z")
        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.recentchanges,
                          start="2008-02-03T00:00:01Z",
                          end="2008-02-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.recentchanges,
                          start=pywikibot.Timestamp.fromISOformat("2008-02-03T23:59:59Z"),
                          end=pywikibot.Timestamp.fromISOformat('2008-02-03T00:00:01Z'),
                          reverse=True, total=5)

    def test_ns_file(self):
        """Test the site.recentchanges() method with File: and File talk:."""
        if self.site.code == 'wikidata':
            raise unittest.SkipTest(
                'MediaWiki bug frequently occurring on Wikidata. T101502')
        mysite = self.site
        for change in mysite.recentchanges(namespaces=[6, 7], total=5):
            self.assertIsInstance(change, dict)
            self.assertIn('title', change)
            self.assertIn('ns', change)
            title = change['title']
            self.assertIn(":", title)
            prefix = title[:title.index(":")]
            self.assertIn(self.site.namespaces.lookup_name(prefix).id, [6, 7])
            self.assertIn(change["ns"], [6, 7])

    def test_pagelist(self):
        """Test the site.recentchanges() with pagelist deprecated MW 1.14."""
        mysite = self.site
        mainpage = self.get_mainpage()
        imagepage = self.imagepage
        if MediaWikiVersion(mysite.version()) <= MediaWikiVersion("1.14"):
            pagelist = [mainpage]
            if imagepage:
                pagelist += [imagepage]
            titlelist = set(page.title() for page in pagelist)
            for change in mysite.recentchanges(pagelist=pagelist,
                                               total=5):
                self.assertIsInstance(change, dict)
                self.assertIn("title", change)
                self.assertIn(change["title"], titlelist)

    def test_changetype(self):
        """Test the site.recentchanges() with changetype."""
        mysite = self.site
        for typ in ("edit", "new", "log"):
            for change in mysite.recentchanges(changetype=typ, total=5):
                self.assertIsInstance(change, dict)
                self.assertIn("type", change)
                self.assertEqual(change["type"], typ)

    def test_flags(self):
        """Test the site.recentchanges() with boolean flags."""
        mysite = self.site
        for change in mysite.recentchanges(showMinor=True, total=5):
            self.assertIsInstance(change, dict)
            self.assertIn("minor", change)
        for change in mysite.recentchanges(showMinor=False, total=5):
            self.assertIsInstance(change, dict)
            self.assertNotIn("minor", change)
        for change in mysite.recentchanges(showBot=True, total=5):
            self.assertIsInstance(change, dict)
            self.assertIn("bot", change)
        for change in mysite.recentchanges(showBot=False, total=5):
            self.assertIsInstance(change, dict)
            self.assertNotIn("bot", change)
        for change in mysite.recentchanges(showAnon=True, total=5):
            self.assertIsInstance(change, dict)
        for change in mysite.recentchanges(showAnon=False, total=5):
            self.assertIsInstance(change, dict)
        for change in mysite.recentchanges(showRedirects=True, total=5):
            self.assertIsInstance(change, dict)
            self.assertIn("redirect", change)
        for change in mysite.recentchanges(showRedirects=False, total=5):
            self.assertIsInstance(change, dict)
            self.assertNotIn("redirect", change)

    def test_tag_filter(self):
        """Test the site.recentchanges() with tag filter."""
        mysite = self.site
        for tag in ('visualeditor', 'mobile edit'):
            for change in mysite.recentchanges(tag=tag, total=5):
                self.assertIsInstance(change, dict)
                self.assertIn('tags', change)
                self.assertIsInstance(change['tags'], list)
                self.assertIn(tag, change['tags'])


class TestUserRecentChanges(DefaultSiteTestCase):

    """Test recentchanges method requiring a user."""

    user = True

    def test_patrolled(self):
        """Test the site.recentchanges() with patrolled boolean flags."""
        mysite = self.site
        for change in mysite.recentchanges(showPatrolled=True, total=5):
            self.assertIsInstance(change, dict)
            if mysite.has_right('patrol'):
                self.assertIn("patrolled", change)
        for change in mysite.recentchanges(showPatrolled=False, total=5):
            self.assertIsInstance(change, dict)
            if mysite.has_right('patrol'):
                self.assertNotIn("patrolled", change)


class TestUserWatchedPages(DefaultSiteTestCase):

    """Test user watched pages."""

    user = True

    def test_watched_pages(self):
        """Test the site.watched_pages() method."""
        gen = self.site.watched_pages(total=5, force=False)
        self.assertIsInstance(gen.request, api.CachedRequest)
        for page in gen:
            self.assertIsInstance(page, pywikibot.Page)
        # repeat to use the cache
        gen = self.site.watched_pages(total=5, force=False)
        self.assertIsInstance(gen.request, api.CachedRequest)
        for page in gen:
            self.assertIsInstance(page, pywikibot.Page)

    def test_watched_pages_uncached(self):
        """Test the site.watched_pages() method uncached."""
        gen = self.site.watched_pages(total=5, force=True)
        self.assertIsInstance(gen.request, api.Request)
        self.assertFalse(issubclass(gen.request_class, api.CachedRequest))
        for page in gen:
            self.assertIsInstance(page, pywikibot.Page)


class SearchTestCase(DefaultSiteTestCase):

    """Test search method."""

    def setUp(self):
        """Skip tests for Wikia Search extension."""
        super(SearchTestCase, self).setUp()
        if self.site.has_extension('Wikia Search'):
            raise unittest.SkipTest(
                'The site %r does not use MediaWiki search' % self.site)

    def testSearch(self):
        """Test the site.search() method."""
        mysite = self.site
        try:
            se = list(mysite.search("wiki", total=100, namespaces=0))
            self.assertLessEqual(len(se), 100)
            self.assertTrue(all(isinstance(hit, pywikibot.Page)
                                for hit in se))
            self.assertTrue(all(hit.namespace() == 0 for hit in se))
            for hit in mysite.search("common", namespaces=4, total=5):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertEqual(hit.namespace(), 4)
            for hit in mysite.search("word", namespaces=[5, 6, 7], total=5):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertIn(hit.namespace(), [5, 6, 7])
            for hit in mysite.search("another", namespaces="8|9|10", total=5):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertIn(hit.namespace(), [8, 9, 10])
            for hit in mysite.search("wiki", namespaces=0, total=10,
                                     get_redirects=True):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertEqual(hit.namespace(), 0)
        except pywikibot.data.api.APIError as e:
            if e.code == "gsrsearch-error" and "timed out" in e.info:
                raise unittest.SkipTest("gsrsearch returned timeout on site: %r" % e)
            raise

    def test_search_where_title(self):
        """Test site.search() method with 'where' parameter set to title."""
        try:
            for hit in self.site.search('wiki', namespaces=0, total=10,
                                        get_redirects=True, where='title'):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertEqual(hit.namespace(), 0)
                self.assertTrue('wiki' in hit.title().lower())
        except pywikibot.data.api.APIError as e:
            if e.code in ('search-title-disabled', 'gsrsearch-title-disabled'):
                raise unittest.SkipTest(
                    'Title search disabled on site: {0}'.format(self.site))
            raise


class TestUserContribsAsUser(DefaultSiteTestCase):

    """Test site method site.usercontribs() with bot user."""

    user = True

    def test_basic(self):
        """Test the site.usercontribs() method."""
        mysite = self.get_site()
        uc = list(mysite.usercontribs(user=mysite.user(), total=10))
        self.assertLessEqual(len(uc), 10)
        self.assertTrue(all(isinstance(contrib, dict)
                            for contrib in uc))
        self.assertTrue(all('user' in contrib and contrib['user'] == mysite.user()
                            for contrib in uc))

    def test_namespaces(self):
        """Test the site.usercontribs() method using namespaces."""
        mysite = self.get_site()
        for contrib in mysite.usercontribs(user=mysite.user(),
                                           namespaces=14, total=5):
            self.assertIsInstance(contrib, dict)
            self.assertIn("title", contrib)
            self.assertTrue(contrib["title"].startswith(mysite.namespace(14)))

        for contrib in mysite.usercontribs(user=mysite.user(),
                                           namespaces=[10, 11], total=5):
            self.assertIsInstance(contrib, dict)
            self.assertIn("title", contrib)
            self.assertIn(contrib["ns"], (10, 11))

    def test_show_minor(self):
        """Test the site.usercontribs() method using showMinor."""
        mysite = self.get_site()
        for contrib in mysite.usercontribs(user=mysite.user(),
                                           showMinor=True, total=5):
            self.assertIsInstance(contrib, dict)
            self.assertIn("minor", contrib)

        for contrib in mysite.usercontribs(user=mysite.user(),
                                           showMinor=False, total=5):
            self.assertIsInstance(contrib, dict)
            self.assertNotIn("minor", contrib)


class TestUserContribsWithoutUser(DefaultSiteTestCase):

    """Test site method site.usercontribs() without bot user."""

    def test_user_prefix(self):
        """Test the site.usercontribs() method with userprefix."""
        mysite = self.get_site()
        for contrib in mysite.usercontribs(userprefix="John", total=5):
            self.assertIsInstance(contrib, dict)
            for key in ("user", "title", "ns", "pageid", "revid"):
                self.assertIn(key, contrib)
            self.assertTrue(contrib["user"].startswith("John"))

    def test_user_prefix_range(self):
        """Test the site.usercontribs() method."""
        mysite = self.get_site()
        start = '2008-10-06T01:02:03Z'
        for contrib in mysite.usercontribs(
                userprefix='Jane',
                start=pywikibot.Timestamp.fromISOformat(start),
                total=5):
            self.assertLessEqual(contrib['timestamp'], start)

        end = '2008-10-07T02:03:04Z'
        for contrib in mysite.usercontribs(
                userprefix='Jane',
                end=pywikibot.Timestamp.fromISOformat(end),
                total=5):
            self.assertGreaterEqual(contrib['timestamp'], end)

        start = '2008-10-10T11:59:59Z'
        end = '2008-10-10T00:00:01Z'
        for contrib in mysite.usercontribs(
                userprefix='Timshiel',
                start=pywikibot.Timestamp.fromISOformat(start),
                end=pywikibot.Timestamp.fromISOformat(end),
                total=5):
            self.assertTrue(end <= contrib['timestamp'] <= start)

    def test_user_prefix_reverse(self):
        """Test the site.usercontribs() method with range reversed."""
        mysite = self.get_site()
        start = '2008-10-08T03:05:07Z'
        for contrib in mysite.usercontribs(
                userprefix='Brion',
                start=pywikibot.Timestamp.fromISOformat(start),
                total=5, reverse=True):
            self.assertGreaterEqual(contrib['timestamp'], start)

        for contrib in mysite.usercontribs(
                userprefix='Brion',
                end=pywikibot.Timestamp.fromISOformat("2008-10-09T04:06:08Z"),
                total=5, reverse=True):
            self.assertLessEqual(contrib['timestamp'], "2008-10-09T04:06:08Z")

        start = '2008-10-11T06:00:01Z'
        end = '2008-10-11T23:59:59Z'
        for contrib in mysite.usercontribs(
                userprefix='Tim symond',
                start=pywikibot.Timestamp.fromISOformat(start),
                end=pywikibot.Timestamp.fromISOformat(end),
                reverse=True, total=5):
            self.assertTrue(start <= contrib['timestamp'] <= end)

    def test_invalid_range(self):
        """Test the site.usercontribs() method with invalid parameters."""
        mysite = self.get_site()
        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.usercontribs,
                          userprefix="Jim",
                          start="2008-10-03T00:00:01Z",
                          end="2008-10-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.usercontribs,
                          userprefix="Jim",
                          start="2008-10-03T23:59:59Z",
                          end="2008-10-03T00:00:01Z", reverse=True, total=5)


class SiteWatchlistRevsTestCase(DefaultSiteTestCase):

    """Test site method watchlist_revs()."""

    user = True

    def testWatchlistrevs(self):
        """Test the site.watchlist_revs() method."""
        mysite = self.get_site()
        wl = list(mysite.watchlist_revs(total=10))
        self.assertLessEqual(len(wl), 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in wl))
        for rev in mysite.watchlist_revs(start="2008-10-11T01:02:03Z",
                                         total=5):
            self.assertIsInstance(rev, dict)
            self.assertLessEqual(rev['timestamp'], "2008-10-11T01:02:03Z")
        for rev in mysite.watchlist_revs(end="2008-04-01T02:03:04Z",
                                         total=5):
            self.assertIsInstance(rev, dict)
            self.assertGreaterEqual(rev['timestamp'], "2008-10-11T02:03:04Z")
        for rev in mysite.watchlist_revs(start="2008-10-11T03:05:07Z",
                                         total=5, reverse=True):
            self.assertIsInstance(rev, dict)
            self.assertGreaterEqual(rev['timestamp'], "2008-10-11T03:05:07Z")
        for rev in mysite.watchlist_revs(end="2008-10-11T04:06:08Z",
                                         total=5, reverse=True):
            self.assertIsInstance(rev, dict)
            self.assertLessEqual(rev['timestamp'], "2008-10-11T04:06:08Z")
        for rev in mysite.watchlist_revs(start="2008-10-13T11:59:59Z",
                                         end="2008-10-13T00:00:01Z",
                                         total=5):
            self.assertIsInstance(rev, dict)
            self.assertTrue(
                "2008-10-13T00:00:01Z" <= rev['timestamp'] <= "2008-10-13T11:59:59Z")
        for rev in mysite.watchlist_revs(start="2008-10-15T06:00:01Z",
                                         end="2008-10-15T23:59:59Z",
                                         reverse=True, total=5):
            self.assertIsInstance(rev, dict)
            self.assertTrue(
                "2008-10-15T06:00:01Z" <= rev['timestamp'] <= "2008-10-15T23:59:59Z")
        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.watchlist_revs,
                          start="2008-09-03T00:00:01Z",
                          end="2008-09-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.watchlist_revs,
                          start="2008-09-03T23:59:59Z",
                          end="2008-09-03T00:00:01Z", reverse=True, total=5)
        for rev in mysite.watchlist_revs(namespaces=[6, 7], total=5):
            self.assertIsInstance(rev, dict)
            self.assertIn('title', rev)
            self.assertIn('ns', rev)
            title = rev['title']
            self.assertIn(":", title)
            prefix = title[:title.index(":")]
            self.assertIn(self.site.namespaces.lookup_name(prefix).id, [6, 7])
            self.assertIn(rev["ns"], [6, 7])
        for rev in mysite.watchlist_revs(showMinor=True, total=5):
            self.assertIsInstance(rev, dict)
            self.assertIn("minor", rev)
        for rev in mysite.watchlist_revs(showMinor=False, total=5):
            self.assertIsInstance(rev, dict)
            self.assertNotIn("minor", rev)
        for rev in mysite.watchlist_revs(showBot=True, total=5):
            self.assertIsInstance(rev, dict)
            self.assertIn("bot", rev)
        for rev in mysite.watchlist_revs(showBot=False, total=5):
            self.assertIsInstance(rev, dict)
            self.assertNotIn("bot", rev)
        for rev in mysite.watchlist_revs(showAnon=True, total=5):
            self.assertIsInstance(rev, dict)
        for rev in mysite.watchlist_revs(showAnon=False, total=5):
            self.assertIsInstance(rev, dict)


class SiteSysopTestCase(DefaultSiteTestCase):

    """Test site method using a sysop account."""

    sysop = True

    def test_methods(self):
        """Test sysop related methods."""
        mysite = self.get_site()
        self.assertIsInstance(mysite.is_blocked(True), bool)
        self.assertIsInstance(mysite.has_right("edit", True), bool)
        self.assertFalse(mysite.has_right("nonexistent_right", True))
        self.assertIsInstance(mysite.has_group("bots", True), bool)
        self.assertFalse(mysite.has_group("nonexistent_group", True))

    def testDeletedrevs(self):
        """Test the site.deletedrevs() method."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        gen = mysite.deletedrevs(total=10, page=mainpage)
        for dr in gen:
            break
        else:
            raise unittest.SkipTest(
                '{0} contains no deleted revisions.'.format(mainpage))
        self.assertLessEqual(len(dr['revisions']), 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in dr['revisions']))
        for item in mysite.deletedrevs(start="2008-10-11T01:02:03Z",
                                       page=mainpage, total=5):
            for rev in item['revisions']:
                self.assertIsInstance(rev, dict)
                self.assertLessEqual(rev['timestamp'], "2008-10-11T01:02:03Z")
        for item in mysite.deletedrevs(end="2008-04-01T02:03:04Z",
                                       page=mainpage, total=5):
            for rev in item['revisions']:
                self.assertIsInstance(rev, dict)
                self.assertGreaterEqual(rev['timestamp'], "2008-10-11T02:03:04Z")
        for item in mysite.deletedrevs(start="2008-10-11T03:05:07Z",
                                       page=mainpage, total=5,
                                       reverse=True):
            for rev in item['revisions']:
                self.assertIsInstance(rev, dict)
                self.assertGreaterEqual(rev['timestamp'], "2008-10-11T03:05:07Z")
        for item in mysite.deletedrevs(end="2008-10-11T04:06:08Z",
                                       page=mainpage, total=5,
                                       reverse=True):
            for rev in item['revisions']:
                self.assertIsInstance(rev, dict)
                self.assertLessEqual(rev['timestamp'], "2008-10-11T04:06:08Z")
        for item in mysite.deletedrevs(start="2008-10-13T11:59:59Z",
                                       end="2008-10-13T00:00:01Z",
                                       page=mainpage, total=5):
            for rev in item['revisions']:
                self.assertIsInstance(rev, dict)
                self.assertLessEqual(rev['timestamp'], "2008-10-13T11:59:59Z")
                self.assertGreaterEqual(rev['timestamp'], "2008-10-13T00:00:01Z")
        for item in mysite.deletedrevs(start="2008-10-15T06:00:01Z",
                                       end="2008-10-15T23:59:59Z",
                                       page=mainpage, reverse=True,
                                       total=5):
            for rev in item['revisions']:
                self.assertIsInstance(rev, dict)
                self.assertLessEqual(rev['timestamp'], "2008-10-15T23:59:59Z")
                self.assertGreaterEqual(rev['timestamp'], "2008-10-15T06:00:01Z")

        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.deletedrevs,
                          page=mainpage, start="2008-09-03T00:00:01Z",
                          end="2008-09-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.deletedrevs,
                          page=mainpage, start="2008-09-03T23:59:59Z",
                          end="2008-09-03T00:00:01Z", reverse=True,
                          total=5)


class TestSiteSysopWrite(TestCase):

    """Test site sysop methods that require writing."""

    family = 'test'
    code = 'test'

    write = True
    sysop = True

    def test_protect(self):
        """Test the site.protect() method."""
        site = self.get_site()
        p1 = pywikibot.Page(site, u'User:Unicodesnowman/ProtectTest')

        r = site.protect(protections={'edit': 'sysop', 'move': 'autoconfirmed'},
                         page=p1,
                         reason='Pywikibot unit test')
        self.assertEqual(r, None)
        self.assertEqual(site.page_restrictions(page=p1),
                         {u'edit': (u'sysop', u'infinity'),
                          u'move': (u'autoconfirmed', u'infinity')})

        expiry = pywikibot.Timestamp.fromISOformat('2050-01-01T00:00:00Z')
        site.protect(protections={'edit': 'sysop', 'move': 'autoconfirmed'},
                     page=p1,
                     expiry=expiry,
                     reason='Pywikibot unit test')

        self.assertEqual(site.page_restrictions(page=p1),
                         {u'edit': (u'sysop', u'2050-01-01T00:00:00Z'),
                          u'move': (u'autoconfirmed', u'2050-01-01T00:00:00Z')})

        site.protect(protections={'edit': '', 'move': ''},
                     page=p1,
                     reason='Pywikibot unit test')
        self.assertEqual(site.page_restrictions(page=p1), {})

    def test_protect_alt(self):
        """Test the site.protect() method, works around T78522."""
        site = self.get_site()
        p1 = pywikibot.Page(site, u'User:Unicodesnowman/ProtectTest')

        r = site.protect(protections={'edit': 'sysop', 'move': 'autoconfirmed'},
                         page=p1,
                         reason='Pywikibot unit test')
        self.assertEqual(r, None)
        self.assertEqual(site.page_restrictions(page=p1),
                         {u'edit': (u'sysop', u'infinity'),
                          u'move': (u'autoconfirmed', u'infinity')})

        p1 = pywikibot.Page(site, u'User:Unicodesnowman/ProtectTest')
        expiry = pywikibot.Timestamp.fromISOformat('2050-01-01T00:00:00Z')
        site.protect(protections={'edit': 'sysop', 'move': 'autoconfirmed'},
                     page=p1,
                     expiry=expiry,
                     reason='Pywikibot unit test')

        self.assertEqual(site.page_restrictions(page=p1),
                         {u'edit': (u'sysop', u'2050-01-01T00:00:00Z'),
                          u'move': (u'autoconfirmed', u'2050-01-01T00:00:00Z')})

        p1 = pywikibot.Page(site, u'User:Unicodesnowman/ProtectTest')
        site.protect(protections={'edit': '', 'move': ''},
                     page=p1,
                     reason='Pywikibot unit test')
        self.assertEqual(site.page_restrictions(page=p1), {})

    def test_protect_exception(self):
        """Test that site.protect() throws an exception when passed invalid args."""
        site = self.get_site()
        p1 = pywikibot.Page(site, u'User:Unicodesnowman/ProtectTest')
        self.assertRaises(pywikibot.Error, site.protect,
                          protections={'anInvalidValue': 'sysop'},
                          page=p1, reason='Pywikibot unit test')
        self.assertRaises(pywikibot.Error, site.protect,
                          protections={'edit': 'anInvalidValue'},
                          page=p1, reason='Pywikibot unit test')

    def test_delete(self):
        """Test the site.deletepage() and site.undelete_page() methods."""
        site = self.get_site()
        p = pywikibot.Page(site, u'User:Unicodesnowman/DeleteTestSite')
        # Verify state
        if not p.exists():
            site.undelete_page(p, 'pywikibot unit tests')

        site.deletepage(p, reason='pywikibot unit tests')
        self.assertRaises(pywikibot.NoPage, p.get, force=True)

        site.undelete_page(p, 'pywikibot unit tests',
                           revisions=[u'2014-12-21T06:07:47Z',
                                      u'2014-12-21T06:07:31Z'])

        revs = list(p.revisions())
        self.assertEqual(len(revs), 2)
        self.assertEqual(revs[0].revid, 219995)
        self.assertEqual(revs[1].revid, 219994)

        site.deletepage(p, reason='pywikibot unit tests')
        site.undelete_page(p, 'pywikibot unit tests')
        revs = list(p.revisions())
        self.assertTrue(len(revs) > 2)


class TestUsernameInUsers(DefaultSiteTestCase):

    """Test that the user account can be found in users list."""

    user = True
    cached = True

    def test_username_in_users(self):
        """Test the site.users() method with bot username."""
        mysite = self.get_site()
        us = list(mysite.users(mysite.user()))
        self.assertEqual(len(us), 1)
        self.assertIsInstance(us[0], dict)


class TestUserList(DefaultSiteTestCase):

    """Test usernames Jimbo Wales, Brion VIBBER and Tim Starling."""

    cached = True

    def testUsers(self):
        """Test the site.users() method with preset usernames."""
        mysite = self.site
        cnt = 0
        for user in mysite.users(
                ["Jimbo Wales", "Brion VIBBER", "Tim Starling"]):
            self.assertIsInstance(user, dict)
            self.assertTrue(user["name"]
                            in ["Jimbo Wales", "Brion VIBBER", "Tim Starling"])
            cnt += 1
        if not cnt:
            raise unittest.SkipTest('Test usernames not found')


class PatrolTestCase(TokenTestBase, TestCase):

    """Test patrol method."""

    family = 'test'
    code = 'test'

    user = True
    token_type = 'patrol'
    write = True

    def testPatrol(self):
        """Test the site.patrol() method."""
        mysite = self.get_site()

        rc = list(mysite.recentchanges(total=1))
        if not rc:
            raise unittest.SkipTest('no recent changes to patrol')

        rc = rc[0]

        # site.patrol() needs params
        self.assertRaises(pywikibot.Error, lambda x: list(x), mysite.patrol())
        try:
            result = list(mysite.patrol(rcid=rc['rcid']))
        except api.APIError as error:
            if error.code == u'permissiondenied':
                raise unittest.SkipTest(error)
            raise

        if hasattr(mysite, u'_patroldisabled') and mysite._patroldisabled:
            raise unittest.SkipTest(u'Patrolling is disabled on %s wiki.'
                                    % mysite)

        result = result[0]
        self.assertIsInstance(result, dict)

        params = {'rcid': 0}
        if mysite.version() >= MediaWikiVersion('1.22'):
            params['revid'] = [0, 1]

        try:
            # no such rcid, revid or too old revid
            result = list(mysite.patrol(**params))
        except api.APIError as error:
            if error.code == u'badtoken':
                raise unittest.SkipTest(error)
        except pywikibot.Error as error:
            # expected result
            pass


class SiteRandomTestCase(DefaultSiteTestCase):

    """Test random methods of a site."""

    def test_unlimited_small_step(self):
        """Test site.randompages() continuation.

        Note that uniqueness is not guaranteed if multiple requests are
        performed, so we also don't test this here.
        """
        mysite = self.get_site()
        pages = []
        rngen = mysite.randompages(total=None)
        rngen.set_query_increment = 5
        for rndpage in rngen:
            self.assertIsInstance(rndpage, pywikibot.Page)
            pages.append(rndpage)
            if len(pages) == 11:
                break
        self.assertEqual(len(pages), 11)

    def test_limit_10(self):
        """Test site.randompages() with limit."""
        mysite = self.get_site()
        rn = list(mysite.randompages(total=10))
        self.assertLessEqual(len(rn), 10)
        self.assertTrue(all(isinstance(a_page, pywikibot.Page)
                            for a_page in rn))
        self.assertFalse(all(a_page.isRedirectPage() for a_page in rn))

    def test_redirects(self):
        """Test site.randompages() with redirects."""
        mysite = self.get_site()
        for rndpage in mysite.randompages(total=5, redirects=True):
            self.assertIsInstance(rndpage, pywikibot.Page)
            self.assertTrue(rndpage.isRedirectPage())

    def test_namespaces(self):
        """Test site.randompages() with namespaces."""
        mysite = self.get_site()
        for rndpage in mysite.randompages(total=5, namespaces=[6, 7]):
            self.assertIsInstance(rndpage, pywikibot.Page)
            self.assertIn(rndpage.namespace(), [6, 7])


class TestSiteTokens(DefaultSiteTestCase):

    """Test cases for tokens in Site methods.

    Versions of sites are simulated if actual versions are higher than
    needed by the test case.

    Test is skipped if site version is not compatible.

    """

    user = True

    def setUp(self):
        """Store version."""
        super(TestSiteTokens, self).setUp()
        self.mysite = self.get_site()
        self._version = MediaWikiVersion(self.mysite.version())
        self.orig_version = self.mysite.version

    def tearDown(self):
        """Restore version."""
        super(TestSiteTokens, self).tearDown()
        self.mysite.version = self.orig_version

    def _test_tokens(self, version, test_version, additional_token):
        """Test tokens."""
        if version and self._version < MediaWikiVersion(version):
            raise unittest.SkipTest(
                u'Site %s version %s is too low for this tests.'
                % (self.mysite, self._version))

        if version and self._version < MediaWikiVersion(test_version):
            raise unittest.SkipTest(
                u'Site %s version %s is too low for this tests.'
                % (self.mysite, self._version))

        self.mysite.version = lambda: test_version

        for ttype in ("edit", "move", additional_token):
            tokentype = self.mysite.validate_tokens([ttype])
            try:
                token = self.mysite.tokens[ttype]
            except pywikibot.Error as error_msg:
                if tokentype:
                    self.assertRegex(
                        unicode(error_msg),
                        "Action '[a-z]+' is not allowed for user .* on .* wiki.")
                    # test __contains__
                    self.assertNotIn(tokentype[0], self.mysite.tokens)
                else:
                    self.assertRegex(
                        unicode(error_msg),
                        "Requested token '[a-z]+' is invalid on .* wiki.")
            else:
                self.assertIsInstance(token, basestring)
                self.assertEqual(token, self.mysite.tokens[ttype])
                # test __contains__
                self.assertIn(tokentype[0], self.mysite.tokens)

    def test_patrol_tokens_in_mw_116(self):
        """Test ability to get patrol token on MW 1.16 wiki."""
        self._test_tokens('1.14', '1.16', 'patrol')

    def test_tokens_in_mw_119(self):
        """Test ability to get page tokens."""
        self._test_tokens(None, '1.19', 'delete')

    def test_patrol_tokens_in_mw_119(self):
        """Test ability to get patrol token on MW 1.19 wiki."""
        self._test_tokens('1.14', '1.19', 'patrol')

    def test_tokens_in_mw_120_124wmf18(self):
        """Test ability to get page tokens."""
        self._test_tokens('1.20', '1.21', 'deleteglobalaccount')

    def test_patrol_tokens_in_mw_120(self):
        """Test ability to get patrol token."""
        self._test_tokens('1.14', '1.20', 'patrol')

    def test_tokens_in_mw_124wmf19(self):
        """Test ability to get page tokens."""
        self._test_tokens('1.24wmf19', '1.24wmf20', 'deleteglobalaccount')

    def testInvalidToken(self):
        """Test invalid token."""
        self.assertRaises(pywikibot.Error, lambda t: self.mysite.tokens[t], "invalidtype")


class TestDeprecatedEditTokenFunctions(TokenTestBase,
                                       DefaultSiteTestCase,
                                       DeprecationTestCase):

    """Test cases for Site edit token deprecated methods."""

    cached = True
    user = True
    token_type = 'edit'

    def test_token(self):
        """Test ability to get page tokens using site.tokens."""
        token = self.token
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        ttype = "edit"
        self.assertEqual(token, mysite.token(mainpage, ttype))
        self.assertOneDeprecationParts('pywikibot.site.APISite.token',
                                       "the 'tokens' property")

    def test_getToken(self):
        """Test ability to get page tokens using site.getToken."""
        self.mysite = self.site
        self.assertEqual(self.mysite.getToken(), self.mysite.tokens['edit'])
        self.assertOneDeprecationParts('pywikibot.site.APISite.getToken',
                                       "the 'tokens' property")


class TestDeprecatedPatrolToken(DefaultSiteTestCase, DeprecationTestCase):

    """Test cases for Site patrol token deprecated methods."""

    cached = True
    user = True

    def test_getPatrolToken(self):
        """Test site.getPatrolToken."""
        self.mysite = self.site
        try:
            self.assertEqual(self.mysite.getPatrolToken(), self.mysite.tokens['patrol'])
            self.assertOneDeprecation()
        except pywikibot.Error as error_msg:
            self.assertRegex(
                unicode(error_msg),
                "Action '[a-z]+' is not allowed for user .* on .* wiki.")
            # test __contains__
            self.assertNotIn('patrol', self.mysite.tokens)


class TestSiteExtensions(WikimediaDefaultSiteTestCase):

    """Test cases for Site extensions."""

    cached = True

    def testExtensions(self):
        """Test Extensions."""
        mysite = self.get_site()
        # test automatically getting extensions cache
        if 'extensions' in mysite.siteinfo:
            del mysite.siteinfo._cache['extensions']
        self.assertTrue(mysite.has_extension('Disambiguator'))

        # test case-sensitivity
        self.assertFalse(mysite.has_extension('disambiguator'))

        self.assertFalse(mysite.has_extension('ThisExtensionDoesNotExist'))


class TestSiteAPILimits(TestCase):

    """Test cases for Site method that use API limits."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def test_API_limits_with_site_methods(self):
        """Test step/total parameters for different sitemethods."""
        mysite = self.get_site()
        mypage = pywikibot.Page(mysite, 'Albert Einstein')
        mycat = pywikibot.Page(mysite, 'Category:1879 births')

        gen = mysite.pagecategories(mypage, total=12)
        gen.set_query_increment = 5
        cats = [c for c in gen]
        self.assertEqual(len(cats), 12)

        gen = mysite.categorymembers(mycat, total=12)
        gen.set_query_increment = 5
        cat_members = [cm for cm in gen]
        self.assertEqual(len(cat_members), 12)

        gen = mysite.pageimages(mypage, total=5)
        gen.set_query_increment = 3
        images = [im for im in gen]
        self.assertEqual(len(images), 5)

        gen = mysite.pagetemplates(mypage, total=5)
        gen.set_query_increment = 3
        templates = [tl for tl in gen]
        self.assertEqual(len(templates), 5)

        mysite.loadrevisions(mypage, step=5, total=12)
        self.assertEqual(len(mypage._revisions), 12)


class TestSiteInfo(DefaultSiteTestCase):

    """Test cases for Site metadata and capabilities."""

    cached = True

    def testSiteinfo(self):
        """Test the siteinfo property."""
        # general enteries
        mysite = self.get_site()
        self.assertIsInstance(mysite.siteinfo['timeoffset'], (int, float))
        self.assertTrue(-12 * 60 <= mysite.siteinfo['timeoffset'] <= +14 * 60)
        self.assertEqual(mysite.siteinfo['timeoffset'] % 15, 0)
        self.assertRegex(mysite.siteinfo['timezone'], "([A-Z]{3,4}|[A-Z][a-z]+/[A-Z][a-z]+)")
        self.assertIn(mysite.siteinfo['case'], ["first-letter", "case-sensitive"])

    def test_siteinfo_boolean(self):
        """Test conversion of boolean properties from empty strings to True/False."""
        mysite = self.get_site()
        self.assertIsInstance(mysite.siteinfo['titleconversion'], bool)

        self.assertIsInstance(mysite.namespaces[0].subpages, bool)
        self.assertIsInstance(mysite.namespaces[0].content, bool)

    def test_siteinfo_v1_16(self):
        """Test v.16+ siteinfo values."""
        if MediaWikiVersion(self.site.version()) < MediaWikiVersion('1.16'):
            raise unittest.SkipTest('requires v1.16+')

        mysite = self.get_site()
        self.assertIsInstance(
            datetime.strptime(mysite.siteinfo['time'], '%Y-%m-%dT%H:%M:%SZ'),
            datetime)
        self.assertEqual(re.findall(r'\$1', mysite.siteinfo['articlepath']), ['$1'])

    def test_properties_with_defaults(self):
        """Test the siteinfo properties with defaults."""
        # This does not test that the defaults work correct,
        # unless the default site is a version needing these defaults
        # 'fileextensions' introduced in v1.15:
        self.assertIsInstance(self.site.siteinfo.get('fileextensions'), list)
        self.assertIn('fileextensions', self.site.siteinfo)
        fileextensions = self.site.siteinfo.get('fileextensions')
        self.assertIn({'ext': 'png'}, fileextensions)
        # 'restrictions' introduced in v1.23:
        mysite = self.site
        self.assertIsInstance(mysite.siteinfo.get('restrictions'), dict)
        self.assertIn('restrictions', mysite.siteinfo)
        restrictions = self.site.siteinfo.get('restrictions')
        self.assertIn('cascadinglevels', restrictions)

    def test_no_cache(self):
        """Test siteinfo caching can be disabled."""
        if 'fileextensions' in self.site.siteinfo._cache:
            del self.site.siteinfo._cache['fileextensions']
        self.site.siteinfo.get('fileextensions', cache=False)
        self.assertNotIn('fileextensions', self.site.siteinfo)

    def test_not_exists(self):
        """Test accessing a property not in siteinfo."""
        not_exists = 'this-property-does-not-exist'
        mysite = self.site
        self.assertRaises(KeyError, mysite.siteinfo.__getitem__, not_exists)
        self.assertNotIn(not_exists, mysite.siteinfo)
        self.assertEqual(len(mysite.siteinfo.get(not_exists)), 0)
        self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists)))
        if PY2:
            self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).iteritems()))
            self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).itervalues()))
            self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).iterkeys()))
        self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).items()))
        self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).values()))
        self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).keys()))


class TestSiteinfoAsync(DefaultSiteTestCase):

    """Test asynchronous siteinfo fetch."""

    def test_async_request(self):
        """Test async request."""
        self.assertTrue(page_put_queue.empty())
        self.assertNotIn('statistics', self.site.siteinfo)
        async_request(self.site.siteinfo.get, 'statistics')
        page_put_queue.join()
        self.assertIn('statistics', self.site.siteinfo)


class TestSiteLoadRevisionsCaching(BasePageLoadRevisionsCachingTestBase,
                                   DefaultSiteTestCase):

    """Test site.loadrevisions() caching."""

    def setUp(self):
        """Setup tests."""
        self._page = self.get_mainpage(force=True)
        super(TestSiteLoadRevisionsCaching, self).setUp()

    def test_page_text(self):
        """Test site.loadrevisions() with Page.text."""
        self._test_page_text()


class TestSiteLoadRevisions(TestCase):

    """Test cases for Site.loadrevision() method."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    # Implemented without setUpClass(cls) and global variables as objects
    # were not completely disposed and recreated but retained 'memory'
    def setUp(self):
        """Setup tests."""
        super(TestSiteLoadRevisions, self).setUp()
        self.mysite = self.get_site()
        self.mainpage = pywikibot.Page(pywikibot.Link("Main Page", self.mysite))

    def testLoadRevisions_basic(self):
        """Test the site.loadrevisions() method."""
        # Load revisions without content
        self.mysite.loadrevisions(self.mainpage, total=15)
        self.mysite.loadrevisions(self.mainpage)
        self.assertFalse(hasattr(self.mainpage, '_text'))
        self.assertEqual(len(self.mainpage._revisions), 15)
        self.assertIn(self.mainpage._revid, self.mainpage._revisions)
        self.assertIsNone(self.mainpage._revisions[self.mainpage._revid].text)
        # The revision content will be loaded by .text
        self.assertIsNotNone(self.mainpage.text)

    def testLoadRevisions_getText(self):
        """Test the site.loadrevisions() method with getText=True."""
        self.mysite.loadrevisions(self.mainpage, getText=True, total=5)
        self.assertFalse(hasattr(self.mainpage, '_text'))
        self.assertIn(self.mainpage._revid, self.mainpage._revisions)
        self.assertIsNotNone(self.mainpage._revisions[self.mainpage._revid].text)
        self.assertTrue(self.mainpage._revisions[self.mainpage._revid].text)
        self.assertIsNotNone(self.mainpage.text)

    def testLoadRevisions_revids(self):
        """Test the site.loadrevisions() method, listing based on revid."""
        # revids as list of int
        self.mysite.loadrevisions(self.mainpage, revids=[139992, 139993])
        self.assertTrue(all(rev in self.mainpage._revisions for rev in [139992, 139993]))
        # revids as list of str
        self.mysite.loadrevisions(self.mainpage, revids=['139994', '139995'])
        self.assertTrue(all(rev in self.mainpage._revisions for rev in [139994, 139995]))
        # revids as int
        self.mysite.loadrevisions(self.mainpage, revids=140000)
        self.assertIn(140000, self.mainpage._revisions)
        # revids as str
        self.mysite.loadrevisions(self.mainpage, revids='140001')
        self.assertIn(140001, self.mainpage._revisions)
        # revids belonging to a different page raises Exception
        self.assertRaises(pywikibot.Error, self.mysite.loadrevisions,
                          self.mainpage, revids=130000)

    def testLoadRevisions_querycontinue(self):
        """Test the site.loadrevisions() method with query-continue."""
        self.mysite.loadrevisions(self.mainpage, step=5, total=12)
        self.assertEqual(len(self.mainpage._revisions), 12)

    def testLoadRevisions_revdir(self):
        """Test the site.loadrevisions() method with rvdir=True."""
        self.mysite.loadrevisions(self.mainpage, rvdir=True, total=15)
        self.assertEqual(len(self.mainpage._revisions), 15)

    def testLoadRevisions_timestamp(self):
        """Test the site.loadrevisions() method, listing based on timestamp."""
        self.mysite.loadrevisions(self.mainpage, rvdir=True, total=15)
        self.assertEqual(len(self.mainpage._revisions), 15)
        revs = self.mainpage._revisions
        timestamps = [str(revs[rev].timestamp) for rev in revs]
        self.assertTrue(all(ts < "2002-01-31T00:00:00Z" for ts in timestamps))

        # Retrieve oldest revisions; listing based on timestamp.
        # Raises "loadrevisions: starttime > endtime with rvdir=True"
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=True,
                          starttime="2002-02-01T00:00:00Z", endtime="2002-01-01T00:00:00Z")

        # Retrieve newest revisions; listing based on timestamp.
        # Raises "loadrevisions: endtime > starttime with rvdir=False"
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=False,
                          starttime="2002-01-01T00:00:00Z", endtime="2002-02-01T00:00:00Z")

    def testLoadRevisions_rev_id(self):
        """Test the site.loadrevisions() method, listing based on rev_id."""
        self.mysite.loadrevisions(self.mainpage, rvdir=True, total=15)
        self.assertEqual(len(self.mainpage._revisions), 15)
        revs = self.mainpage._revisions
        self.assertTrue(all(139900 <= rev <= 140100 for rev in revs))

        # Retrieve oldest revisions; listing based on revid.
        # Raises "loadrevisions: startid > endid with rvdir=True"
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=True,
                          startid="200000", endid="100000")

        # Retrieve newest revisions; listing based on revid.
        # Raises "loadrevisions: endid > startid with rvdir=False
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=False,
                          startid="100000", endid="200000")

    def testLoadRevisions_user(self):
        """Test the site.loadrevisions() method, filtering by user."""
        # Only list revisions made by this user.
        self.mainpage._revisions = {}
        self.mysite.loadrevisions(self.mainpage, rvdir=True,
                                  user="Magnus Manske")
        revs = self.mainpage._revisions
        self.assertTrue(all(revs[rev].user == "Magnus Manske" for rev in revs))

    def testLoadRevisions_excludeuser(self):
        """Test the site.loadrevisions() method, excluding user."""
        # Do not list revisions made by this user.
        self.mainpage._revisions = {}
        self.mysite.loadrevisions(self.mainpage, rvdir=True,
                                  excludeuser="Magnus Manske")
        revs = self.mainpage._revisions
        self.assertFalse(any(revs[rev].user == "Magnus Manske" for rev in revs))

        # TODO test other optional arguments


class TestSiteLoadRevisionsSysop(DefaultSiteTestCase):

    """Test cases for Site.loadrevision() method."""

    sysop = True

    def test_rollback(self):
        """Test the site.loadrevisions() method with rollback."""
        mainpage = self.get_mainpage()
        self.site.loadrevisions(mainpage, total=12, rollback=True, sysop=True)
        self.assertGreater(len(mainpage._revisions), 0)
        self.assertLessEqual(len(mainpage._revisions), 12)
        self.assertTrue(all(rev.rollbacktoken is not None
                            for rev in mainpage._revisions.values()))


class TestCommonsSite(TestCase):

    """Test cases for Site methods on Commons."""

    family = "commons"
    code = "commons"

    cached = True

    def testInterWikiForward(self):
        """Test interwiki forward."""
        self.site = self.get_site()
        self.mainpage = pywikibot.Page(pywikibot.Link("Main Page", self.site))
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

    def testNamespaceCase(self):
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

    def testNamespaceAliases(self):
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
        self.assertEqual(len(image_namespace), 4)

        self.assertEqual(len(namespaces[1].aliases), 0)
        self.assertEqual(len(namespaces[4].aliases), 1)
        self.assertEqual(namespaces[4].aliases[0], 'WP')
        self.assertIn('WP', namespaces[4])


class TestUploadEnabledSite(TestCase):

    """Test Site.is_uploaddisabled."""

    sites = {
        'wikidatatest': {
            'family': 'wikidata',
            'code': 'test',
            'enabled': False,
        },
        'wikipediatest': {
            'family': 'wikipedia',
            'code': 'test',
            'enabled': True,
        }
    }

    user = True

    def test_is_uploaddisabled(self, key):
        """Test is_uploaddisabled()."""
        site = self.get_site(key)
        if self.sites[key]['enabled']:
            self.assertFalse(site.is_uploaddisabled())
        else:
            self.assertTrue(site.is_uploaddisabled())


class TestLoadPagesFromPageids(DefaultSiteTestCase):

    """Test site.load_pages_from_pageids()."""

    cached = True

    def setUp(self):
        """Setup tests."""
        super(TestLoadPagesFromPageids, self).setUp()
        self.site = self.get_site()
        mainpage = self.get_mainpage()
        self.links = [
            page for page in self.site.pagelinks(mainpage, total=10)
            if page.exists()]

    def test_load_from_pageids_iterable_of_str(self):
        """Test basic loading with pageids."""
        pageids = [str(page.pageid) for page in self.links]
        gen = self.site.load_pages_from_pageids(pageids)
        count = 0
        for count, page in enumerate(gen, start=1):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            self.assertTrue(page.exists())
            self.assertTrue(hasattr(page, '_pageid'))
            self.assertIn(page, self.links)
        self.assertEqual(count, len(self.links))

    def test_load_from_pageids_iterable_of_int(self):
        """Test basic loading with pageids."""
        pageids = [page.pageid for page in self.links]
        gen = self.site.load_pages_from_pageids(pageids)
        count = 0
        for count, page in enumerate(gen, start=1):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            self.assertTrue(page.exists())
            self.assertTrue(hasattr(page, '_pageid'))
            self.assertIn(page, self.links)
        self.assertEqual(count, len(self.links))

    def test_load_from_pageids_iterable_in_order(self):
        """Test loading with pageids is ordered."""
        pageids = [page.pageid for page in self.links]
        gen = self.site.load_pages_from_pageids(pageids)
        for page in gen:
            link = self.links.pop(0)
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            self.assertTrue(page.exists())
            self.assertTrue(hasattr(page, '_pageid'))
            self.assertEqual(page, link)

    def test_load_from_pageids_iterable_with_duplicate(self):
        """Test loading with duplicate pageids."""
        pageids = [page.pageid for page in self.links]
        pageids = pageids + pageids
        gen = self.site.load_pages_from_pageids(pageids)
        count = 0
        for count, page in enumerate(gen, start=1):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            self.assertTrue(page.exists())
            self.assertTrue(hasattr(page, '_pageid'))
            self.assertIn(page, self.links)
        self.assertEqual(count, len(self.links))

    def test_load_from_pageids_comma_separated(self):
        """Test loading from comma-separated pageids."""
        pageids = ', '.join(str(page.pageid) for page in self.links)
        gen = self.site.load_pages_from_pageids(pageids)
        count = 0
        for count, page in enumerate(gen, start=1):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            self.assertTrue(page.exists())
            self.assertTrue(hasattr(page, '_pageid'))
            self.assertIn(page, self.links)
        self.assertEqual(count, len(self.links))

    def test_load_from_pageids_pipe_separated(self):
        """Test loading from comma-separated pageids."""
        pageids = '|'.join(str(page.pageid) for page in self.links)
        gen = self.site.load_pages_from_pageids(pageids)
        count = 0
        for count, page in enumerate(gen, start=1):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            self.assertTrue(page.exists())
            self.assertTrue(hasattr(page, '_pageid'))
            self.assertIn(page, self.links)
        self.assertEqual(count, len(self.links))


class TestPagePreloading(DefaultSiteTestCase):

    """Test site.preloadpages()."""

    def test_order(self):
        """Test outcome is following same order of input."""
        mainpage = self.get_mainpage()
        links = [page for page in self.site.pagelinks(mainpage, total=20)
                 if page.exists()]
        pages = list(self.site.preloadpages(links, groupsize=5))
        self.assertEqual(pages, links)

    def test_duplicates(self):
        """Test outcome is following same order of input."""
        mainpage = self.get_mainpage()
        links = [page for page in self.site.pagelinks(mainpage, total=20)
                 if page.exists()]
        dupl_links = links + links[::-1]
        pages = list(self.site.preloadpages(dupl_links, groupsize=40))
        self.assertEqual(pages, links)

    def test_pageids(self):
        """Test basic preloading with pageids."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0
        links = mysite.pagelinks(mainpage, total=10)
        # preloadpages will send the page ids,
        # as they have already been loaded by pagelinks
        for page in mysite.preloadpages(links):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertTrue(hasattr(page, '_revid'))
                self.assertEqual(len(page._revisions), 1)
                self.assertIn(page._revid, page._revisions)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
            count += 1
            if count >= 5:
                break

    def test_titles(self):
        """Test basic preloading with titles."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0
        links = mysite.pagelinks(mainpage, total=10)

        # remove the pageids that have already been loaded above by pagelinks
        # so that preloadpages will use the titles instead
        for page in links:
            if hasattr(page, '_pageid'):
                self.assertEqual(page.pageid, page._pageid)
            del page._pageid

        for page in mysite.preloadpages(links):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertEqual(len(page._revisions), 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
            count += 1
            if count >= 5:
                break

    def test_preload_continuation(self):
        """Test preloading continuation works."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0
        links = mysite.pagelinks(mainpage, total=10)
        for page in mysite.preloadpages(links, groupsize=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertEqual(len(page._revisions), 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
            count += 1
            if count >= 6:
                break

    def test_preload_high_groupsize(self):
        """Test preloading continuation with groupsize greater than total."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0

        # Determine if there are enough links on the main page,
        # for the test to be useful.
        link_count = len(list(mysite.pagelinks(mainpage, total=10)))
        if link_count < 2:
            raise unittest.SkipTest('insufficient links on main page')

        # get a fresh generator; we now know how many results it will have,
        # if it is less than 10.
        links = mysite.pagelinks(mainpage, total=10)
        for page in mysite.preloadpages(links, groupsize=50):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertEqual(len(page._revisions), 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
            count += 1
        self.assertEqual(count, link_count)

    def test_preload_low_groupsize(self):
        """Test preloading continuation with groupsize greater than total."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0

        # Determine if there are enough links on the main page,
        # for the test to be useful.
        link_count = len(list(mysite.pagelinks(mainpage, total=10)))
        if link_count < 2:
            raise unittest.SkipTest('insufficient links on main page')

        # get a fresh generator; we now know how many results it will have,
        # if it is less than 10.
        links = mysite.pagelinks(mainpage, total=10)
        for page in mysite.preloadpages(links, groupsize=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertEqual(len(page._revisions), 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
            count += 1
        self.assertEqual(count, link_count)

    def test_preload_unexpected_titles_using_pageids(self):
        """Test sending pageids with unnormalized titles, causing warnings."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0
        links = list(mysite.pagelinks(mainpage, total=10))
        if len(links) < 2:
            raise unittest.SkipTest('insufficient links on main page')

        # change the title of the page, to test sametitle().
        # preloadpages will send the page ids, as they have already been loaded
        # by pagelinks, and preloadpages should complain the returned titles
        # do not match any title in the pagelist.
        # However, APISite.sametitle now correctly links them.
        for page in links:
            page._link._text += ' '

        gen = mysite.preloadpages(links, groupsize=5)
        for page in gen:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertEqual(len(page._revisions), 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
            count += 1
            if count > 5:
                break

    def test_preload_unexpected_titles_using_titles(self):
        """Test sending unnormalized titles, causing warnings."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0
        links = list(mysite.pagelinks(mainpage, total=10))
        if len(links) < 2:
            raise unittest.SkipTest('insufficient links on main page')

        # change the title of the page _and_ delete the pageids.
        # preloadpages can only send the titles, and preloadpages should
        # complain the returned titles do not match any title in the pagelist.
        # However, APISite.sametitle now correctly links them.
        for page in links:
            page._link._text += ' '
            del page._pageid

        gen = mysite.preloadpages(links, groupsize=5)
        for page in gen:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertEqual(len(page._revisions), 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
            count += 1
            if count > 5:
                break

    def test_preload_invalid_titles_without_pageids(self):
        """Test sending invalid titles. No warnings issued, but it should."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0
        links = list(mysite.pagelinks(mainpage, total=10))
        if len(links) < 2:
            raise unittest.SkipTest('insufficient links on main page')

        for page in links:
            page._link._text += ' foobar'
            del page._pageid

        gen = mysite.preloadpages(links, groupsize=5)
        for page in gen:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            self.assertFalse(page.exists())
            count += 1
            if count > 5:
                break

    @allowed_failure
    def test_preload_langlinks_normal(self):
        """Test preloading continuation works."""
        # FIXME: test fails
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0
        links = mysite.pagelinks(mainpage, total=10)
        for page in mysite.preloadpages(links, groupsize=5, langlinks=True):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertEqual(len(page._revisions), 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
                self.assertTrue(hasattr(page, '_langlinks'))
            count += 1
            if count >= 6:
                break

    @allowed_failure
    def test_preload_langlinks_count(self):
        """Test preloading continuation works."""
        # FIXME: test fails
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0
        links = mysite.pagelinks(mainpage, total=20)
        pages = list(mysite.preloadpages(links, groupsize=5,
                                         langlinks=True))
        for page in pages:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertEqual(len(page._revisions), 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
            count += 1

        self.assertEqual(len(list(links)), count)

    def _test_preload_langlinks_long(self):
        """Test preloading continuation works."""
        # FIXME: test fails. It is disabled as it takes more
        # than 10 minutes on travis for English Wikipedia
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0
        links = mainpage.backlinks(total=100)
        for page in mysite.preloadpages(links, groupsize=50,
                                        langlinks=True):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertEqual(len(page._revisions), 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
                self.assertTrue(hasattr(page, '_langlinks'))
            count += 1

        self.assertEqual(len(links), count)

    @allowed_failure
    def test_preload_templates(self):
        """Test preloading templates works."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0
        # Use backlinks, as any backlink has at least one link
        links = mysite.pagelinks(mainpage, total=10)
        for page in mysite.preloadpages(links, templates=True):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertEqual(len(page._revisions), 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
                self.assertTrue(hasattr(page, '_templates'))
            count += 1
            if count >= 6:
                break

    @allowed_failure
    def test_preload_templates_and_langlinks(self):
        """Test preloading templates and langlinks works."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0
        # Use backlinks, as any backlink has at least one link
        links = mysite.pagebacklinks(mainpage, total=10)
        for page in mysite.preloadpages(links, langlinks=True, templates=True):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertEqual(len(page._revisions), 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
                self.assertTrue(hasattr(page, '_templates'))
                self.assertTrue(hasattr(page, '_langlinks'))
            count += 1
            if count >= 6:
                break


class TestDataSitePreloading(WikidataTestCase):

    """Test DataSite.preloaditempages for repo pages."""

    def test_item(self):
        """Test that ItemPage preloading works for Item objects."""
        datasite = self.get_repo()
        items = [pywikibot.ItemPage(datasite, 'q' + str(num))
                 for num in range(1, 6)]

        seen = []
        for item in datasite.preloaditempages(items):
            self.assertIsInstance(item, pywikibot.ItemPage)
            self.assertTrue(hasattr(item, '_content'))
            self.assertNotIn(item, seen)
            seen.append(item)
        self.assertEqual(len(seen), 5)

    def test_item_as_page(self):
        """Test that ItemPage preloading works for Page objects."""
        site = self.get_site()
        datasite = self.get_repo()
        pages = [pywikibot.Page(site, 'q' + str(num))
                 for num in range(1, 6)]

        seen = []
        for item in datasite.preloaditempages(pages):
            self.assertIsInstance(item, pywikibot.ItemPage)
            self.assertTrue(hasattr(item, '_content'))
            self.assertNotIn(item, seen)
            seen.append(item)
        self.assertEqual(len(seen), 5)


class TestDataSiteClientPreloading(DefaultWikidataClientTestCase):

    """Test DataSite.preloaditempages for client pages."""

    def test_non_item(self):
        """Test that ItemPage preloading works with Page generator."""
        mainpage = self.get_mainpage()
        datasite = self.get_repo()

        item = next(datasite.preloaditempages([mainpage]))
        self.assertIsInstance(item, pywikibot.ItemPage)
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q5296')


class TestDataSiteSearchEntities(WikidataTestCase):

    """Test DataSite.search_entities."""

    def test_general(self):
        """Test basic search_entities functionality."""
        datasite = self.get_repo()
        pages = datasite.search_entities('abc', 'en', limit=50)
        self.assertGreater(len(list(pages)), 0)
        self.assertLessEqual(len(list(pages)), 50)
        pages = datasite.search_entities('alphabet', 'en', type='property',
                                         limit=50)
        self.assertGreater(len(list(pages)), 0)
        self.assertLessEqual(len(list(pages)), 50)

    def test_continue(self):
        """Test that continue parameter in search_entities works."""
        datasite = self.get_repo()
        kwargs = {'limit': 50}
        pages = datasite.search_entities('Rembrandt', 'en', **kwargs)
        kwargs['continue'] = 1
        pages_continue = datasite.search_entities('Rembrandt', 'en', **kwargs)
        self.assertNotEqual(list(pages), list(pages_continue))

    def test_language_lists(self):
        """Test that languages returned by paraminfo and MW are the same."""
        site = self.get_site()
        lang_codes = site._paraminfo.parameter('wbsearchentities',
                                               'language')['type']
        lang_codes2 = [lang['code'] for lang in site._siteinfo.get('languages')]
        self.assertEqual(lang_codes, lang_codes2)

    def test_invalid_language(self):
        """Test behavior of search_entities with invalid language provided."""
        datasite = self.get_repo()
        self.assertRaises(ValueError, datasite.search_entities, 'abc',
                          'invalidlanguage')


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

    def test_enwp(self):
        """Test sametitle for enwp."""
        self.assertTrue(self.get_site('enwp').sametitle('Foo', 'foo'))
        self.assertFalse(self.get_site('enwp').sametitle(
            'Template:Test template', 'Template:Test Template'))

    def test_dewp(self):
        """Test sametitle for dewp."""
        site = self.get_site('dewp')
        self.assertTrue(site.sametitle('Foo', 'foo'))
        self.assertTrue(site.sametitle('Benutzer:Foo', 'User:Foo'))
        self.assertTrue(site.sametitle('Benutzerin:Foo', 'User:Foo'))
        self.assertTrue(site.sametitle('Benutzerin:Foo', 'Benutzer:Foo'))

    def test_enwt(self):
        """Test sametitle for enwt."""
        self.assertFalse(self.get_site('enwt').sametitle('Foo', 'foo'))

    def test_general(self, code):
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


class TestObsoleteSite(TestCase):

    """Test 'closed' and obsolete code sites."""

    # hostname() fails, so it is provided here otherwise the
    # test class fails with hostname not defined for mh.wikipedia.org
    sites = {
        'mhwp': {
            'family': 'wikipedia',
            'code': 'mh',
            'hostname': 'mh.wikipedia.org',
        },
        # pywikibot should never attempt to access jp.wikipedia.org,
        # however this entry ensures that there is a change in the builds
        # if jp.wikipedia.org goes offline.
        'jpwp': {
            'family': 'wikipedia',
            'code': 'jp',
            'hostname': 'jp.wikipedia.org',
        },
        'jawp': {
            'family': 'wikipedia',
            'code': 'ja',
        },
    }

    def test_locked_site(self):
        """Test Wikimedia closed/locked site."""
        site = self.get_site('mhwp')
        self.assertEqual(site.code, 'mh')
        self.assertIsInstance(site.obsolete, bool)
        self.assertTrue(site.obsolete)
        self.assertRaises(KeyError, site.hostname)
        r = http.fetch(uri='http://mh.wikipedia.org/w/api.php',
                       default_error_handling=False)
        self.assertEqual(r.status, 200)

    def test_removed_site(self):
        """Test Wikimedia offline site."""
        site = pywikibot.Site('ru-sib', 'wikipedia')
        self.assertIsInstance(site, pywikibot.site.RemovedSite)
        self.assertEqual(site.code, 'ru-sib')
        self.assertIsInstance(site.obsolete, bool)
        self.assertTrue(site.obsolete)
        self.assertRaises(KeyError, site.hostname)
        # See also http_tests, which tests that ru-sib.wikipedia.org is offline

    def test_alias_code_site(self):
        """Test Wikimedia site with an alias code."""
        site = self.get_site('jpwp')
        self.assertIsInstance(site.obsolete, bool)
        self.assertEqual(site.code, 'ja')
        self.assertFalse(site.obsolete)
        self.assertEqual(site.hostname(), 'ja.wikipedia.org')
        self.assertEqual(site.ssl_hostname(), 'ja.wikipedia.org')


class TestSingleCodeFamilySite(AlteredDefaultSiteTestCase):

    """Test site without other production sites in its family."""

    sites = {
        'wikia': {
            'family': 'wikia',
            'code': 'wikia',
        },
        'lyricwiki': {
            'family': 'lyricwiki',
            'code': 'en',
        },
        'commons': {
            'family': 'commons',
            'code': 'commons',
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

    def test_wikia(self):
        """Test www.wikia.com."""
        site = self.get_site('wikia')
        self.assertEqual(site.hostname(), 'www.wikia.com')
        self.assertEqual(site.code, 'wikia')
        self.assertIsInstance(site.namespaces, Mapping)
        self.assertFalse(site.obsolete)
        self.assertEqual(site.family.hostname('en'), 'www.wikia.com')
        self.assertEqual(site.family.hostname('wikia'), 'www.wikia.com')
        self.assertEqual(site.family.hostname('www'), 'www.wikia.com')

        pywikibot.config.family = 'wikia'
        pywikibot.config.mylang = 'de'

        site2 = pywikibot.Site('www', 'wikia')
        self.assertEqual(site2.code, 'wikia')
        self.assertFalse(site2.obsolete)
        self.assertEqual(site, site2)
        self.assertEqual(pywikibot.config.mylang, 'de')

        site2 = pywikibot.Site('really_invalid', 'wikia')
        self.assertEqual(site2.code, 'wikia')
        self.assertFalse(site2.obsolete)
        self.assertEqual(site, site2)
        self.assertEqual(pywikibot.config.mylang, 'de')

        site2 = pywikibot.Site('de', 'wikia')
        self.assertEqual(site2.code, 'wikia')
        self.assertFalse(site2.obsolete)
        self.assertEqual(site, site2)
        # When the code is the same as config.mylang, Site() changes mylang
        self.assertEqual(pywikibot.config.mylang, 'wikia')

    def test_lyrics(self):
        """Test lyrics.wikia.com."""
        site = self.get_site('lyricwiki')
        self.assertEqual(site.hostname(), 'lyrics.wikia.com')
        self.assertEqual(site.code, 'en')
        self.assertIsInstance(site.namespaces, Mapping)
        self.assertFalse(site.obsolete)
        self.assertEqual(site.family.hostname('en'), 'lyrics.wikia.com')

        self.assertEqual(site.family.hostname('lyrics'), 'lyrics.wikia.com')
        self.assertEqual(site.family.hostname('lyricwiki'), 'lyrics.wikia.com')

        self.assertRaises(pywikibot.UnknownSite, pywikibot.Site,
                          'lyricwiki', 'lyricwiki')

        self.assertRaises(pywikibot.UnknownSite, pywikibot.Site,
                          'de', 'lyricwiki')

    def test_commons(self):
        """Test Wikimedia Commons."""
        site = self.get_site('commons')
        self.assertEqual(site.hostname(), 'commons.wikimedia.org')
        self.assertEqual(site.code, 'commons')
        self.assertIsInstance(site.namespaces, Mapping)
        self.assertFalse(site.obsolete)

        self.assertEqual(site.family.hostname('en'), 'commons.wikimedia.org')

        pywikibot.config.family = 'commons'
        pywikibot.config.mylang = 'de'

        site2 = pywikibot.Site('en', 'commons')
        self.assertEqual(site2.code, 'commons')
        self.assertFalse(site2.obsolete)
        self.assertEqual(site, site2)
        self.assertEqual(pywikibot.config.mylang, 'de')

        site2 = pywikibot.Site('really_invalid', 'commons')
        self.assertEqual(site2.code, 'commons')
        self.assertFalse(site2.obsolete)
        self.assertEqual(site, site2)
        self.assertEqual(pywikibot.config.mylang, 'de')

        site2 = pywikibot.Site('de', 'commons')
        self.assertEqual(site2.code, 'commons')
        self.assertFalse(site2.obsolete)
        self.assertEqual(site, site2)
        # When the code is the same as config.mylang, Site() changes mylang
        self.assertEqual(pywikibot.config.mylang, 'commons')

    def test_wikidata(self):
        """Test Wikidata family, with sites for test and production."""
        site = self.get_site('wikidata')
        self.assertEqual(site.hostname(), 'www.wikidata.org')
        self.assertEqual(site.code, 'wikidata')
        self.assertIsInstance(site.namespaces, Mapping)
        self.assertFalse(site.obsolete)

        self.assertRaises(KeyError, site.family.hostname, 'en')

        pywikibot.config.family = 'wikidata'
        pywikibot.config.mylang = 'en'

        site2 = pywikibot.Site('test')
        self.assertEqual(site2.hostname(), 'test.wikidata.org')
        self.assertEqual(site2.code, 'test')

        # Languages cant be used due to T71255
        self.assertRaises(pywikibot.UnknownSite,
                          pywikibot.Site, 'en', 'wikidata')


class TestNonMWAPISite(TestCase):

    """Test the BaseSite subclass, site.NonMWAPISite."""

    net = False

    def testNonMWsites(self):
        """Test NonMWAPISite for sites not using MediaWiki."""
        self._run_test("http://moinmo.in/$1")
        self._run_test("http://twiki.org/cgi-bin/view/$1")
        self._run_test("http://www.usemod.com/cgi-bin/wiki.pl?$1")
        self._run_test("https://developer.mozilla.org/en/docs/$1")
        self._run_test("http://www.tvtropes.org/pmwiki/pmwiki.php/Main/$1")

    def _run_test(self, url):
        """Run test method."""
        site = pywikibot.site.NonMWAPISite(url)
        with self.assertRaises(NotImplementedError):
            site.attr


class TestSiteProofreadinfo(DefaultSiteTestCase):

    """Test proofreadinfo information."""

    sites = {
        'en.ws': {
            'family': 'wikisource',
            'code': 'en',
        },
        'en.wp': {
            'family': 'wikipedia',
            'code': 'en',
        },
    }

    cached = True

    def test_cache_proofreadinfo_on_site_with_ProofreadPage(self):
        """Test Site._cache_proofreadinfo()."""
        site = self.get_site('en.ws')
        ql_res = {0: u'Without text', 1: u'Not proofread', 2: u'Problematic',
                  3: u'Proofread', 4: u'Validated'}

        site._cache_proofreadinfo()
        self.assertEqual(site.namespaces[106], site.proofread_index_ns)
        self.assertEqual(site.namespaces[104], site.proofread_page_ns)
        self.assertEqual(site.proofread_levels, ql_res)
        self.assertEqual(site.namespaces[106], site.proofread_index_ns)
        del site._proofread_page_ns  # Check that property reloads.
        self.assertEqual(site.namespaces[104], site.proofread_page_ns)

    def test_cache_proofreadinfo_on_site_without_ProofreadPage(self):
        """Test Site._cache_proofreadinfo()."""
        site = self.get_site('en.wp')
        self.assertRaises(pywikibot.UnknownExtension, site._cache_proofreadinfo)
        self.assertRaises(pywikibot.UnknownExtension, lambda x: x.proofread_index_ns, site)
        self.assertRaises(pywikibot.UnknownExtension, lambda x: x.proofread_page_ns, site)
        self.assertRaises(pywikibot.UnknownExtension, lambda x: x.proofread_levels, site)


class TestPropertyNames(DefaultSiteTestCase):

    """Test Special:PagesWithProp method."""

    sites = {
        'en.ws': {
            'family': 'wikisource',
            'code': 'en',
        },
        'de.wp': {
            'family': 'wikipedia',
            'code': 'de',
        },
    }

    cached = True

    def test_get_property_names(self, key):
        """Test get_property_names method."""
        mysite = self.get_site(key)
        pnames = mysite.get_property_names()
        self.assertIsInstance(pnames, list)
        for item in ('defaultsort', 'disambiguation', 'displaytitle',
                     'forcetoc', 'graph_specs', 'hiddencat', 'newsectionlink',
                     'noeditsection', 'noexternallanglinks', 'nogallery',
                     'noindex', 'nonewsectionlink', 'notoc', 'score',
                     'templatedata', 'wikibase-badge-Q17437796',
                     'wikibase_item'):
            self.assertIn(item, pnames)


class TestPageFromWikibase(DefaultSiteTestCase):

    """Test page_from_repository method."""

    sites = {
        'it.wb': {
            'family': 'wikibooks',
            'code': 'it',
            'result': 'Hello world',
        },
        'de.wp': {
            'family': 'wikipedia',
            'code': 'de',
            'result': 'Hallo-Welt-Programm',
        },
        'en.wp': {
            'family': 'wikipedia',
            'code': 'en',
            'result': '"Hello, World!" program',
        },
    }

    ITEM = 'Q131303'

    def test_page_from_repository(self, key):
        """Validate page_from_repository."""
        site = self.get_site(key)
        page = site.page_from_repository(self.ITEM)
        self.assertIsInstance(page, pywikibot.Page)
        self.assertEqual(page.title(), self.sites[key]['result'])

    def test_page_from_repository_none(self):
        """Validate page_from_repository return NoneType."""
        site = pywikibot.Site('pdc', 'wikipedia')
        page = site.page_from_repository(self.ITEM)
        self.assertIsNone(page)


class TestCategoryFromWikibase(DefaultSiteTestCase):

    """Test page_from_repository method."""

    sites = {
        'it.wb': {
            'family': 'wikinews',
            'code': 'it',
            'result': 'Categoria:2016',
        },
        'de.wp': {
            'family': 'wikipedia',
            'code': 'de',
            'result': 'Kategorie:2016',
        },
        'en.wp': {
            'family': 'wikipedia',
            'code': 'en',
            'result': 'Category:2016',
        },
    }

    ITEM = 'Q6939656'

    def test_page_from_repository(self, key):
        """Validate page_from_repository."""
        site = self.get_site(key)
        page = site.page_from_repository(self.ITEM)
        self.assertIsInstance(page, pywikibot.Category)
        self.assertEqual(page.title(), self.sites[key]['result'])

    def test_page_from_repository_none(self):
        """Validate page_from_repository return NoneType."""
        site = pywikibot.Site('pdc', 'wikipedia')
        page = site.page_from_repository(self.ITEM)
        self.assertIsNone(page)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
