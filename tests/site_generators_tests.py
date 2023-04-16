#!/usr/bin/env python3
"""Tests for generators of the site module."""
#
# (C) Pywikibot team, 2008-2023
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress
from unittest.mock import patch

import pywikibot
from pywikibot.data import api
from pywikibot.exceptions import (
    APIError,
    Error,
    HiddenKeyError,
    NoPageError,
    TimeoutError,
)
from pywikibot.tools import suppress_warnings
from tests import WARN_SITE_CODE, unittest_print
from tests.aspects import DefaultSiteTestCase, DeprecationTestCase, TestCase
from tests.utils import skipping


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
        with skipping(TimeoutError):
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
        with skipping(TimeoutError):
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

    def test_page_redirects(self):
        """Test Site.page_redirects."""
        redirects_ns_0 = set(self.site.page_redirects(
            self.mainpage,
            namespaces=0,
        ))
        redirects_ns_0_4 = set(self.site.page_redirects(
            self.mainpage,
            namespaces=[0, 4],
        ))
        redirects_ns_0_frag = set(self.site.page_redirects(
            self.mainpage,
            filter_fragments=True,
            namespaces=0,
        ))
        redirects_ns_0_nofrag = set(self.site.page_redirects(
            self.mainpage,
            filter_fragments=False,
            namespaces=0,
        ))

        self.assertLessEqual(redirects_ns_0, redirects_ns_0_4)
        self.assertLessEqual(redirects_ns_0_frag, redirects_ns_0)
        self.assertLessEqual(redirects_ns_0_nofrag, redirects_ns_0)

        for redirect in redirects_ns_0_4:
            self.assertIsInstance(redirect, pywikibot.Page)
            self.assertIn(redirect.namespace(), [0, 4])
            self.assertTrue(redirect.isRedirectPage())

        for redirect in redirects_ns_0:
            self.assertEqual(redirect.namespace(), 0)

        for redirect in redirects_ns_0_frag:
            redirect_target = redirect.getRedirectTarget()
            self.assertIsNotNone(redirect_target.section())
            redirect_target = pywikibot.Page(
                redirect_target.site,
                redirect_target.title(with_section=False)
            )
            self.assertEqual(redirect_target, self.mainpage)

        for redirect in redirects_ns_0_nofrag:
            redirect_target = redirect.getRedirectTarget()
            self.assertIsNone(redirect_target.section())
            self.assertEqual(redirect_target, self.mainpage)

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
        uniq = list(mysite.alllinks(total=10, unique=True))

        self.assertLessEqual(len(fwd), 10)

        for link in fwd:
            self.assertIsInstance(link, pywikibot.Page)
            self.assertIn(link, uniq)
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
        for cat in ac:
            self.assertIsInstance(cat, pywikibot.Category)

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
        for image in ai:
            self.assertIsInstance(image, pywikibot.FilePage)

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

    def test_querypage(self):
        """Test the site.querypage() method."""
        mysite = self.get_site()
        pages = mysite.querypage('Longpages', total=10)
        for p in pages:
            self.assertIsInstance(p, pywikibot.Page)
        with self.assertRaises(AssertionError):
            mysite.querypage('LongpageX')

    def test_longpages(self):
        """Test the site.longpages() method."""
        mysite = self.get_site()
        longpages = mysite.longpages(total=10)

        # Make sure each object returned by site.longpages() is
        # a tuple of a Page object and an int
        for tup in longpages:
            self.assertIsInstance(tup, tuple)
            self.assertLength(tup, 2)
            self.assertIsInstance(tup[0], pywikibot.Page)
            self.assertIsInstance(tup[1], int)

    def test_shortpages(self):
        """Test the site.shortpages() method."""
        mysite = self.get_site()
        shortpages = mysite.shortpages(total=10)

        # Make sure each object returned by site.shortpages() is
        # a tuple of a Page object and an int
        for tup in shortpages:
            self.assertIsInstance(tup, tuple)
            self.assertLength(tup, 2)
            self.assertIsInstance(tup[0], pywikibot.Page)
            self.assertIsInstance(tup[1], int)

    def test_ancientpages(self):
        """Test the site.ancientpages() method."""
        mysite = self.get_site()
        ancientpages = mysite.ancientpages(total=10)

        # Make sure each object returned by site.ancientpages() is
        # a tuple of a Page object and a Timestamp object
        for tup in ancientpages:
            self.assertIsInstance(tup, tuple)
            self.assertLength(tup, 2)
            self.assertIsInstance(tup[0], pywikibot.Page)
            self.assertIsInstance(tup[1], pywikibot.Timestamp)

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
        for p in unwatchedpages:
            self.assertIsInstance(p, pywikibot.Page)

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
        with self.subTest(starttime=low, endtime=high, reverse=False), \
             self.assertRaises(AssertionError):
            mysite.blocks(total=5, starttime=low, endtime=high)

        # reverse: endtime earlier than starttime
        with self.subTest(starttime=high, endtime=low, reverse=True), \
             self.assertRaises(AssertionError):
            mysite.blocks(total=5, starttime=high, endtime=low, reverse=True)

    def test_exturl_usage(self):
        """Test the site.exturlusage() method."""
        mysite = self.get_site()
        url = 'www.google.com'
        eu = list(mysite.exturlusage(url, total=10))
        self.assertLessEqual(len(eu), 10)
        for link in eu:
            self.assertIsInstance(link, pywikibot.Page)

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
                        f'NotImplementedError not raised for {item}')

    def test_unconnected(self):
        """Test site.unconnected_pages method."""
        if not self.site.data_repository():
            self.skipTest('Site is not using a Wikibase repository')
        pages = list(self.site.unconnected_pages(total=3))
        self.assertLessEqual(len(pages), 3)

        site = self.site.data_repository()
        pattern = (r'Page '
                   r'\[\[({site.sitename}:|{site.code}:)-1\]\]'
                   r" doesn't exist\.".format(site=site))
        for page in pages:
            with self.assertRaisesRegex(NoPageError, pattern):
                page.data_item()

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

        .. note:: This is not implemented as setUpClass which would be
           invoked while initialising all tests, to reduce chance of an
           error preventing all tests from running.
        """
        if hasattr(self.__class__, '_image_page'):
            return self.__class__._image_page

        mysite = self.get_site()
        page = pywikibot.Page(mysite, mysite.siteinfo['mainpage'])
        with skipping(
            StopIteration,
                msg=f'No images on the main page of site {mysite!r}'):
            imagepage = next(page.imagelinks())  # 1st image of page

        unittest_print('site_tests.TestImageUsage found {} on {}'
                       .format(imagepage, page))

        self.__class__._image_page = imagepage
        return imagepage

    def test_image_usage(self):
        """Test the site.imageusage() method."""
        mysite = self.get_site()
        imagepage = self.imagepage
        iu = list(mysite.imageusage(imagepage, total=10))
        self.assertLessEqual(len(iu), 10)
        for link in iu:
            self.assertIsInstance(link, pywikibot.Page)

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


class TestLogEvents(DefaultSiteTestCase):

    """Test logevents methods."""

    def test_logevents(self):
        """Test logevents method."""
        mysite = self.get_site()
        le = list(mysite.logevents(total=10))
        self.assertLessEqual(len(le), 10)
        for entry in le:
            self.assertIsInstance(entry, pywikibot.logentries.LogEntry)

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

    def test_basic(self):
        """Test the site.recentchanges() method."""
        mysite = self.site
        rc = list(mysite.recentchanges(total=10))
        self.assertLessEqual(len(rc), 10)
        for change in rc:
            self.assertIsInstance(change, dict)

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
    rights = 'patrol'

    def test_patrolled(self):
        """Test the site.recentchanges() with patrolled boolean flags."""
        mysite = self.site
        for change in mysite.recentchanges(patrolled=True, total=5):
            self.assertIsInstance(change, dict)
            self.assertIn('patrolled', change)

        for change in mysite.recentchanges(patrolled=False, total=5):
            self.assertIsInstance(change, dict)
            self.assertNotIn('patrolled', change)


class TestUserWatchedPages(DefaultSiteTestCase):

    """Test user watched pages."""

    login = True
    rights = 'viewmywatchlist'

    def test_watched_pages(self):
        """Test the site.watched_pages() method."""
        gen = self.site.watched_pages(total=5, force=False)
        self.assertIsInstance(gen.request, api.CachedRequest)
        for page in gen:
            self.assertIsInstance(page, pywikibot.Page)

        gen.restart()  # repeat to use the cache
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
            for hit in se:
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertEqual(hit.namespace(), 0)
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
            raise

    def test_search_where_title(self):
        """Test site.search() method with 'where' parameter set to title."""
        search_gen = self.site.search(
            'wiki', namespaces=0, total=10, where='title')
        expected_params = {
            'prop': ['info', 'imageinfo', 'categoryinfo'],
            'inprop': ['protection'],
            'iiprop': ['timestamp', 'user', 'comment', 'url', 'size', 'sha1',
                       'metadata'],
            'iilimit': ['max'], 'generator': ['search'], 'action': ['query'],
            'indexpageids': [True], 'continue': [True],
            'gsrnamespace': [0], 'gsrsearch': ['wiki'], 'gsrwhat': ['title']}
        self.assertEqual(search_gen.request._params, expected_params)
        for hit in search_gen:
            self.assertIsInstance(hit, pywikibot.Page)
            self.assertEqual(hit.namespace(), 0)


class TestUserContribsAsUser(DefaultSiteTestCase):

    """Test site method site.usercontribs() with bot user."""

    login = True

    def test_basic(self):
        """Test the site.usercontribs() method."""
        mysite = self.get_site()
        uc = list(mysite.usercontribs(user=mysite.user(), total=10))
        self.assertLessEqual(len(uc), 10)
        for contrib in uc:
            self.assertIsInstance(contrib, dict)
            self.assertIn('user', contrib)
            self.assertEqual(contrib['user'], mysite.user())

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

    def test_basic(self):
        """Test the site.alldeletedrevisions() method."""
        mysite = self.get_site()
        result = list(mysite.alldeletedrevisions(user=mysite.user(), total=10))

        if not result:
            self.skipTest('No deleted revisions available')

        for data in result:
            with self.subTest(data=data):
                self.assertIsInstance(data, dict)
                self.assertIn('revisions', data)
                self.assertIsInstance(data['revisions'], list)

                for drev in data['revisions']:
                    self.assertIsInstance(drev, dict)
                    self.assertIn('user', drev)
                    self.assertEqual(drev['user'], mysite.user())

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
    rights = 'viewmywatchlist'

    def test_watchlist_revs(self):
        """Test the site.watchlist_revs() method."""
        mysite = self.get_site()
        wl = list(mysite.watchlist_revs(total=10))
        self.assertLessEqual(len(wl), 10)
        for rev in wl:
            self.assertIsInstance(rev, dict)
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

    @classmethod
    def setUpClass(cls):
        """Skip test on beta due to T282602."""
        super().setUpClass()
        site = cls.get_site()
        if site.family.name in ('wpbeta', 'wsbeta'):
            cls.skipTest(cls,
                         'Skipping test on {} due to T282602' .format(site))

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
        for a_page in rn:
            self.assertIsInstance(a_page, pywikibot.Page)
            self.assertFalse(a_page.isRedirectPage())

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
        for rev in [139992, 139993]:
            self.assertIn(rev, self.mainpage._revisions)
        # revids as list of str
        self.mysite.loadrevisions(self.mainpage, revids=['139994', '139995'])
        for rev in [139994, 139995]:
            self.assertIn(rev, self.mainpage._revisions)
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
        for ts in timestamps:
            self.assertLess(ts, '2002-01-31T00:00:00Z')

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
        for rev in revs:
            self.assertTrue(139900 <= rev <= 140100)

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
        for rev in self.mainpage._revisions.values():
            self.assertEqual(rev.user, 'Magnus Manske')

    def test_loadrevisions_excludeuser(self):
        """Test the site.loadrevisions() method, excluding user."""
        excludeuser = 'Magnus Manske'  # exclude revisions made by this user
        self.mainpage._revisions = {}
        self.mysite.loadrevisions(self.mainpage, rvdir=True,
                                  excludeuser=excludeuser)
        for rev in self.mainpage._revisions.values():
            self.assertNotEqual(rev.user, excludeuser)

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
        item = next(gen)
        self.assertIn('sha1', item)
        self.assertIn('size', item)
        self.assertIn('user', item)

    def test_filearchive_reverse(self):
        """Test reverse parameter."""
        gen1 = self.site.filearchive(total=1)
        gen2 = self.site.filearchive(reverse=True, total=1)
        self.assertNotIn('fadir=', str(gen1.request))
        self.assertIn('fadir=descending', str(gen2.request))
        fa1 = next(gen1)
        fa2 = next(gen2)
        self.assertLess(fa1['name'], fa2['name'])

    def test_filearchive_start(self):
        """Test start/end parameters."""
        gen = self.site.filearchive(start='py', end='wiki', total=1)
        self.assertIn('fafrom=py', str(gen.request))
        self.assertIn('fato=wiki', str(gen.request))
        item = next(gen)
        self.assertGreaterEqual(item['name'], 'Py')

    def test_filearchive_sha1(self):
        """Test sha1 parameter."""
        sha1 = '0d5a00aa774100408e60da09f5fb21f253b366f1'
        gen = self.site.filearchive(sha1=sha1, prop='sha1', total=1)
        self.assertIn('fasha1=' + sha1, str(gen.request))
        item = next(gen)
        self.assertEqual(item['sha1'], sha1)


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
        pageids += pageids
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
        links = mysite.pagelinks(mainpage, total=10)
        # preloadpages will send the page ids,
        # as they have already been loaded by pagelinks
        for count, page in enumerate(mysite.preloadpages(links), start=1):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertTrue(hasattr(page, '_revid'))
                self.assertLength(page._revisions, 1)
                self.assertIn(page._revid, page._revisions)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
            if count >= 5:
                break

    def test_titles(self):
        """Test basic preloading with titles."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        links = mysite.pagelinks(mainpage, total=10)

        # remove the pageids that have already been loaded above by pagelinks
        # so that preloadpages will use the titles instead
        for page in links:
            if hasattr(page, '_pageid'):
                self.assertEqual(page.pageid, page._pageid)
            del page._pageid

        for count, page in enumerate(mysite.preloadpages(links), start=1):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertLength(page._revisions, 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
            if count >= 5:
                break

    def test_preload_continuation(self):
        """Test preloading continuation works."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        links = mysite.pagelinks(mainpage, total=10)
        for count, page in enumerate(mysite.preloadpages(links, groupsize=5)):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertLength(page._revisions, 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
            if count >= 5:
                break

    def test_preload_high_groupsize(self):
        """Test preloading continuation with groupsize greater than total."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()

        # Determine if there are enough links on the main page,
        # for the test to be useful.
        link_count = len(list(mysite.pagelinks(mainpage, total=10)))
        if link_count < 2:
            self.skipTest('insufficient links on main page')

        # get a fresh generator; we now know how many results it will have,
        # if it is less than 10.
        links = mysite.pagelinks(mainpage, total=10)
        count = 0
        for count, page in enumerate(
                mysite.preloadpages(links, groupsize=50), start=1):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertLength(page._revisions, 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
        self.assertEqual(count, link_count)

    def test_preload_low_groupsize(self):
        """Test preloading continuation with groupsize greater than total."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()

        # Determine if there are enough links on the main page,
        # for the test to be useful.
        link_count = len(list(mysite.pagelinks(mainpage, total=10)))
        if link_count < 2:
            self.skipTest('insufficient links on main page')

        # get a fresh generator; we now know how many results it will have,
        # if it is less than 10.
        links = mysite.pagelinks(mainpage, total=10)
        count = 0
        for count, page in enumerate(
                mysite.preloadpages(links, groupsize=5), start=1):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertLength(page._revisions, 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
        self.assertEqual(count, link_count)

    def test_preload_unexpected_titles_using_pageids(self):
        """Test sending pageids with unnormalized titles, causing warnings."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
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
        for count, page in enumerate(gen):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertLength(page._revisions, 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
            if count >= 5:
                break

    def test_preload_unexpected_titles_using_titles(self):
        """Test sending unnormalized titles, causing warnings."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
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
        for count, page in enumerate(gen):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertLength(page._revisions, 1)
                self.assertIsNotNone(page._revisions[page._revid].text)
                self.assertFalse(hasattr(page, '_pageprops'))
            if count >= 5:
                break

    def test_preload_invalid_titles_without_pageids(self):
        """Test sending invalid titles. No warnings issued, but it should."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        links = list(mysite.pagelinks(mainpage, total=10))
        if len(links) < 2:
            self.skipTest('insufficient links on main page')

        for page in links:
            page._link._text += ' foobar'
            del page._pageid

        gen = mysite.preloadpages(links, groupsize=5)
        for count, page in enumerate(gen):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            self.assertFalse(page.exists(), f'page {page} exists')
            if count >= 5:
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

    @patch.object(pywikibot, 'info')
    def test_preload_langlinks_count(self, output_mock):
        """Test preloading continuation works."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        links = list(mysite.pagelinks(mainpage, total=20))

        with suppress_warnings(WARN_SITE_CODE, category=UserWarning):
            pages = list(mysite.preloadpages(links, groupsize=5,
                                             langlinks=True, quiet=False))

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

    def test_preload_categories(self):
        """Test preloading categories works."""
        mysite = self.get_site()
        cats = mysite.randompages(total=10, namespaces=14)
        gen = mysite.preloadpages(cats, categories=True)
        for count, page in enumerate(gen):
            with self.subTest(page=page.title()):
                self.assertTrue(hasattr(page, '_categories'))
                # content=True will bypass cache
                self.assertEqual(page._categories,
                                 set(page.categories(content=True)))
            if count >= 5:
                break

    def test_preload_content(self):
        """Test preloading templates and langlinks works."""
        mysite = self.get_site()

        page = next(mysite.preloadpages([self.get_mainpage()], content=False))
        self.assertFalse(page.has_content())

        page = next(mysite.preloadpages([self.get_mainpage()], content=True))
        self.assertTrue(page.has_content())


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
