"""Tests for the site module."""
#
# (C) Pywikibot team, 2008-2021
#
# Distributed under the terms of the MIT license.
#
import pickle
import random
import threading
import time
import unittest
from collections.abc import Iterable, Mapping
from contextlib import suppress
from http import HTTPStatus

import pywikibot
from pywikibot import config
from pywikibot.comms import http
from pywikibot.data import api
from pywikibot.exceptions import (
    APIError,
    Error,
    HiddenKeyError,
    IsNotRedirectPageError,
    NoPageError,
    PageInUseError,
    UnknownExtensionError,
    UnknownSiteError,
)
from pywikibot.tools import suppress_warnings
from tests import WARN_SITE_CODE, patch, unittest_print
from tests.aspects import (
    AlteredDefaultSiteTestCase,
    DefaultDrySiteTestCase,
    DefaultSiteTestCase,
    DeprecationTestCase,
    TestCase,
    WikimediaDefaultSiteTestCase,
)
from tests.basepage import BasePageLoadRevisionsCachingTestBase
from tests.utils import skipping


class TestSiteObjectDeprecatedFunctions(DefaultSiteTestCase,
                                        DeprecationTestCase):

    """Test cases for Site deprecated methods on a live wiki."""

    cached = True

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

    def test_namespace_shortcuts(self):
        """Test namespace shortcuts."""
        self.assertEqual(self.site.image_namespace(), self.site.namespace(6))
        self.assertEqual(self.site.mediawiki_namespace(),
                         self.site.namespace(8))
        self.assertEqual(self.site.template_namespace(),
                         self.site.namespace(10))
        self.assertEqual(self.site.category_namespace(),
                         self.site.namespace(14))


class TestSiteDryDeprecatedFunctions(DefaultDrySiteTestCase,
                                     DeprecationTestCase):

    """Test cases for Site deprecated methods without a user."""

    def test_namespaces_callable(self):
        """Test that namespaces is callable and returns itself."""
        site = self.get_site()
        self.assertIs(site.namespaces(), site.namespaces)
        self.assertOneDeprecationParts(
            'Referencing this attribute like a function',
            'it directly')


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
        expect = 'Site("{}", "{}")'.format(code, self.family)
        self.assertTrue(repr(self.site).endswith(expect))

    def test_constructors(self):
        """Test cases for site constructors."""
        test_list = [
            ['enwiki', 'wikipedia:en'],
            ['eswikisource', 'wikisource:es'],
            ['dewikinews', 'wikinews:de'],
            ['ukwikivoyage', 'wikivoyage:uk'],
            ['metawiki', 'meta:meta'],
            ['commonswiki', 'commons:commons'],
            ['wikidatawiki', 'wikidata:wikidata'],
            ['testwikidatawiki', 'wikidata:test'],
            ['testwiki', 'wikipedia:test'],  # see T225729, T228300
            ['test2wiki', 'wikipedia:test2'],  # see T225729
            ['sourceswiki', 'wikisource:mul'],  # see T226960
        ]
        if isinstance(self.site.family, pywikibot.family.WikimediaFamily):
            site = self.site
        else:
            site = None
        for dbname, sitename in test_list:
            with self.subTest(dbname=dbname):
                self.assertIs(
                    pywikibot.site.APISite.fromDBName(dbname, site),
                    pywikibot.Site(sitename))

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

    def test_user_attributes_return_types(self):
        """Test returned types of user attributes."""
        mysite = self.get_site()
        self.assertIsInstance(mysite.logged_in(), bool)
        self.assertIsInstance(mysite.userinfo, dict)

    def test_messages(self):
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
            if lang1 != lang2 and lang1 != familyname and lang2 != familyname:
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
        with self.subTest(messages='about'):
            with self.assertRaises(KeyError):
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
        with suppress_warnings('pywikibot.site._apisite.APISite.page_exists',
                               DeprecationWarning):
            self.assertIsInstance(mysite.page_exists(mainpage), bool)
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


class TestSiteGenerators(DefaultSiteTestCase):
    """Test cases for Site methods."""

    cached = True

    def setUp(self):
        """Initialize self.site and self.mainpage."""
        super().setUp()
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
        if not cats:
            self.skipTest('Main page is not in any categories.')

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
            'continue': [True],
            'inprop': ['protection'],
            'iilimit': ['max'],
            'iiprop': ['timestamp', 'user', 'comment', 'url', 'size', 'sha1',
                       'metadata'],
            'indexpageids': [True],
            'generator': ['templates'], 'action': ['query'],
            'prop': ['info', 'imageinfo', 'categoryinfo'],
            'titles': [self.mainpage.title()],
        }

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
            self.assertIsInstance(el, str)

    def test_pagelinks(self):
        """Test Site.pagelinks."""
        links_gen = self.site.pagelinks(self.mainpage)
        gen_params = links_gen.request._params.copy()
        expected_params = {
            'action': ['query'], 'indexpageids': [True],
            'continue': [True],
            'inprop': ['protection'],
            'iilimit': ['max'],
            'iiprop': ['timestamp', 'user', 'comment', 'url', 'size',
                       'sha1', 'metadata'], 'generator': ['links'],
            'prop': ['info', 'imageinfo', 'categoryinfo'],
            'redirects': [False],
        }
        if 'pageids' in gen_params:
            expected_params['pageids'] = [str(self.mainpage.pageid)]
        else:
            expected_params['titles'] = [self.mainpage.title()]

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
        with self.assertRaises(Error):
            next(errgen)

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
        self.assertTrue(all(isinstance(tup[2], str) for tup in the_list))
        self.assertTrue(all(isinstance(tup[3], str) for tup in the_list))

    def test_querypage(self):
        """Test the site.querypage() method."""
        mysite = self.get_site()
        pages = list(mysite.querypage('Longpages', total=10))

        self.assertTrue(all(isinstance(p, pywikibot.Page) for p in pages))
        with self.assertRaises(AssertionError):
            mysite.querypage('LongpageX')

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
        except APIError as error:
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
            with self.assertRaises(AssertionError):
                mysite.blocks(total=5,
                              starttime=low,
                              endtime=high)

        # reverse: endtime earlier than starttime
        with self.subTest(starttime=high, endtime=low, reverse=True):
            with self.assertRaises(AssertionError):
                mysite.blocks(total=5,
                              starttime=high,
                              endtime=low,
                              reverse=True)

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
                'The site "{}" has no protected pages in main namespace.'
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
                        'NotImplementedError not raised for {}'.format(item))

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
        with self.assertRaises(AssertionError):
            func('m', 2, 1, False, False)

        # reverse=False, is_ts=True
        self.assertIsNone(func('m', 2, 1, False, True))
        with self.assertRaises(AssertionError):
            func('m', 1, 2, False, True)

        # reverse=True, is_ts=False
        self.assertIsNone(func('m', 2, 1, True, False))
        with self.assertRaises(AssertionError):
            func('m', 1, 2, True, False)

        # reverse=True, is_ts=True
        self.assertIsNone(func('m', 1, 2, True, True))
        with self.assertRaises(AssertionError):
            func('m', 2, 1, True, True)


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
        for _ in range(5):
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
        with self.assertRaises(PageInUseError):
            site.lock_page(page=p1, block=False)
        site.unlock_page(page=p1)
        # verify it's unlocked
        site.lock_page(page=p1, block=False)
        site.unlock_page(page=p1)


class TestSiteGeneratorsUsers(DefaultSiteTestCase):
    """Test cases for Site methods with users."""

    cached = True

    def setUp(self):
        """Initialize self.site and self.mainpage."""
        super().setUp()
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
            self.assertIn('groups', user)
            self.assertIn('sysop', user['groups'])


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
        with skipping(
            StopIteration,
                msg='No images on the main page of site {0!r}'.format(mysite)):
            imagepage = next(iter(page.imagelinks()))  # 1st image of page

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
                    '{} is a redirect, although just non-redirects were '
                    'searched. See also T75120'.format(using))
            self.assertFalse(using.isRedirectPage())


class SiteUserTestCase(DefaultSiteTestCase):

    """Test site method using a user."""

    login = True

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
        with self.assertRaises(AssertionError):
            mysite.logevents(start=pywikibot.Timestamp.fromISOformat(
                             '2008-02-03T00:00:01Z'),
                             end=pywikibot.Timestamp.fromISOformat(
                             '2008-02-03T23:59:59Z'), total=5)
        # reverse: endtime earlier than starttime
        with self.assertRaises(AssertionError):
            mysite.logevents(start=pywikibot.Timestamp.fromISOformat(
                             '2008-02-03T23:59:59Z'),
                             end=pywikibot.Timestamp.fromISOformat(
                             '2008-02-03T00:00:01Z'),
                             reverse=True, total=5)


class TestRecentChanges(DefaultSiteTestCase):

    """Test recentchanges method."""

    @classmethod
    def setUpClass(cls):
        """Test up test class."""
        super().setUpClass()
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
        with self.assertRaises(AssertionError):
            mysite.recentchanges(start='2008-02-03T00:00:01Z',
                                 end='2008-02-03T23:59:59Z', total=5)
        # reverse: end earlier than start
        with self.assertRaises(AssertionError):
            mysite.recentchanges(start=pywikibot.Timestamp.fromISOformat(
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

    login = True

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

    login = True

    def test_watched_pages(self):
        """Test the site.watched_pages() method."""
        if not self.site.has_right('viewmywatchlist'):
            self.skipTest('user {} cannot view its watch list'
                          .format(self.site.user()))

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
        if not self.site.has_right('viewmywatchlist'):
            self.skipTest('user {} cannot view its watch list'
                          .format(self.site.user()))

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
            for hit in mysite.search('wiki', namespaces=0, total=10):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertEqual(hit.namespace(), 0)
        except APIError as e:
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
            'wiki', namespaces=0, total=10, where='title')
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
        except APIError as e:
            if e.code in ('search-title-disabled', 'gsrsearch-title-disabled'):
                self.skipTest(
                    'Title search disabled on site: {}'.format(self.site))
            raise


class TestUserContribsAsUser(DefaultSiteTestCase):

    """Test site method site.usercontribs() with bot user."""

    login = True

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
        with self.assertRaises(AssertionError):
            mysite.usercontribs(userprefix='Jim',
                                start='2008-10-03T00:00:01Z',
                                end='2008-10-03T23:59:59Z', total=5)
        # reverse: end earlier than start
        with self.assertRaises(AssertionError):
            mysite.usercontribs(userprefix='Jim',
                                start='2008-10-03T23:59:59Z',
                                end='2008-10-03T00:00:01Z',
                                reverse=True, total=5)


class TestAlldeletedrevisionsAsUser(DefaultSiteTestCase):

    """Test site method site.alldeletedrevisions() with bot user."""

    login = True

    @classmethod
    def setUpClass(cls):
        """Skip test if necessary."""
        super().setUpClass()
        if cls.site.mw_version < '1.34':
            cls.skipTest(cls, 'site.alldeletedrevisions() needs mw 1.34')

    def test_basic(self):
        """Test the site.alldeletedrevisions() method."""
        mysite = self.get_site()
        drev = list(mysite.alldeletedrevisions(user=mysite.user(), total=10))
        self.assertTrue(all(isinstance(data, dict)
                            for data in drev))
        self.assertTrue(all('revisions' in data
                            and isinstance(data['revisions'], dict)
                            for data in drev))
        self.assertTrue(all('user' in rev
                            and rev['user'] == mysite.user()
                            for data in drev
                            for rev in data))

    def test_namespaces(self):
        """Test the site.alldeletedrevisions() method using namespaces."""
        mysite = self.get_site()
        for data in mysite.alldeletedrevisions(namespaces=14, total=5):
            self.assertIsInstance(data, dict)
            self.assertIn('title', data)
            self.assertTrue(data['title'].startswith(mysite.namespace(14)))

        for data in mysite.alldeletedrevisions(user=mysite.user(),
                                               namespaces=[10, 11],
                                               total=5):
            self.assertIsInstance(data, dict)
            self.assertIn('title', data)
            self.assertIn(data['ns'], (10, 11))

    def test_excludeuser(self):
        """Test the site.alldeletedrevisions() method using excludeuser."""
        mysite = self.get_site()
        for data in mysite.alldeletedrevisions(excludeuser=mysite.user(),
                                               total=5):
            self.assertIsInstance(data, dict)
            self.assertIn('revisions', data)
            self.assertIsInstance(data['revisions'], list)
            for drev in data['revisions']:
                self.assertIsInstance(drev, dict)
                self.assertIn('user', drev)
                self.assertNotEqual(drev['user'], mysite.user())

    def test_user_range(self):
        """Test the site.alldeletedrevisions() method with range."""
        mysite = self.get_site()
        start = '2008-10-06T01:02:03Z'
        for data in mysite.alldeletedrevisions(
                user=mysite.user(),
                start=pywikibot.Timestamp.fromISOformat(start),
                total=5):
            self.assertIsInstance(data, dict)
            self.assertIn('revisions', data)
            self.assertIsInstance(data['revisions'], list)
            for drev in data['revisions']:
                self.assertIsInstance(drev, dict)
                self.assertIn('timestamp', drev)
                self.assertLessEqual(drev['timestamp'], start)

        end = '2008-10-07T02:03:04Z'
        for data in mysite.alldeletedrevisions(
                user=mysite.user(),
                end=pywikibot.Timestamp.fromISOformat(end),
                total=5):
            self.assertIsInstance(data, dict)
            self.assertIn('revisions', data)
            self.assertIsInstance(data['revisions'], list)
            for drev in data['revisions']:
                self.assertIsInstance(drev, dict)
                self.assertIn('timestamp', drev)
                self.assertGreaterEqual(drev['timestamp'], end)

        start = '2008-10-10T11:59:59Z'
        end = '2008-10-10T00:00:01Z'
        for data in mysite.alldeletedrevisions(
                user=mysite.user(),
                start=pywikibot.Timestamp.fromISOformat(start),
                end=pywikibot.Timestamp.fromISOformat(end),
                total=5):
            self.assertIsInstance(data, dict)
            self.assertIn('revisions', data)
            self.assertIsInstance(data['revisions'], list)
            for drev in data['revisions']:
                self.assertIsInstance(drev, dict)
                self.assertIn('timestamp', drev)
                self.assertTrue(end <= drev['timestamp'] <= start)

    def test_user_range_reverse(self):
        """Test the site.alldeletedrevisions() method with range reversed."""
        mysite = self.get_site()
        start = '2008-10-08T03:05:07Z'
        for data in mysite.alldeletedrevisions(
                user=mysite.user(),
                start=pywikibot.Timestamp.fromISOformat(start),
                total=5, reverse=True):
            self.assertIsInstance(data, dict)
            self.assertIn('revisions', data)
            self.assertIsInstance(data['revisions'], list)
            for drev in data['revisions']:
                self.assertIsInstance(drev, dict)
                self.assertIn('timestamp', drev)
                self.assertGreaterEqual(drev['timestamp'], start)

        for data in mysite.alldeletedrevisions(
                user=mysite.user(),
                end=pywikibot.Timestamp.fromISOformat('2008-10-09T04:06:08Z'),
                total=5, reverse=True):
            self.assertIsInstance(data, dict)
            self.assertIn('revisions', data)
            self.assertIsInstance(data['revisions'], list)
            for drev in data['revisions']:
                self.assertIsInstance(drev, dict)
                self.assertIn('timestamp', drev)
                self.assertLessEqual(drev['timestamp'],
                                     '2008-10-09T04:06:08Z')

        start = '2008-10-11T06:00:01Z'
        end = '2008-10-11T23:59:59Z'
        for data in mysite.alldeletedrevisions(
                user=mysite.user(),
                start=pywikibot.Timestamp.fromISOformat(start),
                end=pywikibot.Timestamp.fromISOformat(end),
                reverse=True, total=5):
            self.assertIsInstance(data, dict)
            self.assertIn('revisions', data)
            self.assertIsInstance(data['revisions'], list)
            for drev in data['revisions']:
                self.assertIsInstance(drev, dict)
                self.assertIn('timestamp', drev)
                self.assertTrue(start <= drev['timestamp'] <= end)

    def test_invalid_range(self):
        """Test site.alldeletedrevisions() method with invalid range."""
        mysite = self.get_site()
        # start earlier than end
        with self.assertRaises(AssertionError):
            adrgen = mysite.alldeletedrevisions(user=mysite.user(),
                                                start='2008-10-03T00:00:01Z',
                                                end='2008-10-03T23:59:59Z',
                                                total=5)
            next(adrgen)
        # reverse: end earlier than start
        with self.assertRaises(AssertionError):
            adrgen = mysite.alldeletedrevisions(user=mysite.user(),
                                                start='2008-10-03T23:59:59Z',
                                                end='2008-10-03T00:00:01Z',
                                                reverse=True, total=5)
            next(adrgen)


class TestAlldeletedrevisionsWithoutUser(DefaultSiteTestCase):

    """Test site method site.alldeletedrevisions() without bot user."""

    def test_prefix(self):
        """Test the site.alldeletedrevisions() method with prefix."""
        mysite = self.get_site()
        if mysite.mw_version < '1.34':
            self.skipTest('site.alldeletedrevisions() needs mw 1.34')

        for data in mysite.alldeletedrevisions(prefix='John', total=5):
            self.assertIsInstance(data, dict)
            for key in ('title', 'ns', 'revisions'):
                self.assertIn(key, data)
            title = data['title']
            if data['ns'] > 0:
                *_, title = title.partition(':')
            self.assertTrue(title.startswith('John'))
            self.assertIsInstance(data['revisions'], list)
            for drev in data['revisions']:
                self.assertIsInstance(drev, dict)
                for key in ('revid', 'timestamp', 'user'):
                    self.assertIn(key, drev)


class SiteWatchlistRevsTestCase(DefaultSiteTestCase):

    """Test site method watchlist_revs()."""

    login = True

    def test_watchlist_revs(self):
        """Test the site.watchlist_revs() method."""
        if not self.site.has_right('viewmywatchlist'):
            self.skipTest('user {} cannot view its watch list'
                          .format(self.site.user()))

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
        with self.assertRaises(AssertionError):
            mysite.watchlist_revs(start='2008-09-03T00:00:01Z',
                                  end='2008-09-03T23:59:59Z', total=5)
        # reverse: end earlier than start
        with self.assertRaises(AssertionError):
            mysite.watchlist_revs(start='2008-09-03T23:59:59Z',
                                  end='2008-09-03T00:00:01Z',
                                  reverse=True, total=5)
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
        self.assertIsInstance(mysite.is_blocked(), bool)
        self.assertIsInstance(mysite.has_right('edit'), bool)
        self.assertFalse(mysite.has_right('nonexistent_right'))
        self.assertIsInstance(mysite.has_group('bots'), bool)
        self.assertFalse(mysite.has_group('nonexistent_group'))

    def test_deletedrevs(self):
        """Test the site.deletedrevs() method."""
        mysite = self.get_site()
        if not mysite.has_right('deletedhistory'):
            self.skipTest(
                "You don't have permission to view the deleted revisions "
                'on {}.'.format(mysite))
        mainpage = self.get_mainpage()
        gen = mysite.deletedrevs(total=10, titles=mainpage)

        for dr in gen:
            break
        else:
            self.skipTest(
                '{} contains no deleted revisions.'.format(mainpage))
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

    def test_alldeletedrevisions(self):
        """Test the site.alldeletedrevisions() method."""
        mysite = self.get_site()
        myuser = mysite.user()
        if not mysite.has_right('deletedhistory'):
            self.skipTest(
                "You don't have permission to view the deleted revisions "
                'on {}.'.format(mysite))
        prop = ['ids', 'timestamp', 'flags', 'user', 'comment']
        gen = mysite.alldeletedrevisions(total=10, prop=prop)

        for data in gen:
            break
        else:
            self.skipTest('{} does not have deleted edits.'.format(myuser))
        self.assertIn('revisions', data)
        for drev in data['revisions']:
            for key in ('revid', 'timestamp', 'user', 'comment'):
                self.assertIn(key, drev)

        with self.subTest(start='2008-10-11T01:02:03Z', reverse=False,
                          prop=prop):
            for item in mysite.alldeletedrevisions(
                start='2008-10-11T01:02:03Z',
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
                total=5
            ):
                for drev in item['revisions']:
                    self.assertIsInstance(drev, dict)
                    self.assertGreaterEqual(drev['timestamp'],
                                            '2008-10-11T01:02:03Z')

        # start earlier than end
        with self.subTest(start='2008-09-03T00:00:01Z',
                          end='2008-09-03T23:59:59Z',
                          reverse=False, prop=prop):
            with self.assertRaises(AssertionError):
                gen = mysite.alldeletedrevisions(start='2008-09-03T00:00:01Z',
                                                 end='2008-09-03T23:59:59Z',
                                                 total=5)
                next(gen)

        # reverse: end earlier than start
        with self.subTest(start='2008-09-03T23:59:59Z',
                          end='2008-09-03T00:00:01Z',
                          reverse=True, prop=prop):
            with self.assertRaises(AssertionError):
                gen = mysite.alldeletedrevisions(start='2008-09-03T23:59:59Z',
                                                 end='2008-09-03T00:00:01Z',
                                                 total=5, reverse=True)
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
        with self.assertRaises(AssertionError):
            site.protect(protections={'anInvalidValue': 'sysop'},
                         page=p1, reason='Pywikibot unit test')
        with self.assertRaises(AssertionError):
            site.protect(protections={'edit': 'anInvalidValue'},
                         page=p1, reason='Pywikibot unit test')

    def test_delete(self):
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

    def test_revdel_page(self):
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

    def test_revdel_file(self):
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

        fp1 = pywikibot.FilePage(site, 'File:T276726.png')
        site.loadimageinfo(fp1, history=True)
        for idx, v in fp1._file_revisions.items():
            if v['timestamp'] == pywikibot.Timestamp(2021, 3, 14, 18, 43, 57):
                self.assertTrue(hasattr(v, 'userhidden'))

        # Multiple revisions
        site.deleterevs('oldimage', '20210314184415|20210314184430',
                        hide='comment', reason='pywikibot unit tests',
                        target='File:T276726.png')

        fp2 = pywikibot.FilePage(site, 'File:T276726.png')
        site.loadimageinfo(fp2, history=True)
        for idx, v in fp2._file_revisions.items():
            if v['timestamp'] == pywikibot.Timestamp(2021, 3, 14, 18, 43, 57):
                self.assertTrue(hasattr(v, 'commenthidden'))
            if v['timestamp'] == pywikibot.Timestamp(2021, 3, 14, 18, 44, 17):
                self.assertTrue(hasattr(v, 'commenthidden'))

        # Concurrently show and hide
        site.deleterevs('oldimage', ['20210314184415', '20210314184430'],
                        hide='user|content', show='comment',
                        reason='pywikibot unit tests',
                        target='File:T276726.png')

        fp3 = pywikibot.FilePage(site, 'File:T276726.png')
        site.loadimageinfo(fp3, history=True)
        for idx, v in fp3._file_revisions.items():
            if v['timestamp'] == pywikibot.Timestamp(2021, 3, 14, 18, 43, 57):
                self.assertFalse(hasattr(v, 'commenthidden'))
                self.assertFalse(hasattr(v, 'userhidden'))
                self.assertFalse(hasattr(v, 'filehidden'))
            if v['timestamp'] == pywikibot.Timestamp(2021, 3, 14, 18, 44, 17):
                self.assertFalse(hasattr(v, 'commenthidden'))
                self.assertFalse(hasattr(v, 'userhidden'))
                self.assertFalse(hasattr(v, 'filehidden'))

        # Cleanup
        site.deleterevs('oldimage', [20210314184415, 20210314184430],
                        show='content|comment|user',
                        reason='pywikibot unit tests',
                        target='File:T276726.png')

    def test_delete_oldimage(self):
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

        site.undelet(fp, 'pywikibot unit tests', fileids=[fileid])


class TestUsernameInUsers(DefaultSiteTestCase):

    """Test that the user account can be found in users list."""

    login = True
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


class TestSiteLoadRevisionsCaching(BasePageLoadRevisionsCachingTestBase,
                                   DefaultSiteTestCase):

    """Test site.loadrevisions() caching."""

    def setUp(self):
        """Setup tests."""
        self._page = self.get_mainpage(force=True)
        super().setUp()

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
        super().setUp()
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
        with self.assertRaises(Error):
            self.mysite.loadrevisions(self.mainpage,
                                      revids=130000)

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
        with self.assertRaises(ValueError):
            self.mysite.loadrevisions(self.mainpage, rvdir=True,
                                      starttime='2002-02-01T00:00:00Z',
                                      endtime='2002-01-01T00:00:00Z')

        # Retrieve newest revisions; listing based on timestamp.
        # Raises "loadrevisions: endtime > starttime with rvdir=False"
        with self.assertRaises(ValueError):
            self.mysite.loadrevisions(self.mainpage, rvdir=False,
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
        with self.assertRaises(ValueError):
            self.mysite.loadrevisions(self.mainpage, rvdir=True,
                                      startid='200000', endid='100000')

        # Retrieve newest revisions; listing based on revid.
        # Raises "loadrevisions: endid > startid with rvdir=False
        with self.assertRaises(ValueError):
            self.mysite.loadrevisions(self.mainpage, rvdir=False,
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


class TestBacklinks(TestCase):

    """Test for backlinks (issue T194233)."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def setUp(self):
        """Setup tests."""
        super().setUp()
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

    login = True

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
        super().setUp()
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

        with suppress_warnings(WARN_SITE_CODE, category=UserWarning):
            gen = mysite.preloadpages(links, groupsize=5, langlinks=True)
            pages = list(gen)

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
        r = http.fetch('http://mh.wikipedia.org/w/api.php',
                       default_error_handling=False)
        self.assertEqual(r.status_code, HTTPStatus.OK.value)
        self.assertEqual(site.siteinfo['lang'], 'mh')

    def test_removed_site(self):
        """Test Wikimedia offline site."""
        site = pywikibot.Site('ru-sib', 'wikipedia')
        self.assertIsInstance(site, pywikibot.site.RemovedSite)
        self.assertEqual(site.code, 'ru-sib')
        self.assertIsInstance(site.obsolete, bool)
        self.assertTrue(site.obsolete)
        with self.assertRaises(KeyError):
            site.hostname()
        # See also http_tests, which tests that ru-sib.wikipedia.org is offline

    def test_alias_code_site(self):
        """Test Wikimedia site with an alias code."""
        with suppress_warnings(WARN_SITE_CODE, category=UserWarning):
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
    family = 'wowwiki'

    def test_wow(self):
        """Test wowwiki.fandom.com."""
        url = 'wowwiki.fandom.com'
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
            pywikibot.Site('wowwiki', 'wowwiki')
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

    def test_commons(self):
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
                         'commons.wikimedia.beta.wmflabs.org')
        self.assertEqual(site2.code, 'beta')
        self.assertFalse(site2.obsolete)

        with self.assertRaises(UnknownSiteError):
            pywikibot.Site()

    def test_wikidata(self):
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

    def test_get_property_names(self, key):
        """Test get_property_names method."""
        mysite = self.get_site(key)
        pnames = mysite.get_property_names()
        self.assertIsInstance(pnames, list)
        for item in ('defaultsort', 'disambiguation', 'displaytitle',
                     'forcetoc', 'hiddencat', 'index', 'newsectionlink',
                     'noeditsection', 'noexternallanglinks', 'nogallery',
                     'noindex', 'nonewsectionlink', 'notoc', 'score',
                     'templatedata', 'wikibase-badge-Q17437796',
                     'wikibase-badge-Q17437798', 'wikibase_item'):
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

    login = True

    def test_login_logout(self):
        """Validate login and logout methods by toggling the state."""
        site = self.get_site()
        loginstatus = pywikibot.login.LoginStatus

        self.assertTrue(site.logged_in())
        self.assertIn(site._loginstatus, (loginstatus.IN_PROGRESS,
                                          loginstatus.AS_USER))
        self.assertIn('_userinfo', site.__dict__.keys())

        self.assertIsNone(site.login())

        if site.is_oauth_token_available():
            with self.assertRaisesRegex(APIError, 'cannotlogout.*OAuth'):
                site.logout()
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


class TestClearCookies(TestCase):
    """Test cookies are cleared after logout."""

    login = True

    family = 'wikisource'
    code = 'zh'

    def test_clear_cookies(self):
        """Test cookies are cleared (T224712)."""
        site = self.get_site()
        site.login()
        site2 = pywikibot.Site('mul', 'wikisource', user=site.username())
        site2.login()
        site.logout()

        raised = False
        try:
            site.login()
        except Exception as e:
            raised = e
        self.assertFalse(raised)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
