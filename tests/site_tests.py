# -*- coding: utf-8 -*-
"""Tests for the site module."""
#
# (C) Pywikibot team, 2008-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import pickle
import random
import re
import sys
import time

try:
    from collections.abc import Iterable, Mapping
except ImportError:  # Python 2.7
    from collections import Iterable, Mapping
from datetime import datetime
import threading

import pywikibot

from pywikibot import async_request, config, page_put_queue
from pywikibot.comms import http
from pywikibot.data import api
from pywikibot.exceptions import HiddenKeyError
from pywikibot.tools import (
    PY2,
    StringTypes as basestring,
    suppress_warnings,
    UnicodeType as unicode,
)

from tests import patch, unittest_print, MagicMock
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
from tests.utils import entered_loop

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
            self.skipTest(error_msg)

        self.token = token
        self._orig_wallet = self.site.tokens
        self.site.tokens = pywikibot.site.TokenWallet(self.site)

    def tearDown(self):
        """Restore site tokens."""
        self.site.tokens = self._orig_wallet
        super(TokenTestBase, self).tearDown()


class TestSiteObjectDeprecatedFunctions(DefaultSiteTestCase,
                                        DeprecationTestCase):

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
        if self.site.mw_version < '1.16':
            self.skipTest('requires v1.16+')

        old = self.site.siteinfo('general')
        self.assertIn('time', old)
        self.assertEqual(old, self.site.siteinfo['general'])
        self.assertEqual(self.site.siteinfo('general'), old)
        # Siteinfo always returns copies so it's not possible to directly
        # check if they are the same dict or if they have been rerequested
        # unless the content also changes so force that the content changes
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
        self.assertIn('statistics',
                      self.site.siteinfo('statistics', dump=True))
        self.assertOneDeprecationParts('Calling siteinfo',
                                       'itself as a dictionary')

    def test_language_method(self):
        """Test if the language method returns the same as lang property."""
        self.assertEqual(self.site.language(), self.site.lang)
        self.assertOneDeprecation()

    def test_allpages_filterredir_True(self):
        """Test that filterredir set to 'only' is deprecated to True."""
        for page in self.site.allpages(filterredir='only', total=1):
            self.assertTrue(page.isRedirectPage())
        self.assertOneDeprecation()

    def test_allpages_filterredir_False(self):
        """Test if filterredir's bool is False it's deprecated to False."""
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


class TestSiteDryDeprecatedFunctions(DefaultDrySiteTestCase,
                                     DeprecationTestCase):

    """Test cases for Site deprecated methods without a user."""

    def test_namespaces_callable(self):
        """Test that namespaces is callable and returns itself."""
        site = self.get_site()
        self.assertIs(site.namespaces(), site.namespaces)
        self.assertOneDeprecationParts('Calling the namespaces property',
                                       'it directly')


class TestBaseSiteProperties(TestCase):

    """Test properties for BaseSite."""

    sites = {
        'enwikinews': {
            'family': 'wikinews',
            'code': 'en',
            'result': ('/doc',),
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

    def test_pickle_ability(self):
        """Test pickle ability."""
        mysite = self.get_site()
        mysite_str = pickle.dumps(mysite, protocol=config.pickle_protocol)
        mysite_pickled = pickle.loads(mysite_str)
        self.assertEqual(mysite, mysite_pickled)

    def test_repr(self):
        """Test __repr__."""
        code = self.site.family.obsolete.get(self.code) or self.code
        expect = 'Site("{0}", "{1}")'.format(code, self.family)
        self.assertStringMethod(str.endswith, repr(self.site), expect)

    def test_base_methods(self):
        """Test cases for BaseSite methods."""
        mysite = self.get_site()
        code = self.site.family.obsolete.get(self.code) or self.code
        self.assertEqual(mysite.family.name, self.family)
        self.assertEqual(mysite.code, code)
        self.assertIsInstance(mysite.lang, basestring)
        self.assertEqual(mysite, pywikibot.Site(self.code, self.family))
        self.assertIsInstance(mysite.user(), (basestring, type(None)))
        self.assertEqual(mysite.sitename(), '%s:%s' % (self.family, code))
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

        foo = unicode(pywikibot.Link('foo', source=mysite))
        if self.site.namespaces[0].case == 'case-sensitive':
            self.assertEqual(foo, '[[foo]]')
        else:
            self.assertEqual(foo, '[[Foo]]')

        self.assertFalse(mysite.isInterwikiLink('foo'))
        self.assertIsInstance(mysite.redirectRegex().pattern, basestring)
        self.assertIsInstance(mysite.category_on_one_line(), bool)
        self.assertTrue(mysite.sametitle('Template:Test', 'Template:Test'))
        self.assertTrue(mysite.sametitle('Template: Test', 'Template:   Test'))
        self.assertTrue(mysite.sametitle('Test name', 'Test name'))
        self.assertFalse(mysite.sametitle('Test name', 'Test Name'))
        # User, MediaWiki (both since 1.16) and Special are always
        # first-letter (== only first non-namespace letter is case insensitive)
        # See also: https://www.mediawiki.org/wiki/Manual:$wgCapitalLinks
        self.assertTrue(mysite.sametitle('Special:Always', 'Special:always'))
        if mysite.mw_version >= '1.16':
            self.assertTrue(mysite.sametitle('User:Always', 'User:always'))
            self.assertTrue(mysite.sametitle('MediaWiki:Always',
                                             'MediaWiki:always'))

    def test_constructors(self):
        """Test cases for site constructors."""
        test_list = [
            ['enwiki', ('en', 'wikipedia')],
            ['eswikisource', ('es', 'wikisource')],
            ['dewikinews', ('de', 'wikinews')],
            ['ukwikivoyage', ('uk', 'wikivoyage')],
            ['metawiki', ('meta', 'meta')],
            ['commonswiki', ('commons', 'commons')],
            ['wikidatawiki', ('wikidata', 'wikidata')],
            ['testwikidatawiki', ('test', 'wikidata')],
            ['testwiki', ('test', 'wikipedia')],  # see T225729, T228300
            ['test2wiki', ('test2', 'wikipedia')],  # see T225729
            ['sourceswiki', ('mul', 'wikisource')],  # see T226960
        ]
        if isinstance(self.site.family, pywikibot.family.WikimediaFamily):
            site = self.site
        else:
            site = None
        for dbname, site_tuple in test_list:
            with self.subTest(dbname=dbname):
                self.assertEqual(
                    pywikibot.site.APISite.fromDBName(dbname, site),
                    pywikibot.Site(*site_tuple))

    def test_language_methods(self):
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

    def test_namespace_methods(self):
        """Test cases for methods manipulating namespace names."""
        mysite = self.get_site()
        ns = mysite.namespaces
        self.assertIsInstance(ns, Mapping)
        self.assertTrue(all(x in ns for x in range(0, 16)))
        # built-in namespaces always present
        self.assertIsInstance(mysite.ns_normalize('project'), basestring)
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
            with self.subTest(message=msg, lang=mysite.lang):
                self.assertTrue(mysite.has_mediawiki_message(msg))
                self.assertIsInstance(mysite.mediawiki_message(msg),
                                      basestring)
                self.assertEqual(
                    mysite.mediawiki_message(msg),
                    mysite.mediawiki_message(msg, lang=mysite.lang))

            with self.subTest(message=msg, lang='de'):
                self.assertTrue(mysite.has_mediawiki_message(msg, lang='de'))
                self.assertIsInstance(mysite.mediawiki_message(msg, lang='de'),
                                      basestring)

        with self.subTest(message='nosuchmessage'):
            self.assertFalse(mysite.has_mediawiki_message('nosuchmessage'))
            self.assertRaises(KeyError, mysite.mediawiki_message,
                              'nosuchmessage')

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
        with self.subTest(messages=months, lang1='af', lang2='an'):
            self.assertLength(mysite.mediawiki_messages(months, 'af'), 12)
            self.assertLength(mysite.mediawiki_messages(months, 'an'), 12)
            self.assertNotEqual(mysite.mediawiki_messages(months, 'af'),
                                mysite.mediawiki_messages(months, 'an'))

        # mediawiki_messages must be given a list; using a string will split it
        with self.subTest(messages='about'):
            self.assertRaises(KeyError, self.site.mediawiki_messages, 'about')

        msg = ('nosuchmessage1', 'about', 'aboutpage', 'nosuchmessage')
        with self.subTest(messages=msg):
            self.assertFalse(mysite.has_all_mediawiki_messages(msg))
            self.assertRaises(KeyError, mysite.mediawiki_messages, msg)

        with self.subTest(test='server_time'):
            self.assertIsInstance(mysite.server_time(), pywikibot.Timestamp)
            ts = mysite.getcurrenttimestamp()
            self.assertIsInstance(ts, basestring)
            self.assertRegex(
                ts, r'(19|20)\d\d[0-1]\d[0-3]\d[0-2]\d[0-5]\d[0-5]\d')

        with self.subTest(test='months_names'):
            self.assertIsInstance(mysite.months_names, list)
            self.assertLength(mysite.months_names, 12)
            self.assertTrue(all(isinstance(month, tuple)
                                for month in mysite.months_names))
            for month in mysite.months_names:
                self.assertLength(month, 2)

        with self.subTest(test='list_to_text'):
            self.assertEqual(mysite.list_to_text(('pywikibot',)), 'pywikibot')

    def test_english_specific_methods(self):
        """Test Site methods using English specific inputs and outputs."""
        mysite = self.get_site()
        if mysite.lang != 'en':
            self.skipTest(
                'English-specific tests not valid on {}'.format(mysite))

        self.assertEqual(mysite.months_names[4], ('May', 'May'))
        self.assertEqual(mysite.list_to_text(('Pride', 'Prejudice')),
                         'Pride and Prejudice')
        self.assertEqual(mysite.list_to_text(('This', 'that', 'the other')),
                         'This, that and the other')

    def test_page_methods(self):
        """Test ApiSite methods for getting page-specific info."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        with suppress_warnings('pywikibot.site.APISite.page_exists',
                               DeprecationWarning):
            self.assertIsInstance(mysite.page_exists(mainpage), bool)
        self.assertIsInstance(mysite.page_restrictions(mainpage), dict)
        self.assertIsInstance(mysite.page_can_be_edited(mainpage), bool)
        self.assertIsInstance(mysite.page_isredirect(mainpage), bool)
        if mysite.page_isredirect(mainpage):
            self.assertIsInstance(mysite.getredirtarget(mainpage),
                                  pywikibot.Page)
        else:
            self.assertRaises(pywikibot.IsNotRedirectPage,
                              mysite.getredirtarget, mainpage)
        a = list(mysite.preloadpages([mainpage]))
        self.assertLength(a, int(mainpage.exists()))
        if a:
            self.assertEqual(a[0], mainpage)


class TestSiteGenerators(DefaultSiteTestCase):
    """Test cases for Site methods."""

    cached = True

    def setUp(self):
        """Initialize self.site and self.mainpage."""
        super(TestSiteGenerators, self).setUp()
        self.site = self.get_site()
        self.mainpage = self.get_mainpage()

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

    def test_pagereferences(self):
        """Test Site.pagereferences."""
        # pagereferences includes both backlinks and embeddedin
        backlinks = set(self.site.pagebacklinks(self.mainpage, namespaces=[0]))
        embedded = set(self.site.page_embeddedin(self.mainpage,
                                                 namespaces=[0]))
        refs = set(self.site.pagereferences(self.mainpage, namespaces=[0]))

        self.assertLessEqual(backlinks, refs)
        self.assertLessEqual(embedded, refs)
        self.assertEqual(refs, backlinks | embedded)

    def test_backlinks(self):
        """Test Site.pagebacklinks."""
        backlinks_ns_0 = set(self.site.pagebacklinks(
            self.mainpage, namespaces=[0]))
        backlinks_ns_0_2 = set(self.site.pagebacklinks(
            self.mainpage, namespaces=[0, 2]))

        # only non-redirects:
        filtered = set(self.site.pagebacklinks(
            self.mainpage, namespaces=0, filter_redirects=False))
        # only redirects:
        redirs = set(self.site.pagebacklinks(
            self.mainpage, namespaces=0, filter_redirects=True))
        # including links to redirect pages (but not the redirects):
        indirect = set(
            self.site.pagebacklinks(self.mainpage, namespaces=[0],
                                    follow_redirects=True,
                                    filter_redirects=False))

        for bl in backlinks_ns_0:
            self.assertIsInstance(bl, pywikibot.Page)

        self.assertEqual(filtered & redirs, set())
        self.assertEqual(indirect & redirs, set())
        self.assertLessEqual(filtered, indirect)
        self.assertLessEqual(filtered, backlinks_ns_0)
        self.assertLessEqual(redirs, backlinks_ns_0)
        self.assertLessEqual(backlinks_ns_0, backlinks_ns_0_2)

    def test_embeddedin(self):
        """Test Site.page_embeddedin."""
        embedded_ns_0 = set(self.site.page_embeddedin(
            self.mainpage, namespaces=[0]))
        embedded_ns_0_2 = set(self.site.page_embeddedin(
            self.mainpage, namespaces=[0, 2]))
        redirs = set(self.site.page_embeddedin(
            self.mainpage, filter_redirects=True, namespaces=[0]))
        no_redirs = set(self.site.page_embeddedin(
            self.mainpage, filter_redirects=False, namespaces=[0]))

        for ei in embedded_ns_0:
            self.assertIsInstance(ei, pywikibot.Page)

        self.assertLessEqual(redirs, embedded_ns_0)
        self.assertLessEqual(no_redirs, embedded_ns_0)
        self.assertLessEqual(embedded_ns_0, embedded_ns_0_2)

    def test_pagecategories(self):
        """Test Site.pagecategories."""
        for cat in self.site.pagecategories(self.mainpage):
            self.assertIsInstance(cat, pywikibot.Category)

    def test_categorymembers(self):
        """Test Site.categorymembers."""
        cats = list(self.site.pagecategories(self.mainpage))
        if len(cats) == 0:
            self.skipTest('Main page is not in any categories.')
        else:
            for cm in self.site.categorymembers(cats[0]):
                self.assertIsInstance(cm, pywikibot.Page)

    def test_pageimages(self):
        """Test Site.pageimages."""
        for im in self.site.pageimages(self.mainpage):
            self.assertIsInstance(im, pywikibot.FilePage)

    def test_pagetemplates(self):
        """Test Site.pagetemplates."""
        tl_gen = self.site.pagetemplates(self.mainpage)
        expected_params = {
            'titles': [self.mainpage.title()],
            'prop': ['info', 'imageinfo', 'categoryinfo'],
            'inprop': ['protection'],
            'iilimit': ['max'],
            'iiprop': ['timestamp', 'user', 'comment', 'url', 'size',
                       'sha1', 'metadata'],
            'generator': ['templates'], 'action': ['query'],
            'indexpageids': [True]}
        if self.site.mw_version >= '1.21':
            expected_params['continue'] = [True]

        self.assertEqual(tl_gen.request._params, expected_params)

        tl_gen = self.site.pagetemplates(self.mainpage, namespaces=[10])
        expected_params['gtlnamespace'] = [10]
        self.assertEqual(tl_gen.request._params, expected_params)
        for te in tl_gen:
            self.assertIsInstance(te, pywikibot.Page)
            self.assertEqual(te.namespace(), 10)

    def test_pagelanglinks(self):
        """Test Site.pagelanglinks."""
        for ll in self.site.pagelanglinks(self.mainpage):
            self.assertIsInstance(ll, pywikibot.Link)

    def test_page_extlinks(self):
        """Test Site.extlinks."""
        for el in self.site.page_extlinks(self.mainpage):
            self.assertIsInstance(el, basestring)

    def test_pagelinks(self):
        """Test Site.pagelinks."""
        links_gen = self.site.pagelinks(self.mainpage)
        gen_params = links_gen.request._params.copy()
        expected_params = {
            'redirects': [False],
            'prop': ['info', 'imageinfo', 'categoryinfo'],
            'inprop': ['protection'],
            'iilimit': ['max'],
            'iiprop': ['timestamp', 'user', 'comment', 'url', 'size',
                       'sha1', 'metadata'], 'generator': ['links'],
            'action': ['query'], 'indexpageids': [True]}
        if 'pageids' in gen_params:
            expected_params['pageids'] = [str(self.mainpage.pageid)]
        else:
            expected_params['titles'] = [self.mainpage.title()]
        if self.site.mw_version >= '1.21':
            expected_params['continue'] = [True]

        self.assertEqual(gen_params, expected_params)

        links_gen = self.site.pagelinks(self.mainpage, namespaces=[0, 1])
        gen_params = links_gen.request._params.copy()
        expected_params['gplnamespace'] = [0, 1]
        self.assertEqual(gen_params, expected_params)
        self.assertPagesInNamespaces(links_gen, {0, 1})

        for target in self.site.preloadpages(
                self.site.pagelinks(self.mainpage, follow_redirects=True,
                                    total=5)):
            self.assertIsInstance(target, pywikibot.Page)
            self.assertFalse(target.isRedirectPage())

    def test_allpages(self):
        """Test the site.allpages() method."""
        mysite = self.get_site()
        fwd = list(mysite.allpages(total=10))
        self.assertLessEqual(len(fwd), 10)
        for page in fwd:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            self.assertEqual(page.namespace(), 0)
        rev = list(mysite.allpages(reverse=True, start='Aa', total=12))
        self.assertLessEqual(len(rev), 12)
        for page in rev:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            self.assertEqual(page.namespace(), 0)
            self.assertLessEqual(page.title(), 'Aa')
        for page in mysite.allpages(start='Py', total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            self.assertEqual(page.namespace(), 0)
            self.assertGreaterEqual(page.title(), 'Py')
        for page in mysite.allpages(prefix='Pre', total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title().startswith('Pre'))
        for page in mysite.allpages(namespace=1, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            self.assertEqual(page.namespace(), 1)
        for page in mysite.allpages(filterredir=True, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.isRedirectPage())
        for page in mysite.allpages(filterredir=False, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            self.assertEqual(page.namespace(), 0)
            self.assertFalse(page.isRedirectPage())

    def test_allpages_langlinks_enabled(self):
        """Test allpages with langlinks enabled."""
        mysite = self.get_site()
        for page in mysite.allpages(
                filterlanglinks=True, total=3, namespace=4):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            self.assertEqual(page.namespace(), 4)
            self.assertNotEqual(page.langlinks(), [])

    def test_allpages_langlinks_disabled(self):
        """Test allpages with langlinks disabled."""
        mysite = self.get_site()
        for page in mysite.allpages(filterlanglinks=False, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            self.assertEqual(page.namespace(), 0)
            self.assertEqual(page.langlinks(), [])

    def test_allpages_pagesize(self):
        """Test allpages with page maxsize parameter."""
        mysite = self.get_site()
        for page in mysite.allpages(minsize=100, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            self.assertGreaterEqual(len(page.text.encode(mysite.encoding())),
                                    100)
        for page in mysite.allpages(maxsize=200, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            if (len(page.text.encode(mysite.encoding())) > 200
                    and mysite.data_repository() == mysite):
                unittest_print(
                    '{}.text is > 200 bytes while raw JSON is <= 200'
                    .format(page))
                continue
            self.assertLessEqual(len(page.text.encode(mysite.encoding())), 200)

    def test_allpages_protection(self):
        """Test allpages with protect_type parameter."""
        mysite = self.get_site()
        for page in mysite.allpages(protect_type='edit', total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            self.assertIn('edit', page._protection)
        for page in mysite.allpages(protect_type='edit',
                                    protect_level='sysop', total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(page.exists())
            self.assertIn('edit', page._protection)
            self.assertIn('sysop', page._protection['edit'])

    def test_all_links(self):
        """Test the site.alllinks() method."""
        mysite = self.get_site()
        fwd = list(mysite.alllinks(total=10))
        self.assertLessEqual(len(fwd), 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page) for link in fwd))
        uniq = list(mysite.alllinks(total=10, unique=True))
        self.assertTrue(all(link in uniq for link in fwd))
        for page in mysite.alllinks(start='Link', total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 0)
            self.assertGreaterEqual(page.title(), 'Link')
        for page in mysite.alllinks(prefix='Fix', total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title().startswith('Fix'))
        for page in mysite.alllinks(namespace=1, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 1)
        for page in mysite.alllinks(start='From', namespace=4, fromids=True,
                                    total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertGreaterEqual(page.title(with_ns=False), 'From')
            self.assertTrue(hasattr(page, '_fromid'))
        errgen = mysite.alllinks(unique=True, fromids=True)
        self.assertRaises(pywikibot.Error, next, errgen)

    def test_all_categories(self):
        """Test the site.allcategories() method."""
        mysite = self.get_site()
        ac = list(mysite.allcategories(total=10))
        self.assertLessEqual(len(ac), 10)
        self.assertTrue(all(isinstance(cat, pywikibot.Category)
                            for cat in ac))
        for cat in mysite.allcategories(total=5, start='Abc'):
            self.assertIsInstance(cat, pywikibot.Category)
            self.assertGreaterEqual(cat.title(with_ns=False), 'Abc')
        for cat in mysite.allcategories(total=5, prefix='Def'):
            self.assertIsInstance(cat, pywikibot.Category)
            self.assertTrue(cat.title(with_ns=False).startswith('Def'))
        # Bug T17985 - reverse and start combined; fixed in v 1.14
        for cat in mysite.allcategories(total=5, start='Hij', reverse=True):
            self.assertIsInstance(cat, pywikibot.Category)
            self.assertLessEqual(cat.title(with_ns=False), 'Hij')

    def test_all_images(self):
        """Test the site.allimages() method."""
        mysite = self.get_site()
        ai = list(mysite.allimages(total=10))
        self.assertLessEqual(len(ai), 10)
        self.assertTrue(all(isinstance(image, pywikibot.FilePage)
                            for image in ai))
        for impage in mysite.allimages(start='Ba', total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(impage.exists())
            self.assertGreaterEqual(impage.title(with_ns=False), 'Ba')
        # Bug T17985 - reverse and start combined; fixed in v 1.14
        for impage in mysite.allimages(start='Da', reverse=True, total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(impage.exists())
            self.assertLessEqual(impage.title(with_ns=False), 'Da')
        for impage in mysite.allimages(prefix='Ch', total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(impage.exists())
            self.assertTrue(impage.title(with_ns=False).startswith('Ch'))
        for impage in mysite.allimages(minsize=100, total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(impage.exists())
            self.assertGreaterEqual(impage.latest_file_info['size'], 100)
        for impage in mysite.allimages(maxsize=2000, total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(impage.exists())
            self.assertLessEqual(impage.latest_file_info['size'], 2000)

    def test_newfiles(self):
        """Test the site.newfiles() method."""
        my_site = self.get_site()
        with suppress_warnings(category=DeprecationWarning):
            gen = my_site.newfiles(total=10)
        the_list = list(gen)
        self.assertLessEqual(len(the_list), 10)
        self.assertTrue(all(isinstance(tup, tuple) and len(tup) == 4
                            for tup in the_list))
        self.assertTrue(all(isinstance(tup[0], pywikibot.FilePage)
                            for tup in the_list))
        self.assertTrue(all(isinstance(tup[1], pywikibot.Timestamp)
                            for tup in the_list))
        self.assertTrue(all(isinstance(tup[2], unicode) for tup in the_list))
        self.assertTrue(all(isinstance(tup[3], unicode) for tup in the_list))

    def test_querypage(self):
        """Test the site.querypage() method."""
        mysite = self.get_site()
        pages = list(mysite.querypage('Longpages', total=10))

        self.assertTrue(all(isinstance(p, pywikibot.Page) for p in pages))
        self.assertRaises(AssertionError, mysite.querypage, 'LongpageX')

    def test_longpages(self):
        """Test the site.longpages() method."""
        mysite = self.get_site()
        longpages = list(mysite.longpages(total=10))

        # Make sure each object returned by site.longpages() is
        # a tuple of a Page object and an int
        self.assertTrue(all(isinstance(tup, tuple) and len(tup) == 2
                            for tup in longpages))
        self.assertTrue(all(isinstance(tup[0], pywikibot.Page)
                            for tup in longpages))
        self.assertTrue(all(isinstance(tup[1], int) for tup in longpages))

    def test_shortpages(self):
        """Test the site.shortpages() method."""
        mysite = self.get_site()
        shortpages = list(mysite.shortpages(total=10))

        # Make sure each object returned by site.shortpages() is
        # a tuple of a Page object and an int
        self.assertTrue(all(isinstance(tup, tuple) and len(tup) == 2
                            for tup in shortpages))
        self.assertTrue(all(isinstance(tup[0], pywikibot.Page)
                            for tup in shortpages))
        self.assertTrue(all(isinstance(tup[1], int) for tup in shortpages))

    def test_ancientpages(self):
        """Test the site.ancientpages() method."""
        mysite = self.get_site()
        ancientpages = list(mysite.ancientpages(total=10))

        # Make sure each object returned by site.ancientpages() is
        # a tuple of a Page object and a Timestamp object
        self.assertTrue(all(isinstance(tup, tuple) and len(tup) == 2
                            for tup in ancientpages))
        self.assertTrue(all(isinstance(tup[0], pywikibot.Page)
                            for tup in ancientpages))
        self.assertTrue(all(isinstance(tup[1], pywikibot.Timestamp)
                            for tup in ancientpages))

    def test_unwatchedpages(self):
        """Test the site.unwatchedpages() method."""
        mysite = self.get_site()
        try:
            unwatchedpages = list(mysite.unwatchedpages(total=10))
        except api.APIError as error:
            if error.code in ('specialpage-cantexecute',
                              'gqpspecialpage-cantexecute'):
                # User must have correct permissions to use
                # Special:UnwatchedPages
                self.skipTest(error)
            raise

        # Make sure each object returned by site.unwatchedpages() is a
        # Page object
        self.assertTrue(all(isinstance(p, pywikibot.Page)
                            for p in unwatchedpages))

    def test_blocks(self):
        """Test the site.blocks() method."""
        mysite = self.get_site()
        props = ('id', 'by', 'timestamp', 'expiry', 'reason')

        with self.subTest(total=10, reverse=False):
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

        with self.subTest(total=10, reverse=True):
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

        ip = '80.100.22.71'
        with self.subTest(users=ip):
            for block in mysite.blocks(users=ip, total=5):
                self.assertIsInstance(block, dict)
                self.assertEqual(block['user'], ip)

        low = pywikibot.Timestamp.fromISOformat('2008-08-03T00:00:01Z')
        high = pywikibot.Timestamp.fromISOformat('2008-08-03T23:59:59Z')

        with self.subTest(starttime=low):
            for block in mysite.blocks(starttime=low, total=5):
                self.assertIsInstance(block, dict)
                for prop in props:
                    self.assertIn(prop, block)

        with self.subTest(endtime=high):
            for block in mysite.blocks(endtime=high, total=5):
                self.assertIsInstance(block, dict)
                for prop in props:
                    self.assertIn(prop, block)

        with self.subTest(starttime=high, endtime=low, reverse=False):
            for block in mysite.blocks(starttime=high, endtime=low, total=5):
                self.assertIsInstance(block, dict)
                for prop in props:
                    self.assertIn(prop, block)

        with self.subTest(starttime=low, endtime=high, reverse=True):
            for block in mysite.blocks(starttime=low, endtime=high,
                                       reverse=True, total=5):
                self.assertIsInstance(block, dict)
                for prop in props:
                    self.assertIn(prop, block)

        # starttime earlier than endtime
        with self.subTest(starttime=low, endtime=high, reverse=False):
            self.assertRaises(AssertionError, mysite.blocks, total=5,
                              starttime=low, endtime=high)

        # reverse: endtime earlier than starttime
        with self.subTest(starttime=high, endtime=low, reverse=True):
            self.assertRaises(AssertionError, mysite.blocks, total=5,
                              starttime=high, endtime=low, reverse=True)

    def test_exturl_usage(self):
        """Test the site.exturlusage() method."""
        mysite = self.get_site()
        url = 'www.google.com'
        eu = list(mysite.exturlusage(url, total=10))
        self.assertLessEqual(len(eu), 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page)
                            for link in eu))
        for link in mysite.exturlusage(url, namespaces=[2, 3], total=5):
            self.assertIsInstance(link, pywikibot.Page)
            self.assertIn(link.namespace(), (2, 3))

    def test_protectedpages_create(self):
        """Test that protectedpages returns protected page titles."""
        if self.site.mw_version < '1.15':
            self.skipTest('requires v1.15+')

        pages = list(self.get_site().protectedpages(type='create', total=10))
        # Do not check for the existence of pages as they might exist (T205883)
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
            self.skipTest(
                'The site "{0}" has no protected pages in main namespace.'
                .format(site))
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

    def test_pages_with_property(self):
        """Test pages_with_property method."""
        if self.site.mw_version < '1.21':
            self.skipTest('requires v1.21+')
        mysite = self.get_site()
        pnames = mysite.get_property_names()
        for item in ('defaultsort', 'disambiguation', 'displaytitle',
                     'hiddencat', 'invalid_property'):
            if item in pnames:
                for page in mysite.pages_with_property(item, total=5):
                    self.assertIsInstance(page, pywikibot.Page)
                    self.assertTrue(page.exists())
                    if item == 'disambiguation':
                        self.assertTrue(page.isDisambig)
            else:
                with self.assertRaises(NotImplementedError):
                    mysite.pages_with_property(item)
                    self.fail(
                        'NotImplementedError not raised for {0}'.format(item))

    def test_unconnected(self):
        """Test site.unconnected_pages method."""
        if not self.site.data_repository():
            self.skipTest('Site is not using a Wikibase repository')
        upgen = self.site.unconnected_pages(total=3)
        self.assertDictEqual(
            upgen.request._params, {
                'gqppage': ['UnconnectedPages'],
                'prop': ['info', 'imageinfo', 'categoryinfo'],
                'inprop': ['protection'],
                'iilimit': ['max'],
                'iiprop': ['timestamp', 'user', 'comment', 'url', 'size',
                           'sha1', 'metadata'],
                'generator': ['querypage'], 'action': ['query'],
                'indexpageids': [True], 'continue': [True]})
        self.assertLessEqual(len(tuple(upgen)), 3)

    def test_assert_valid_iter_params(self):
        """Test site.assert_valid_iter_params method."""
        func = self.site.assert_valid_iter_params

        # reverse=False, is_ts=False
        self.assertIsNone(func('m', 1, 2, False, False))
        self.assertRaises(AssertionError, func, 'm', 2, 1, False, False)

        # reverse=False, is_ts=True
        self.assertIsNone(func('m', 2, 1, False, True))
        self.assertRaises(AssertionError, func, 'm', 1, 2, False, True)

        # reverse=True, is_ts=False
        self.assertIsNone(func('m', 2, 1, True, False))
        self.assertRaises(AssertionError, func, 'm', 1, 2, True, False)

        # reverse=True, is_ts=True
        self.assertIsNone(func('m', 1, 2, True, True))
        self.assertRaises(AssertionError, func, 'm', 2, 1, True, True)


class TestLockingPage(DefaultSiteTestCase):
    """Test cases for lock/unlock a page within threads."""

    cached = True

    def worker(self):
        """Lock a page, wait few seconds and unlock the page."""
        page = pywikibot.Page(self.site, 'Foo')
        page.site.lock_page(page=page, block=True)
        wait = random.randint(1, 25) / 10
        time.sleep(wait)
        page.site.unlock_page(page=page)

    def test_threads_locking_page(self):
        """Test lock_page and unlock_page methods for multiple threads."""
        # Start few threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=self.worker)
            thread.setDaemon(True)
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join(15)  # maximum wait time for all threads

            with self.subTest(name=thread.getName()):
                # Check whether a timeout happened.
                # In that case is_alive() is True
                self.assertFalse(thread.is_alive(),
                                 'test page is still locked')

    def test_lock_page(self):
        """Test the site.lock_page() and site.unlock_page() method."""
        site = self.get_site()
        p1 = pywikibot.Page(site, 'Foo')

        site.lock_page(page=p1, block=True)
        self.assertRaises(pywikibot.site.PageInUse, site.lock_page, page=p1,
                          block=False)
        site.unlock_page(page=p1)
        # verify it's unlocked
        site.lock_page(page=p1, block=False)
        site.unlock_page(page=p1)


class TestSiteGeneratorsUsers(DefaultSiteTestCase):
    """Test cases for Site methods with users."""

    cached = True

    def setUp(self):
        """Initialize self.site and self.mainpage."""
        super(TestSiteGeneratorsUsers, self).setUp()
        self.site = self.get_site()
        self.mainpage = self.get_mainpage()

    def test_botusers(self):
        """Test the site.botusers() method."""
        mysite = self.get_site()
        bu = list(mysite.botusers(total=10))
        self.assertLessEqual(len(bu), 10)
        for botuser in bu:
            self.assertIsInstance(botuser, dict)
            self.assertIn('name', botuser)
            self.assertIn('userid', botuser)
            self.assertIn('editcount', botuser)
            self.assertIn('registration', botuser)
            self.assertIn('bot', botuser['groups'])

    def test_allusers(self):
        """Test the site.allusers() method."""
        mysite = self.get_site()
        au = list(mysite.allusers(total=10))
        self.assertLessEqual(len(au), 10)
        for user in au:
            self.assertIsInstance(user, dict)
            self.assertIn('name', user)
            self.assertIn('editcount', user)
            self.assertIn('registration', user)
            self.assertIn('user', user['groups'])

    def test_allusers_with_start(self):
        """Test the site.allusers(start=..) method."""
        mysite = self.get_site()
        for user in mysite.allusers(start='B', total=5):
            self.assertIsInstance(user, dict)
            self.assertIn('name', user)
            self.assertGreaterEqual(user['name'], 'B')
            self.assertIn('editcount', user)
            self.assertIn('registration', user)

    def test_allusers_with_prefix(self):
        """Test the site.allusers(prefix=..) method."""
        mysite = self.get_site()
        for user in mysite.allusers(prefix='C', total=5):
            self.assertIsInstance(user, dict)
            self.assertIn('name', user)
            self.assertTrue(user['name'].startswith('C'))
            self.assertIn('editcount', user)
            self.assertIn('registration', user)

    def _test_allusers_with_group(self):
        """Test the site.allusers(group=..) method."""
        mysite = self.get_site()
        for user in mysite.allusers(prefix='D', group='bot', total=5):
            self.assertIsInstance(user, dict)
            self.assertIn('name', user)
            self.assertTrue(user['name'].startswith('D'))
            self.assertIn('editcount', user)
            self.assertIn('registration', user)
            self.assertIn('groups' in user)
            self.assertIn('sysop' in user['groups'])


class TestLinterPages(DefaultSiteTestCase):

    """Test linter_pages methods."""

    def setUp(self):
        """Skip tests if Linter extension is missing."""
        super(TestLinterPages, self).setUp()
        if not self.site.has_extension('Linter'):
            self.skipTest(
                'The site {0} does not use Linter extension'.format(self.site))

    def test_linter_pages(self):
        """Test the deprecated site.logpages() method."""
        le = list(self.site.linter_pages(
            lint_categories='obsolete-tag|missing-end-tag', total=5))
        self.assertLessEqual(len(le), 5)
        for entry in le:
            self.assertIsInstance(entry, pywikibot.Page)
            self.assertIn(entry._lintinfo['category'],
                          ['obsolete-tag', 'missing-end-tag'])


class TestImageUsage(DefaultSiteTestCase):

    """Test cases for Site.imageusage method."""

    cached = True

    @property
    def imagepage(self):
        """Find an image which is used on the main page.

        If there are no images included in main page it'll skip all tests.

        Note: This is not implemented as setUpClass which would be invoked
        while initialising all tests, to reduce chance of an error preventing
        all tests from running.
        """
        if hasattr(self.__class__, '_image_page'):
            return self.__class__._image_page

        mysite = self.get_site()
        page = pywikibot.Page(mysite, mysite.siteinfo['mainpage'])
        try:
            imagepage = next(iter(page.imagelinks()))  # 1st image of page
        except StopIteration:
            raise unittest.SkipTest(
                'No images on the main page of site {0!r}'.format(mysite))

        pywikibot.output('site_tests.TestImageUsage found {} on {}'
                         .format(imagepage, page))

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
        self.assertIsInstance(mysite.has_right('edit'), bool)
        self.assertFalse(mysite.has_right('nonexistent_right'))
        self.assertIsInstance(mysite.has_group('bots'), bool)
        self.assertFalse(mysite.has_group('nonexistent_group'))
        for grp in ('user', 'autoconfirmed', 'bot', 'sysop', 'nosuchgroup'):
            self.assertIsInstance(mysite.has_group(grp), bool)
        for rgt in ('read', 'edit', 'move', 'delete', 'rollback', 'block',
                    'nosuchright'):
            self.assertIsInstance(mysite.has_right(rgt), bool)

    def test_logevents(self):
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

        for logtype in mysite.logtypes:
            with self.subTest(logtype=logtype):
                gen = iter(mysite.logevents(logtype=logtype, total=3))
                while True:
                    try:
                        entry = next(gen)
                    except StopIteration:
                        break
                    except HiddenKeyError as e:  # T216876
                        self.skipTest(e)
                    else:
                        self.assertEqual(entry.type(), logtype)

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
                start=pywikibot.Timestamp.fromISOformat(
                    '2008-09-01T00:00:01Z'), total=5):
            self.assertIsInstance(entry, pywikibot.logentries.LogEntry)
            self.assertLessEqual(str(entry.timestamp()),
                                 '2008-09-01T00:00:01Z')
        for entry in mysite.logevents(
                end=pywikibot.Timestamp.fromISOformat('2008-09-02T23:59:59Z'),
                total=5):
            self.assertIsInstance(entry, pywikibot.logentries.LogEntry)
            self.assertGreaterEqual(str(entry.timestamp()),
                                    '2008-09-02T23:59:59Z')
        for entry in mysite.logevents(
                start=pywikibot.Timestamp.fromISOformat(
                    '2008-02-02T00:00:01Z'),
                end=pywikibot.Timestamp.fromISOformat('2008-02-02T23:59:59Z'),
                reverse=True, total=5):
            self.assertIsInstance(entry, pywikibot.logentries.LogEntry)
            self.assertTrue(
                '2008-02-02T00:00:01Z' <= str(entry.timestamp())
                <= '2008-02-02T23:59:59Z')
        for entry in mysite.logevents(
                start=pywikibot.Timestamp.fromISOformat(
                    '2008-02-03T23:59:59Z'),
                end=pywikibot.Timestamp.fromISOformat('2008-02-03T00:00:01Z'),
                total=5):
            self.assertIsInstance(entry, pywikibot.logentries.LogEntry)
            self.assertTrue(
                '2008-02-03T00:00:01Z' <= str(entry.timestamp())
                <= '2008-02-03T23:59:59Z')
        # starttime earlier than endtime
        self.assertRaises(AssertionError, mysite.logevents,
                          start=pywikibot.Timestamp.fromISOformat(
                              '2008-02-03T00:00:01Z'),
                          end=pywikibot.Timestamp.fromISOformat(
                              '2008-02-03T23:59:59Z'), total=5)
        # reverse: endtime earlier than starttime
        self.assertRaises(AssertionError, mysite.logevents,
                          start=pywikibot.Timestamp.fromISOformat(
                              '2008-02-03T23:59:59Z'),
                          end=pywikibot.Timestamp.fromISOformat(
                              '2008-02-03T00:00:01Z'),
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
            if not isinstance(entry[0], int):  # autoblock removal entry
                self.assertIsInstance(entry[0], pywikibot.Page)
            self.assertIsInstance(entry[1], basestring)
            self.assertIsInstance(
                entry[2], long if PY2 and entry[2] > sys.maxint else int)
            self.assertIsInstance(entry[3], basestring)

    def test_list_namespace(self):
        """Test the deprecated site.logpages() when namespace is a list."""
        if self.site.mw_version <= '1.19.24':  # T217664
            self.skipTest(
                'logevents does not support namespace parameter with MediaWiki'
                ' {}.'.format(self.site.mw_version))
        le = list(self.site.logpages(namespace=[2, 3], number=10))
        for entry in le:
            if isinstance(entry[0], int):  # autoblock removal entry
                continue
            try:
                self.assertIn(entry[0].namespace(), [2, 3])
            except HiddenKeyError as e:
                self.skipTest(
                    'Log entry {entry} is hidden:\n{entry.data}\n{error!r}'
                    .format(entry=entry, error=e))

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
                start=pywikibot.Timestamp.fromISOformat(
                    '2008-10-01T01:02:03Z'),
                total=5):
            self.assertIsInstance(change, dict)
            self.assertLessEqual(change['timestamp'], '2008-10-01T01:02:03Z')
        for change in mysite.recentchanges(
                end=pywikibot.Timestamp.fromISOformat('2008-04-01T02:03:04Z'),
                total=5):
            self.assertIsInstance(change, dict)
            self.assertGreaterEqual(change['timestamp'],
                                    '2008-10-01T02:03:04Z')
        for change in mysite.recentchanges(
                start=pywikibot.Timestamp.fromISOformat(
                    '2008-10-01T03:05:07Z'),
                total=5, reverse=True):
            self.assertIsInstance(change, dict)
            self.assertGreaterEqual(change['timestamp'],
                                    '2008-10-01T03:05:07Z')
        for change in mysite.recentchanges(
                end=pywikibot.Timestamp.fromISOformat('2008-10-01T04:06:08Z'),
                total=5, reverse=True):
            self.assertIsInstance(change, dict)
            self.assertLessEqual(change['timestamp'], '2008-10-01T04:06:08Z')
        for change in mysite.recentchanges(
                start=pywikibot.Timestamp.fromISOformat(
                    '2008-10-03T11:59:59Z'),
                end=pywikibot.Timestamp.fromISOformat('2008-10-03T00:00:01Z'),
                total=5):
            self.assertIsInstance(change, dict)
            self.assertTrue(
                '2008-10-03T00:00:01Z' <= change['timestamp']
                <= '2008-10-03T11:59:59Z')
        for change in mysite.recentchanges(
                start=pywikibot.Timestamp.fromISOformat(
                    '2008-10-05T06:00:01Z'),
                end=pywikibot.Timestamp.fromISOformat('2008-10-05T23:59:59Z'),
                reverse=True, total=5):
            self.assertIsInstance(change, dict)
            self.assertTrue(
                '2008-10-05T06:00:01Z' <= change['timestamp']
                <= '2008-10-05T23:59:59Z')
        # start earlier than end
        self.assertRaises(AssertionError, mysite.recentchanges,
                          start='2008-02-03T00:00:01Z',
                          end='2008-02-03T23:59:59Z', total=5)
        # reverse: end earlier than start
        self.assertRaises(AssertionError, mysite.recentchanges,
                          start=pywikibot.Timestamp.fromISOformat(
                              '2008-02-03T23:59:59Z'),
                          end=pywikibot.Timestamp.fromISOformat(
                              '2008-02-03T00:00:01Z'),
                          reverse=True, total=5)

    def test_ns_file(self):
        """Test the site.recentchanges() method with File: and File talk:."""
        if self.site.code == 'wikidata':
            self.skipTest(
                'MediaWiki bug frequently occurring on Wikidata. T101502')
        mysite = self.site
        for change in mysite.recentchanges(namespaces=[6, 7], total=5):
            self.assertIsInstance(change, dict)
            self.assertIn('title', change)
            self.assertIn('ns', change)
            title = change['title']
            self.assertIn(':', title)
            prefix = title[:title.index(':')]
            self.assertIn(self.site.namespaces.lookup_name(prefix).id, [6, 7])
            self.assertIn(change['ns'], [6, 7])

    def test_pagelist(self):
        """Test the site.recentchanges() with pagelist deprecated MW 1.14."""
        mysite = self.site
        mainpage = self.get_mainpage()
        imagepage = self.imagepage
        if mysite.mw_version <= '1.14':
            pagelist = [mainpage]
            if imagepage:
                pagelist += [imagepage]
            titlelist = {page.title() for page in pagelist}
            for change in mysite.recentchanges(pagelist=pagelist,
                                               total=5):
                self.assertIsInstance(change, dict)
                self.assertIn('title', change)
                self.assertIn(change['title'], titlelist)

    def test_changetype(self):
        """Test the site.recentchanges() with changetype."""
        mysite = self.site
        for typ in ('edit', 'new', 'log'):
            for change in mysite.recentchanges(changetype=typ, total=5):
                self.assertIsInstance(change, dict)
                self.assertIn('type', change)
                self.assertEqual(change['type'], typ)

    def test_flags(self):
        """Test the site.recentchanges() with boolean flags."""
        mysite = self.site
        for change in mysite.recentchanges(minor=True, total=5):
            self.assertIsInstance(change, dict)
            self.assertIn('minor', change)
        for change in mysite.recentchanges(minor=False, total=5):
            self.assertIsInstance(change, dict)
            self.assertNotIn('minor', change)
        for change in mysite.recentchanges(bot=True, total=5):
            self.assertIsInstance(change, dict)
            self.assertIn('bot', change)
        for change in mysite.recentchanges(bot=False, total=5):
            self.assertIsInstance(change, dict)
            self.assertNotIn('bot', change)
        for change in mysite.recentchanges(anon=True, total=5):
            self.assertIsInstance(change, dict)
        for change in mysite.recentchanges(anon=False, total=5):
            self.assertIsInstance(change, dict)
        for change in mysite.recentchanges(redirect=False, total=5):
            self.assertIsInstance(change, dict)
            self.assertNotIn('redirect', change)

        # Subtest timeouts on Wikidata due to upstream issue, see T245989
        if mysite.sitename != 'wikidata:wikidata':
            for change in mysite.recentchanges(redirect=True, total=5):
                self.assertIsInstance(change, dict)
                self.assertIn('redirect', change)

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
        for change in mysite.recentchanges(patrolled=True, total=5):
            self.assertIsInstance(change, dict)
            if mysite.has_right('patrol'):
                self.assertIn('patrolled', change)
        for change in mysite.recentchanges(patrolled=False, total=5):
            self.assertIsInstance(change, dict)
            if mysite.has_right('patrol'):
                self.assertNotIn('patrolled', change)


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

    def test_search(self):
        """Test the site.search() method."""
        mysite = self.site
        try:
            se = list(mysite.search('wiki', total=100, namespaces=0))
            self.assertLessEqual(len(se), 100)
            self.assertTrue(all(isinstance(hit, pywikibot.Page)
                                for hit in se))
            self.assertTrue(all(hit.namespace() == 0 for hit in se))
            for hit in mysite.search('common', namespaces=4, total=5):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertEqual(hit.namespace(), 4)
            for hit in mysite.search('word', namespaces=[5, 6, 7], total=5):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertIn(hit.namespace(), [5, 6, 7])
            for hit in mysite.search('another', namespaces='8|9|10', total=5):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertIn(hit.namespace(), [8, 9, 10])
            for hit in mysite.search('wiki', namespaces=0, total=10,
                                     get_redirects=True):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertEqual(hit.namespace(), 0)
        except pywikibot.data.api.APIError as e:
            if e.code == 'gsrsearch-error' and 'timed out' in e.info:
                self.skipTest('gsrsearch returned timeout on site{}:\n{!r}'
                              .format(mysite, e))
            if e.code == 'gsrsearch-text-disabled':
                self.skipTest('gsrsearch is diabled on site {}:\n{!r}'
                              .format(mysite, e))

    @suppress_warnings("where='title' is deprecated", DeprecationWarning)
    def test_search_where_title(self):
        """Test site.search() method with 'where' parameter set to title."""
        search_gen = self.site.search(
            'wiki', namespaces=0, total=10, get_redirects=True, where='title')
        expected_params = {
            'prop': ['info', 'imageinfo', 'categoryinfo'],
            'inprop': ['protection'],
            'iiprop': [
                'timestamp', 'user', 'comment', 'url', 'size', 'sha1',
                'metadata'],
            'iilimit': ['max'], 'generator': ['search'], 'action': ['query'],
            'indexpageids': [True], 'continue': [True], 'gsrnamespace': [0]}
        if self.site.has_extension('CirrusSearch'):
            expected_params.update({
                'gsrsearch': ['intitle:wiki'], 'gsrwhat': [None]})
        else:
            expected_params.update({
                'gsrsearch': ['wiki'], 'gsrwhat': ['title']})
        self.assertEqual(search_gen.request._params, expected_params)
        try:
            for hit in search_gen:
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertEqual(hit.namespace(), 0)
        except pywikibot.data.api.APIError as e:
            if e.code in ('search-title-disabled', 'gsrsearch-title-disabled'):
                self.skipTest(
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
        self.assertTrue(
            all('user' in contrib and contrib['user'] == mysite.user()
                for contrib in uc))

    def test_namespaces(self):
        """Test the site.usercontribs() method using namespaces."""
        mysite = self.get_site()
        for contrib in mysite.usercontribs(user=mysite.user(),
                                           namespaces=14, total=5):
            self.assertIsInstance(contrib, dict)
            self.assertIn('title', contrib)
            self.assertTrue(contrib['title'].startswith(mysite.namespace(14)))

        for contrib in mysite.usercontribs(user=mysite.user(),
                                           namespaces=[10, 11], total=5):
            self.assertIsInstance(contrib, dict)
            self.assertIn('title', contrib)
            self.assertIn(contrib['ns'], (10, 11))

    def test_show_minor(self):
        """Test the site.usercontribs() method using showMinor."""
        mysite = self.get_site()
        for contrib in mysite.usercontribs(user=mysite.user(),
                                           minor=True, total=5):
            self.assertIsInstance(contrib, dict)
            self.assertIn('minor', contrib)

        for contrib in mysite.usercontribs(user=mysite.user(),
                                           minor=False, total=5):
            self.assertIsInstance(contrib, dict)
            self.assertNotIn('minor', contrib)


class TestUserContribsWithoutUser(DefaultSiteTestCase):

    """Test site method site.usercontribs() without bot user."""

    def test_user_prefix(self):
        """Test the site.usercontribs() method with userprefix."""
        mysite = self.get_site()
        for contrib in mysite.usercontribs(userprefix='John', total=5):
            self.assertIsInstance(contrib, dict)
            for key in ('user', 'title', 'ns', 'pageid', 'revid'):
                self.assertIn(key, contrib)
            self.assertTrue(contrib['user'].startswith('John'))

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
                end=pywikibot.Timestamp.fromISOformat('2008-10-09T04:06:08Z'),
                total=5, reverse=True):
            self.assertLessEqual(contrib['timestamp'], '2008-10-09T04:06:08Z')

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
        self.assertRaises(AssertionError, mysite.usercontribs,
                          userprefix='Jim',
                          start='2008-10-03T00:00:01Z',
                          end='2008-10-03T23:59:59Z', total=5)
        # reverse: end earlier than start
        self.assertRaises(AssertionError, mysite.usercontribs,
                          userprefix='Jim',
                          start='2008-10-03T23:59:59Z',
                          end='2008-10-03T00:00:01Z', reverse=True, total=5)


class SiteWatchlistRevsTestCase(DefaultSiteTestCase):

    """Test site method watchlist_revs()."""

    user = True

    def test_watchlist_revs(self):
        """Test the site.watchlist_revs() method."""
        mysite = self.get_site()
        wl = list(mysite.watchlist_revs(total=10))
        self.assertLessEqual(len(wl), 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in wl))
        for rev in mysite.watchlist_revs(start='2008-10-11T01:02:03Z',
                                         total=5):
            self.assertIsInstance(rev, dict)
            self.assertLessEqual(rev['timestamp'], '2008-10-11T01:02:03Z')
        for rev in mysite.watchlist_revs(end='2008-04-01T02:03:04Z',
                                         total=5):
            self.assertIsInstance(rev, dict)
            self.assertGreaterEqual(rev['timestamp'], '2008-10-11T02:03:04Z')
        for rev in mysite.watchlist_revs(start='2008-10-11T03:05:07Z',
                                         total=5, reverse=True):
            self.assertIsInstance(rev, dict)
            self.assertGreaterEqual(rev['timestamp'], '2008-10-11T03:05:07Z')
        for rev in mysite.watchlist_revs(end='2008-10-11T04:06:08Z',
                                         total=5, reverse=True):
            self.assertIsInstance(rev, dict)
            self.assertLessEqual(rev['timestamp'], '2008-10-11T04:06:08Z')
        for rev in mysite.watchlist_revs(start='2008-10-13T11:59:59Z',
                                         end='2008-10-13T00:00:01Z',
                                         total=5):
            self.assertIsInstance(rev, dict)
            self.assertTrue(
                '2008-10-13T00:00:01Z' <= rev['timestamp']
                <= '2008-10-13T11:59:59Z')
        for rev in mysite.watchlist_revs(start='2008-10-15T06:00:01Z',
                                         end='2008-10-15T23:59:59Z',
                                         reverse=True, total=5):
            self.assertIsInstance(rev, dict)
            self.assertTrue(
                '2008-10-15T06:00:01Z' <= rev['timestamp']
                <= '2008-10-15T23:59:59Z')
        # start earlier than end
        self.assertRaises(AssertionError, mysite.watchlist_revs,
                          start='2008-09-03T00:00:01Z',
                          end='2008-09-03T23:59:59Z', total=5)
        # reverse: end earlier than start
        self.assertRaises(AssertionError, mysite.watchlist_revs,
                          start='2008-09-03T23:59:59Z',
                          end='2008-09-03T00:00:01Z', reverse=True, total=5)
        for rev in mysite.watchlist_revs(namespaces=[6, 7], total=5):
            self.assertIsInstance(rev, dict)
            self.assertIn('title', rev)
            self.assertIn('ns', rev)
            title = rev['title']
            self.assertIn(':', title)
            prefix = title[:title.index(':')]
            self.assertIn(self.site.namespaces.lookup_name(prefix).id, [6, 7])
            self.assertIn(rev['ns'], [6, 7])
        for rev in mysite.watchlist_revs(minor=True, total=5):
            self.assertIsInstance(rev, dict)
            self.assertIn('minor', rev)
        for rev in mysite.watchlist_revs(minor=False, total=5):
            self.assertIsInstance(rev, dict)
            self.assertNotIn('minor', rev)
        for rev in mysite.watchlist_revs(bot=True, total=5):
            self.assertIsInstance(rev, dict)
            self.assertIn('bot', rev)
        for rev in mysite.watchlist_revs(bot=False, total=5):
            self.assertIsInstance(rev, dict)
            self.assertNotIn('bot', rev)
        for rev in mysite.watchlist_revs(anon=True, total=5):
            self.assertIsInstance(rev, dict)
        for rev in mysite.watchlist_revs(anon=False, total=5):
            self.assertIsInstance(rev, dict)


class SiteSysopTestCase(DefaultSiteTestCase):

    """Test site method using a sysop account."""

    sysop = True

    def test_methods(self):
        """Test sysop related methods."""
        mysite = self.get_site()
        self.assertIsInstance(mysite.is_blocked(True), bool)
        self.assertIsInstance(mysite.has_right('edit', True), bool)
        self.assertFalse(mysite.has_right('nonexistent_right', True))
        self.assertIsInstance(mysite.has_group('bots', True), bool)
        self.assertFalse(mysite.has_group('nonexistent_group', True))

    def test_deletedrevs(self):
        """Test the site.deletedrevs() method."""
        mysite = self.get_site()
        if not mysite.has_right('deletedhistory'):
            self.skipTest(
                "You don't have permission to view the deleted revisions "
                'on {0}.'.format(mysite))
        mainpage = self.get_mainpage()
        gen = mysite.deletedrevs(total=10, titles=mainpage)

        for dr in gen:
            break
        else:
            self.skipTest(
                '{0} contains no deleted revisions.'.format(mainpage))
        self.assertLessEqual(len(dr['revisions']), 10)
        self.assertTrue(all(isinstance(rev, dict) for rev in dr['revisions']))

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
                          reverse=False):
            with self.assertRaises(AssertionError):
                gen = mysite.deletedrevs(titles=mainpage,
                                         start='2008-09-03T00:00:01Z',
                                         end='2008-09-03T23:59:59Z', total=5)
                next(gen)

        # reverse: end earlier than start
        with self.subTest(start='2008-09-03T23:59:59Z',
                          end='2008-09-03T00:00:01Z',
                          reverse=True):
            with self.assertRaises(AssertionError):
                gen = mysite.deletedrevs(titles=mainpage,
                                         start='2008-09-03T23:59:59Z',
                                         end='2008-09-03T00:00:01Z', total=5,
                                         reverse=True)
                next(gen)


class TestSiteSysopWrite(TestCase):

    """Test site sysop methods that require writing."""

    family = 'wikipedia'
    code = 'test'

    write = True
    sysop = True

    def test_protect(self):
        """Test the site.protect() method."""
        site = self.get_site()
        p1 = pywikibot.Page(site, 'User:Unicodesnowman/ProtectTest')

        r = site.protect(protections={'edit': 'sysop',
                                      'move': 'autoconfirmed'},
                         page=p1,
                         reason='Pywikibot unit test')
        self.assertIsNone(r)
        self.assertEqual(site.page_restrictions(page=p1),
                         {'edit': ('sysop', 'infinity'),
                          'move': ('autoconfirmed', 'infinity')})

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

    def test_protect_alt(self):
        """Test the site.protect() method, works around T78522."""
        site = self.get_site()
        p1 = pywikibot.Page(site, 'User:Unicodesnowman/ProtectTest')

        r = site.protect(protections={'edit': 'sysop',
                                      'move': 'autoconfirmed'},
                         page=p1,
                         reason='Pywikibot unit test')
        self.assertIsNone(r)
        self.assertEqual(site.page_restrictions(page=p1),
                         {'edit': ('sysop', 'infinity'),
                          'move': ('autoconfirmed', 'infinity')})

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

    def test_protect_exception(self):
        """Test that site.protect() throws an exception for invalid args."""
        site = self.get_site()
        p1 = pywikibot.Page(site, 'User:Unicodesnowman/ProtectTest')
        self.assertRaises(AssertionError, site.protect,
                          protections={'anInvalidValue': 'sysop'},
                          page=p1, reason='Pywikibot unit test')
        self.assertRaises(AssertionError, site.protect,
                          protections={'edit': 'anInvalidValue'},
                          page=p1, reason='Pywikibot unit test')

    def test_delete(self):
        """Test the site.deletepage() and site.undelete_page() methods."""
        site = self.get_site()
        p = pywikibot.Page(site, 'User:Unicodesnowman/DeleteTestSite')
        # Verify state
        if not p.exists():
            site.undelete_page(p, 'pywikibot unit tests')

        site.deletepage(p, reason='pywikibot unit tests')
        self.assertRaises(pywikibot.NoPage, p.get, force=True)

        site.undelete_page(p, 'pywikibot unit tests',
                           revisions=['2014-12-21T06:07:47Z',
                                      '2014-12-21T06:07:31Z'])

        revs = list(p.revisions())
        self.assertLength(revs, 2)
        self.assertEqual(revs[0].revid, 219995)
        self.assertEqual(revs[1].revid, 219994)

        site.deletepage(p, reason='pywikibot unit tests')
        site.undelete_page(p, 'pywikibot unit tests')
        revs = list(p.revisions())
        self.assertGreater(len(revs), 2)


class TestUsernameInUsers(DefaultSiteTestCase):

    """Test that the user account can be found in users list."""

    user = True
    cached = True

    def test_username_in_users(self):
        """Test the site.users() method with bot username."""
        mysite = self.get_site()
        us = list(mysite.users(mysite.user()))
        self.assertLength(us, 1)
        self.assertIsInstance(us[0], dict)


class TestUserList(DefaultSiteTestCase):

    """Test usernames Jimbo Wales, Brion VIBBER and Tim Starling."""

    cached = True

    def test_users(self):
        """Test the site.users() method with preset usernames."""
        user_list = ['Jimbo Wales', 'Brion VIBBER', 'Tim Starling']
        missing = ['A username that should not exist 1A53F6E375B5']
        all_users = user_list + missing
        for cnt, user in enumerate(self.site.users(all_users), start=1):
            with self.subTest(user=user['name']):
                self.assertIsInstance(user, dict)
                self.assertIn(user['name'], all_users)
                if user['name'] == missing[0]:
                    self.assertIn('missing', user)
                elif self.site.family.name == 'wikipedia':
                    self.assertNotIn('missing', user)
        self.assertEqual(cnt, len(all_users), 'Some test usernames not found')


class PatrolTestCase(TokenTestBase, TestCase):

    """Test patrol method."""

    family = 'wikipedia'
    code = 'test'

    user = True
    token_type = 'patrol'
    write = True

    def test_patrol(self):
        """Test the site.patrol() method."""
        mysite = self.get_site()

        rc = list(mysite.recentchanges(total=1))
        if not rc:
            self.skipTest('no recent changes to patrol')

        rc = rc[0]

        # site.patrol() needs params
        self.assertRaises(pywikibot.Error, lambda x: list(x), mysite.patrol())
        try:
            result = list(mysite.patrol(rcid=rc['rcid']))
        except api.APIError as error:
            if error.code == 'permissiondenied':
                self.skipTest(error)
            raise

        if hasattr(mysite, '_patroldisabled') and mysite._patroldisabled:
            self.skipTest('Patrolling is disabled on {} wiki.'.format(mysite))

        result = result[0]
        self.assertIsInstance(result, dict)

        params = {'rcid': 0}
        if mysite.mw_version >= '1.22':
            params['revid'] = [0, 1]

        try:
            # no such rcid, revid or too old revid
            list(mysite.patrol(**params))
        except api.APIError as error:
            if error.code == 'badtoken':
                self.skipTest(error)
        except pywikibot.Error:
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
        self.assertLength(pages, 11)

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

    def test_all(self):
        """Test site.randompages() with both types."""
        mysite = self.get_site()
        for rndpage in mysite.randompages(total=5, redirects=None):
            self.assertIsInstance(rndpage, pywikibot.Page)

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
        self._version = self.mysite.mw_version
        self.orig_version = self.mysite.version

    def tearDown(self):
        """Restore version."""
        super(TestSiteTokens, self).tearDown()
        self.mysite.version = self.orig_version

    def _test_tokens(self, version, test_version, additional_token):
        """Test tokens."""
        if version and self._version < version:
            raise unittest.SkipTest(
                'Site {} version {} is too low for this tests.'
                .format(self.mysite, self._version))

        if version and self._version < test_version:
            raise unittest.SkipTest(
                'Site {} version {} is too low for this tests.'
                .format(self.mysite, self._version))

        self.mysite.version = lambda: test_version

        for ttype in ('edit', 'move', additional_token):
            tokentype = self.mysite.validate_tokens([ttype])
            try:
                token = self.mysite.tokens[ttype]
            except pywikibot.Error as error_msg:
                if tokentype:
                    self.assertRegex(
                        unicode(error_msg),
                        "Action '[a-z]+' is not allowed "
                        'for user .* on .* wiki.')
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
        self.assertRaises(pywikibot.Error, lambda t: self.mysite.tokens[t],
                          'invalidtype')


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
        ttype = 'edit'
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
            self.assertEqual(self.mysite.getPatrolToken(),
                             self.mysite.tokens['patrol'])
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

    def test_extensions(self):
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

    def test_api_limits_with_site_methods(self):
        """Test step/total parameters for different sitemethods."""
        mysite = self.get_site()
        mypage = pywikibot.Page(mysite, 'Albert Einstein')
        mycat = pywikibot.Page(mysite, 'Category:1879 births')

        gen = mysite.pagecategories(mypage, total=12)
        gen.set_query_increment = 5
        cats = list(gen)
        self.assertLength(cats, 12)

        gen = mysite.categorymembers(mycat, total=12)
        gen.set_query_increment = 5
        cat_members = list(gen)
        self.assertLength(cat_members, 12)

        gen = mysite.pageimages(mypage, total=5)
        gen.set_query_increment = 3
        images = list(gen)
        self.assertLength(images, 5)

        gen = mysite.pagetemplates(mypage, total=5)
        gen.set_query_increment = 3
        templates = list(gen)
        self.assertLength(templates, 5)

        mysite.loadrevisions(mypage, step=5, total=12)
        self.assertLength(mypage._revisions, 12)


class TestSiteInfo(DefaultSiteTestCase):

    """Test cases for Site metadata and capabilities."""

    cached = True

    def test_siteinfo(self):
        """Test the siteinfo property."""
        # general enteries
        mysite = self.get_site()
        self.assertIsInstance(mysite.siteinfo['timeoffset'], (int, float))
        self.assertTrue(-12 * 60 <= mysite.siteinfo['timeoffset'] <= +14 * 60)
        self.assertEqual(mysite.siteinfo['timeoffset'] % 15, 0)
        self.assertRegex(mysite.siteinfo['timezone'],
                         '([A-Z]{3,4}|[A-Z][a-z]+/[A-Z][a-z]+)')
        self.assertIn(mysite.siteinfo['case'], ['first-letter',
                                                'case-sensitive'])

    def test_siteinfo_boolean(self):
        """Test conversion of boolean properties from empty strings."""
        mysite = self.get_site()
        self.assertIsInstance(mysite.siteinfo['titleconversion'], bool)

        self.assertIsInstance(mysite.namespaces[0].subpages, bool)
        self.assertIsInstance(mysite.namespaces[0].content, bool)

    def test_siteinfo_v1_16(self):
        """Test v.16+ siteinfo values."""
        if self.site.mw_version < '1.16':
            self.skipTest('requires v1.16+')

        mysite = self.get_site()
        self.assertIsInstance(
            datetime.strptime(mysite.siteinfo['time'], '%Y-%m-%dT%H:%M:%SZ'),
            datetime)
        self.assertEqual(re.findall(r'\$1', mysite.siteinfo['articlepath']),
                         ['$1'])

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
        self.assertIsEmpty(mysite.siteinfo.get(not_exists))
        self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists)))
        if PY2:
            self.assertFalse(
                entered_loop(mysite.siteinfo.get(not_exists).iteritems()))
            self.assertFalse(
                entered_loop(mysite.siteinfo.get(not_exists).itervalues()))
            self.assertFalse(
                entered_loop(mysite.siteinfo.get(not_exists).iterkeys()))
        self.assertFalse(
            entered_loop(mysite.siteinfo.get(not_exists).items()))
        self.assertFalse(
            entered_loop(mysite.siteinfo.get(not_exists).values()))
        self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).keys()))


class TestSiteinfoDry(DefaultDrySiteTestCase):

    """Test Siteinfo in dry mode."""

    def test_siteinfo_timestamps(self):
        """Test that cache has the timestamp of CachedRequest."""
        site = self.get_site()
        request_mock = MagicMock()
        request_mock.submit = lambda: {'query': {'_prop': '_value'}}
        request_mock._cachetime = '_cache_time'
        with patch.object(site, '_request', return_value=request_mock):
            siteinfo = pywikibot.site.Siteinfo(site)
            result = siteinfo._get_siteinfo('_prop', False)
        self.assertEqual(result, {'_prop': ('_value', '_cache_time')})


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
        self.mainpage = pywikibot.Page(pywikibot.Link('Main Page',
                                                      self.mysite))

    def test_loadrevisions_basic(self):
        """Test the site.loadrevisions() method."""
        # Load revisions without content
        self.mysite.loadrevisions(self.mainpage, total=15)
        self.mysite.loadrevisions(self.mainpage)
        self.assertFalse(hasattr(self.mainpage, '_text'))
        self.assertLength(self.mainpage._revisions, 15)
        self.assertIn(self.mainpage._revid, self.mainpage._revisions)
        self.assertIsNone(self.mainpage._revisions[self.mainpage._revid].text)
        # The revision content will be loaded by .text
        self.assertIsNotNone(self.mainpage.text)

    def test_loadrevisions_content(self):
        """Test the site.loadrevisions() method with content=True."""
        self.mysite.loadrevisions(self.mainpage, content=True, total=5)
        self.assertFalse(hasattr(self.mainpage, '_text'))
        self.assertIn(self.mainpage._revid, self.mainpage._revisions)
        self.assertIsNotNone(
            self.mainpage._revisions[self.mainpage._revid].text)
        self.assertTrue(self.mainpage._revisions[self.mainpage._revid].text)
        self.assertIsNotNone(self.mainpage.text)

    def test_loadrevisions_revids(self):
        """Test the site.loadrevisions() method, listing based on revid."""
        # revids as list of int
        self.mysite.loadrevisions(self.mainpage, revids=[139992, 139993])
        self.assertTrue(all(rev in self.mainpage._revisions
                            for rev in [139992, 139993]))
        # revids as list of str
        self.mysite.loadrevisions(self.mainpage, revids=['139994', '139995'])
        self.assertTrue(all(rev in self.mainpage._revisions
                            for rev in [139994, 139995]))
        # revids as int
        self.mysite.loadrevisions(self.mainpage, revids=140000)
        self.assertIn(140000, self.mainpage._revisions)
        # revids as str
        self.mysite.loadrevisions(self.mainpage, revids='140001')
        self.assertIn(140001, self.mainpage._revisions)
        # revids belonging to a different page raises Exception
        self.assertRaises(pywikibot.Error, self.mysite.loadrevisions,
                          self.mainpage, revids=130000)

    def test_loadrevisions_querycontinue(self):
        """Test the site.loadrevisions() method with query-continue."""
        self.mysite.loadrevisions(self.mainpage, step=5, total=12)
        self.assertLength(self.mainpage._revisions, 12)

    def test_loadrevisions_revdir(self):
        """Test the site.loadrevisions() method with rvdir=True."""
        self.mysite.loadrevisions(self.mainpage, rvdir=True, total=15)
        self.assertLength(self.mainpage._revisions, 15)

    def test_loadrevisions_timestamp(self):
        """Test the site.loadrevisions() method, listing based on timestamp."""
        self.mysite.loadrevisions(self.mainpage, rvdir=True, total=15)
        self.assertLength(self.mainpage._revisions, 15)
        revs = self.mainpage._revisions
        timestamps = [str(revs[rev].timestamp) for rev in revs]
        self.assertTrue(all(ts < '2002-01-31T00:00:00Z' for ts in timestamps))

        # Retrieve oldest revisions; listing based on timestamp.
        # Raises "loadrevisions: starttime > endtime with rvdir=True"
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=True,
                          starttime='2002-02-01T00:00:00Z',
                          endtime='2002-01-01T00:00:00Z')

        # Retrieve newest revisions; listing based on timestamp.
        # Raises "loadrevisions: endtime > starttime with rvdir=False"
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=False,
                          starttime='2002-01-01T00:00:00Z',
                          endtime='2002-02-01T00:00:00Z')

    def test_loadrevisions_rev_id(self):
        """Test the site.loadrevisions() method, listing based on rev_id."""
        self.mysite.loadrevisions(self.mainpage, rvdir=True, total=15)
        self.assertLength(self.mainpage._revisions, 15)
        revs = self.mainpage._revisions
        self.assertTrue(all(139900 <= rev <= 140100 for rev in revs))

        # Retrieve oldest revisions; listing based on revid.
        # Raises "loadrevisions: startid > endid with rvdir=True"
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=True,
                          startid='200000', endid='100000')

        # Retrieve newest revisions; listing based on revid.
        # Raises "loadrevisions: endid > startid with rvdir=False
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=False,
                          startid='100000', endid='200000')

    def test_loadrevisions_user(self):
        """Test the site.loadrevisions() method, filtering by user."""
        # Only list revisions made by this user.
        self.mainpage._revisions = {}
        self.mysite.loadrevisions(self.mainpage, rvdir=True,
                                  user='Magnus Manske')
        revs = self.mainpage._revisions
        self.assertTrue(all(revs[rev].user == 'Magnus Manske' for rev in revs))

    def test_loadrevisions_excludeuser(self):
        """Test the site.loadrevisions() method, excluding user."""
        # Do not list revisions made by this user.
        self.mainpage._revisions = {}
        self.mysite.loadrevisions(self.mainpage, rvdir=True,
                                  excludeuser='Magnus Manske')
        revs = self.mainpage._revisions
        self.assertFalse(any(revs[rev].user == 'Magnus Manske'
                             for rev in revs))

        # TODO test other optional arguments


class TestSiteLoadRevisionsSysop(DefaultSiteTestCase):

    """Test cases for Site.loadrevision() method."""

    sysop = True

    def test_rollback(self):
        """Test the site.loadrevisions() method with rollback."""
        mainpage = self.get_mainpage()
        self.site.loadrevisions(mainpage, total=12, rollback=True)
        self.assertIsNotEmpty(mainpage._revisions)
        self.assertLessEqual(len(mainpage._revisions), 12)
        if self.site.has_right('rollback'):
            self.assertTrue(all(rev.rollbacktoken is not None
                                for rev in mainpage._revisions.values()))


class TestBacklinks(TestCase):

    """Test for backlinks (issue T194233)."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def setUp(self):
        """Setup tests."""
        super(TestBacklinks, self).setUp()
        self.page = pywikibot.Page(self.site, 'File:BoA – Woman.png')
        self.backlinks = list(self.page.backlinks(follow_redirects=False,
                                                  filter_redirects=True,
                                                  total=5))
        self.references = list(self.page.getReferences(follow_redirects=True,
                                                       filter_redirects=True,
                                                       total=5))
        self.nofollow = list(self.page.getReferences(follow_redirects=False,
                                                     filter_redirects=True,
                                                     total=5))

    def test_backlinks_redirects_length(self):
        """Test backlinks redirects length."""
        self.assertLength(self.backlinks, 1)
        self.assertLength(self.references, 1)
        self.assertLength(self.nofollow, 1)

    def test_backlinks_redirects_status(self):
        """Test backlinks redirects statur."""
        for page in self.backlinks:
            self.assertTrue(page.isRedirectPage())
        for page in self.references:
            self.assertTrue(page.isRedirectPage())
        for page in self.nofollow:
            self.assertTrue(page.isRedirectPage())

    def test_backlinks_redirects_pageid(self):
        """Test backlinks redirects pageid."""
        for page in self.backlinks:
            self.assertEqual(page.pageid, 58874049)
        for page in self.references:
            self.assertEqual(page.pageid, 58874049)
        for page in self.nofollow:
            self.assertEqual(page.pageid, 58874049)


class TestCommonsSite(TestCase):

    """Test cases for Site methods on Commons."""

    family = 'commons'
    code = 'commons'

    cached = True

    def test_interwiki_forward(self):
        """Test interwiki forward."""
        self.site = self.get_site()
        self.mainpage = pywikibot.Page(pywikibot.Link('Main Page', self.site))
        # test pagelanglinks on commons,
        # which forwards interwikis to wikipedia
        ll = next(self.site.pagelanglinks(self.mainpage))
        self.assertIsInstance(ll, pywikibot.Link)
        self.assertEqual(ll.site.family.name, 'wikipedia')


class TestFileArchive(DeprecationTestCase):

    """Test filearchive on Commons."""

    family = 'commons'
    code = 'commons'

    cached = True

    def test_filearchive(self):
        """Test filearchive method."""
        gen = self.site.filearchive(total=10)
        self.assertNotIn('fafrom', str(gen.request))
        self.assertNotIn('fato', str(gen.request))
        fa = list(gen)
        self.assertLessEqual(len(fa), 10)
        for item in fa:
            self.assertIsInstance(item, dict)
            self.assertIn('id', item)
            self.assertIn('name', item)
            self.assertIn('ns', item)
            self.assertIn('title', item)
            self.assertIn('timestamp', item)
            self.assertEqual(item['ns'], 6)
            self.assertEqual('File:' + item['name'].replace('_', ' '),
                             item['title'])

    def test_filearchive_limit(self):
        """Test deprecated limit parameter."""
        fa = list(self.site.filearchive(limit=10))
        self.assertOneDeprecation()
        self.assertLessEqual(len(fa), 10)

    def test_filearchive_prefix(self):
        """Test prefix parameter."""
        gen = self.site.filearchive(prefix='py')
        self.assertIn('faprefix=py', str(gen.request))
        for item in gen:
            self.assertTrue(item['name'].startswith('Py'))

    def test_filearchive_prop(self):
        """Test properties."""
        gen = self.site.filearchive(prop=['sha1', 'size', 'user'], total=1)
        self.assertIn('faprop=sha1|size|user', str(gen.request))
        item = next(iter(gen))
        self.assertIn('sha1', item)
        self.assertIn('size', item)
        self.assertIn('user', item)

    def test_filearchive_reverse(self):
        """Test reverse parameter."""
        gen1 = self.site.filearchive(total=1)
        gen2 = self.site.filearchive(reverse=True, total=1)
        self.assertNotIn('fadir=', str(gen1.request))
        self.assertIn('fadir=descending', str(gen2.request))
        fa1 = next(iter(gen1))
        fa2 = next(iter(gen2))
        self.assertLess(fa1['name'], fa2['name'])

    def test_filearchive_start(self):
        """Test start/end parameters."""
        gen = self.site.filearchive(start='py', end='wiki', total=1)
        self.assertIn('fafrom=py', str(gen.request))
        self.assertIn('fato=wiki', str(gen.request))
        item = next(iter(gen))
        self.assertGreaterEqual(item['name'], 'Py')

    def test_filearchive_sha1(self):
        """Test sha1 parameter."""
        sha1 = '0d5a00aa774100408e60da09f5fb21f253b366f1'
        gen = self.site.filearchive(sha1=sha1, prop='sha1', total=1)
        self.assertIn('fasha1=' + sha1, str(gen.request))
        item = next(iter(gen))
        self.assertEqual(item['sha1'], sha1)


class TestWiktionarySite(TestCase):

    """Test Site Object on English Wiktionary."""

    family = 'wiktionary'
    code = 'en'

    cached = True

    def test_namespace_case(self):
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

    def test_namespace_aliases(self):
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
                self.assertLength(page._revisions, 1)
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
                self.assertLength(page._revisions, 1)
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
                self.assertLength(page._revisions, 1)
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
            self.skipTest('insufficient links on main page')

        # get a fresh generator; we now know how many results it will have,
        # if it is less than 10.
        links = mysite.pagelinks(mainpage, total=10)
        for page in mysite.preloadpages(links, groupsize=50):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertLength(page._revisions, 1)
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
            self.skipTest('insufficient links on main page')

        # get a fresh generator; we now know how many results it will have,
        # if it is less than 10.
        links = mysite.pagelinks(mainpage, total=10)
        for page in mysite.preloadpages(links, groupsize=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertLength(page._revisions, 1)
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
            self.skipTest('insufficient links on main page')

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
                self.assertLength(page._revisions, 1)
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
            self.skipTest('insufficient links on main page')

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
                self.assertLength(page._revisions, 1)
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
            self.skipTest('insufficient links on main page')

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

    def test_preload_langlinks_normal(self):
        """Test preloading langlinks works."""
        mysite = self.get_site()
        links = mysite.pagelinks(self.get_mainpage(), total=10)
        gen = mysite.preloadpages(links, groupsize=5, langlinks=True)
        for count, page in enumerate(gen):
            with self.subTest(page=page.title()):
                self.assertIsInstance(page, pywikibot.Page)
                self.assertIsInstance(page.exists(), bool)
                if page.exists():
                    self.assertLength(page._revisions, 1)
                    self.assertIsNotNone(page._revisions[page._revid].text)
                    self.assertFalse(hasattr(page, '_pageprops'))
                    self.assertTrue(hasattr(page, '_langlinks'))
            if count >= 5:
                break

    @patch.object(pywikibot, 'output')
    def test_preload_langlinks_count(self, output_mock):
        """Test preloading continuation works."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        links = list(mysite.pagelinks(mainpage, total=20))
        pages = list(mysite.preloadpages(links, groupsize=5, langlinks=True))
        self.assertLength(links, pages)
        for page in pages:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertLength(page._revisions, 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
        if pages:
            self.assertRegex(
                output_mock.call_args[0][0], r'Retrieving \d pages from ')

    def test_preload_templates(self):
        """Test preloading templates works."""
        mysite = self.get_site()
        # Use backlinks, as any backlink has at least one link
        links = mysite.pagelinks(self.get_mainpage(), total=10)
        gen = mysite.preloadpages(links, templates=True)
        for count, page in enumerate(gen):
            with self.subTest(page=page.title()):
                self.assertIsInstance(page, pywikibot.Page)
                self.assertIsInstance(page.exists(), bool)
                if page.exists():
                    self.assertLength(page._revisions, 1)
                    self.assertIsNotNone(page._revisions[page._revid].text)
                    self.assertFalse(hasattr(page, '_pageprops'))
                    self.assertTrue(hasattr(page, '_templates'))
            if count >= 5:
                break

    def test_preload_templates_and_langlinks(self):
        """Test preloading templates and langlinks works."""
        mysite = self.get_site()
        # Use backlinks, as any backlink has at least one link
        links = mysite.pagebacklinks(self.get_mainpage(), total=10)
        for count, page in enumerate(mysite.preloadpages(links,
                                                         langlinks=True,
                                                         templates=True)):
            with self.subTest(page=page):
                self.assertIsInstance(page, pywikibot.Page)
                self.assertIsInstance(page.exists(), bool)
                if page.exists():
                    self.assertLength(page._revisions, 1)
                    self.assertIsNotNone(page._revisions[page._revid].text)
                    self.assertFalse(hasattr(page, '_pageprops'))
                    self.assertTrue(hasattr(page, '_templates'))
                    self.assertTrue(hasattr(page, '_langlinks'))
            if count >= 5:
                break


class TestDataSitePreloading(WikidataTestCase):

    """Test DataSite.preload_entities for repo pages."""

    def test_item(self):
        """Test that ItemPage preloading works for Item objects."""
        datasite = self.get_repo()
        items = [pywikibot.ItemPage(datasite, 'q' + str(num))
                 for num in range(1, 6)]

        seen = []
        for item in datasite.preload_entities(items):
            self.assertIsInstance(item, pywikibot.ItemPage)
            self.assertTrue(hasattr(item, '_content'))
            self.assertNotIn(item, seen)
            seen.append(item)
        self.assertLength(seen, 5)

    def test_item_as_page(self):
        """Test that ItemPage preloading works for Page objects."""
        site = self.get_site()
        datasite = self.get_repo()
        pages = [pywikibot.Page(site, 'q' + str(num))
                 for num in range(1, 6)]

        seen = []
        for item in datasite.preload_entities(pages):
            self.assertIsInstance(item, pywikibot.ItemPage)
            self.assertTrue(hasattr(item, '_content'))
            self.assertNotIn(item, seen)
            seen.append(item)
        self.assertLength(seen, 5)

    def test_property(self):
        """Test that preloading works for properties."""
        datasite = self.get_repo()
        page = pywikibot.Page(datasite, 'P6')
        property_page = next(datasite.preload_entities([page]))
        self.assertIsInstance(property_page, pywikibot.PropertyPage)
        self.assertTrue(hasattr(property_page, '_content'))


class TestDataSiteClientPreloading(DefaultWikidataClientTestCase):

    """Test DataSite.preload_entities for client pages."""

    def test_non_item(self):
        """Test that ItemPage preloading works with Page generator."""
        mainpage = self.get_mainpage()
        datasite = self.get_repo()

        item = next(datasite.preload_entities([mainpage]))
        self.assertIsInstance(item, pywikibot.ItemPage)
        self.assertTrue(hasattr(item, '_content'))
        self.assertEqual(item.id, 'Q5296')


class TestDataSiteSearchEntities(WikidataTestCase):

    """Test DataSite.search_entities."""

    def test_general(self):
        """Test basic search_entities functionality."""
        datasite = self.get_repo()
        pages = list(datasite.search_entities('abc', 'en', total=50))
        self.assertIsNotEmpty(pages)
        self.assertLessEqual(len(pages), 50)
        pages = list(datasite.search_entities('alphabet', 'en',
                                              type='property', total=50))
        self.assertIsNotEmpty(pages)
        self.assertLessEqual(len(pages), 50)

    def test_continue(self):
        """Test that continue parameter in search_entities works."""
        datasite = self.get_repo()
        kwargs = {'total': 50}
        pages = datasite.search_entities('Rembrandt', 'en', **kwargs)
        kwargs['continue'] = 1
        pages_continue = datasite.search_entities('Rembrandt', 'en', **kwargs)
        self.assertNotEqual(list(pages), list(pages_continue))

    def test_language_lists(self):
        """Test that languages returned by paraminfo and MW are the same."""
        site = self.get_site()
        lang_codes = site._paraminfo.parameter('wbsearchentities',
                                               'language')['type']
        lang_codes2 = [lang['code']
                       for lang in site._siteinfo.get('languages')]
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


class TestObsoleteSite(DefaultSiteTestCase):

    """Test 'closed' and obsolete code sites."""

    def test_locked_site(self):
        """Test Wikimedia closed/locked site."""
        with suppress_warnings('Interwiki removal mh is in wikipedia codes'):
            site = pywikibot.Site('mh', 'wikipedia')
        self.assertIsInstance(site, pywikibot.site.ClosedSite)
        self.assertEqual(site.code, 'mh')
        self.assertIsInstance(site.obsolete, bool)
        self.assertTrue(site.obsolete)
        self.assertEqual(site.hostname(), 'mh.wikipedia.org')
        r = http.fetch(uri='http://mh.wikipedia.org/w/api.php',
                       default_error_handling=False)
        self.assertEqual(r.status, 200)
        self.assertEqual(site.siteinfo['lang'], 'mh')

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
        with suppress_warnings(
                'Site wikipedia:ja instantiated using different code "jp"'):
            site = pywikibot.Site('jp', 'wikipedia')
        self.assertIsInstance(site.obsolete, bool)
        self.assertEqual(site.code, 'ja')
        self.assertFalse(site.obsolete)
        self.assertEqual(site.hostname(), 'ja.wikipedia.org')
        self.assertEqual(site.ssl_hostname(), 'ja.wikipedia.org')


class TestSingleCodeFamilySite(AlteredDefaultSiteTestCase):

    """Test single code family sites."""

    sites = {
        'omegawiki': {
            'family': 'omegawiki',
            'code': 'omegawiki',
        },
    }

    def test_omega(self):
        """Test www.omegawiki.org."""
        url = 'www.omegawiki.org'
        site = self.get_site('omegawiki')
        self.assertEqual(site.hostname(), url)
        self.assertEqual(site.code, 'omegawiki')
        self.assertIsInstance(site.namespaces, Mapping)
        self.assertFalse(site.obsolete)
        self.assertEqual(site.family.hostname('en'), url)
        self.assertEqual(site.family.hostname('omega'), url)
        self.assertEqual(site.family.hostname('omegawiki'), url)


class TestSubdomainFamilySite(TestCase):

    """Test subdomain family site."""

    code = 'en'
    family = 'lyricwiki'

    def test_lyrics(self):
        """Test lyrics.fandom.com."""
        url = 'lyrics.fandom.com'
        site = self.site
        self.assertEqual(site.hostname(), url)
        self.assertEqual(site.code, 'en')
        self.assertIsInstance(site.namespaces, Mapping)
        self.assertFalse(site.obsolete)
        self.assertEqual(site.family.hostname('en'), url)

        self.assertRaises(KeyError, site.family.hostname, 'lyrics')
        self.assertRaises(KeyError, site.family.hostname, 'lyricwiki')
        self.assertRaises(pywikibot.UnknownSite, pywikibot.Site,
                          'lyricwiki', 'lyricwiki')
        self.assertRaises(pywikibot.UnknownSite, pywikibot.Site,
                          'de', 'lyricwiki')


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

    def test_commons(self):
        """Test Wikimedia Commons."""
        site = self.get_site('commons')
        self.assertEqual(site.hostname(), 'commons.wikimedia.org')
        self.assertEqual(site.code, 'commons')
        self.assertIsInstance(site.namespaces, Mapping)
        self.assertFalse(site.obsolete)

        self.assertRaises(KeyError, site.family.hostname, 'en')

        pywikibot.config.family = 'commons'
        pywikibot.config.mylang = 'de'

        site2 = pywikibot.Site('beta')
        self.assertEqual(site2.hostname(),
                         'commons.wikimedia.beta.wmflabs.org')
        self.assertEqual(site2.code, 'beta')
        self.assertFalse(site2.obsolete)

        self.assertRaises(pywikibot.UnknownSite,
                          pywikibot.Site)

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

        # Languages can't be used due to T71255
        self.assertRaises(pywikibot.UnknownSite,
                          pywikibot.Site, 'en', 'wikidata')


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

    def test_cache_proofreadinfo_on_site_with_proofreadpage(self):
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

    def test_cache_proofreadinfo_on_site_without_proofreadpage(self):
        """Test Site._cache_proofreadinfo()."""
        site = self.get_site('en-wp')
        self.assertRaises(pywikibot.UnknownExtension,
                          site._cache_proofreadinfo)
        self.assertRaises(pywikibot.UnknownExtension,
                          lambda x: x.proofread_index_ns, site)
        self.assertRaises(pywikibot.UnknownExtension,
                          lambda x: x.proofread_page_ns, site)
        self.assertRaises(pywikibot.UnknownExtension,
                          lambda x: x.proofread_levels, site)


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


class TestLoginLogout(DefaultSiteTestCase):

    """Test for login and logout methods."""

    user = True

    def test_login_logout(self):
        """Validate login and logout methods by toggling the state."""
        site = self.get_site()
        loginstatus = pywikibot.site.LoginStatus

        self.assertTrue(site.logged_in())
        self.assertIn(site._loginstatus, (loginstatus.IN_PROGRESS,
                                          loginstatus.AS_USER))
        self.assertIn('_userinfo', site.__dict__.keys())

        self.assertIsNone(site.login())

        if site.is_oauth_token_available():
            self.assertRaisesRegexp(api.APIError, 'cannotlogout.*OAuth',
                                    site.logout)
            self.assertTrue(site.logged_in())
            self.assertIn(site._loginstatus, (loginstatus.IN_PROGRESS,
                                              loginstatus.AS_USER))
            self.assertIn('_userinfo', site.__dict__.keys())

        # Fandom family wikis don't support API action=logout
        elif 'fandom.com' not in site.hostname():
            site.logout()
            self.assertFalse(site.logged_in())
            self.assertEqual(site._loginstatus, loginstatus.NOT_LOGGED_IN)
            self.assertNotIn('_userinfo', site.__dict__.keys())

            self.assertIsNone(site.user())


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
