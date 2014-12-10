#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Test pagegenerators module."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
__version__ = '$Id$'

import datetime
import os
import sys

import pywikibot
from pywikibot import pagegenerators

from pywikibot.pagegenerators import (
    PagesFromTitlesGenerator,
    PreloadingGenerator,
)

from tests import _data_dir
from tests.aspects import (
    unittest,
    TestCase,
    WikidataTestCase,
    DefaultSiteTestCase,
)
from tests.thread_tests import GeneratorIntersectTestCase


en_wp_page_titles = (
    # just a bunch of randomly selected titles for English Wikipedia tests
    u"Eastern Sayan",
    u"The Addams Family (pinball)",
    u"Talk:Nowy Sącz",
    u"Talk:Battle of Węgierska Górka",
    u"Template:!",
    u"Template:Template",
)

en_wp_nopage_titles = (
    u"Cities in Burkina Faso",
    u"Talk:Hispanic (U.S. Census)",
    u"Talk:Stołpce",
    u"Template:!/Doc",
    u"Template:!/Meta",
    u"Template:Template/Doc",
    u"Template:Template/Meta",
)


class TestDryPageGenerators(TestCase):

    """Test pagegenerators methods."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    titles = en_wp_page_titles + en_wp_nopage_titles

    def setUp(self):
        super(TestDryPageGenerators, self).setUp()
        self.site = self.get_site()

    def assertFunction(self, obj):
        self.assertTrue(hasattr(pagegenerators, obj))
        self.assertTrue(hasattr(getattr(pagegenerators, obj), '__call__'))

    def test_module_import(self):
        self.assertIn("pywikibot.pagegenerators", sys.modules)

    def test_PagesFromTitlesGenerator(self):
        self.assertFunction("PagesFromTitlesGenerator")
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        self.assertPagelistTitles(gen, self.titles)

    def test_NamespaceFilterPageGenerator(self):
        self.assertFunction("NamespaceFilterPageGenerator")
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, 0)
        self.assertEqual(len(tuple(gen)), 3)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, 1)
        self.assertEqual(len(tuple(gen)), 4)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, 10)
        self.assertEqual(len(tuple(gen)), 6)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, (1, 10))
        self.assertEqual(len(tuple(gen)), 10)

    def test_RegexFilterPageGenerator(self):
        self.assertFunction("RegexFilterPageGenerator")
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, '/doc')
        self.assertPagelistTitles(gen,
                                  ('Template:!/Doc', 'Template:Template/Doc'))
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, '/doc',
                                                      quantifier='none')
        self.assertEqual(len(tuple(gen)), 11)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['/doc', '/meta'])
        self.assertPagelistTitles(gen,
                                  ('Template:!/Doc',
                                   'Template:!/Meta',
                                   'Template:Template/Doc',
                                   'Template:Template/Meta'))
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['/doc', '/meta'],
                                                      quantifier='none')
        self.assertEqual(len(tuple(gen)), 9)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['/doc', '/meta'],
                                                      quantifier='all')
        self.assertPagelistTitles(gen, ())
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['Template', '/meta'],
                                                      quantifier='all')
        self.assertPagelistTitles(gen, ('Template:Template/Meta'))
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['template', '/meta'],
                                                      quantifier='any')
        self.assertPagelistTitles(gen,
                                  ('Template:Template',
                                   'Template:!/Meta',
                                   'Template:Template/Doc',
                                   'Template:Template/Meta'))
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles,
                                                      site=self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['template', '/meta'],
                                                      quantifier='any',
                                                      ignore_namespace=False)
        self.assertEqual(len(tuple(gen)), 6)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles,
                                                      site=self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['template', '/meta'],
                                                      quantifier='all',
                                                      ignore_namespace=False)
        self.assertPagelistTitles(gen,
                                  ('Template:!/Meta',
                                   'Template:Template/Meta'))
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles,
                                                      site=self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['template', '/meta'],
                                                      quantifier='none',
                                                      ignore_namespace=False)
        self.assertEqual(len(tuple(gen)), 7)

    def test_RegexBodyFilterPageGenerator(self):
        self.assertFunction("RegexBodyFilterPageGenerator")
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles,
                                                      site=self.site)
        pages = []
        for p in gen:
            p.text = u"This is the content of %s as a sample" % p.title()
            pages.append(p)
        gen = pagegenerators.RegexBodyFilterPageGenerator(iter(pages), '/doc')
        self.assertPagelistTitles(gen,
                                  ('Template:!/Doc', 'Template:Template/Doc'))
        gen = pagegenerators.RegexBodyFilterPageGenerator(iter(pages), 'This')
        self.assertPagelistTitles(gen, self.titles)
        gen = pagegenerators.RegexBodyFilterPageGenerator(iter(pages), 'talk',
                                                          quantifier='none')
        self.assertEqual(len(tuple(gen)), 9)


class EdittimeFilterPageGeneratorTestCase(TestCase):

    """Test EdittimeFilterPageGenerator."""

    family = 'wikipedia'
    code = 'en'

    titles = en_wp_page_titles

    def test_first_edit(self):
        expect = (
            u'The Addams Family (pinball)',
            u'Talk:Nowy Sącz',
            u'Template:Template',
        )
        gen = PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.EdittimeFilterPageGenerator(
            gen, first_edit_end=datetime.datetime(2006, 1, 1))
        self.assertPagelistTitles(gen, titles=expect, site=self.site)

        gen = PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.EdittimeFilterPageGenerator(
            gen, first_edit_start=datetime.datetime(2006, 1, 1))
        opposite_pages = list(gen)
        self.assertTrue(all(isinstance(p, pywikibot.Page)
                            for p in opposite_pages))
        self.assertTrue(all(p.title not in expect for p in opposite_pages))

    def test_last_edit(self):
        two_days_ago = datetime.datetime.now() - datetime.timedelta(days=2)
        nine_days_ago = datetime.datetime.now() - datetime.timedelta(days=9)

        gen = PagesFromTitlesGenerator(['Wikipedia:Sandbox'], self.site)
        gen = pagegenerators.EdittimeFilterPageGenerator(
            gen, last_edit_start=two_days_ago)
        self.assertEqual(len(list(gen)), 1)

        gen = PagesFromTitlesGenerator(['Wikipedia:Sandbox'], self.site)
        gen = pagegenerators.EdittimeFilterPageGenerator(
            gen, last_edit_end=two_days_ago)
        self.assertEqual(len(list(gen)), 0)

        gen = PagesFromTitlesGenerator(['Template:Sidebox'], self.site)
        gen = pagegenerators.EdittimeFilterPageGenerator(
            gen, last_edit_end=nine_days_ago)
        self.assertEqual(len(list(gen)), 1)

        gen = PagesFromTitlesGenerator(['Template:Sidebox'], self.site)
        gen = pagegenerators.EdittimeFilterPageGenerator(
            gen, last_edit_start=nine_days_ago)
        self.assertEqual(len(list(gen)), 0)


class TestRepeatingGenerator(TestCase):

    """Test RepeatingGenerator."""

    family = 'wikipedia'
    code = 'en'

    def test_RepeatingGenerator(self):
        # site.recentchanges() includes external edits (from wikidata),
        # so total=4 is not too high
        items = list(
            pagegenerators.RepeatingGenerator(self.site.recentchanges,
                                              key_func=lambda x: x['revid'],
                                              sleep_duration=10,
                                              reverse=True,
                                              namespaces=[0],
                                              total=4)
        )
        self.assertEqual(len(items), 4)
        timestamps = [pywikibot.Timestamp.fromISOformat(item['timestamp'])
                      for item in items]
        self.assertEqual(sorted(timestamps), timestamps)
        self.assertTrue(all(item['ns'] == 0 for item in items))
        self.assertEqual(len(set(item['revid'] for item in items)), 4)


class TestTextfilePageGenerator(DefaultSiteTestCase):

    """Test loading pages from a textfile."""

    dry = True

    expected_titles = {
        'case-sensitive': ('file', 'bracket', 'MediaWiki:Test',
                           'under score', 'Upper case'),
        'first-letter': ('File', 'Bracket', 'MediaWiki:Test', 'Under score',
                         'Upper case'),
    }

    def test_brackets(self):
        filename = os.path.join(_data_dir, 'pagelist-brackets.txt')
        site = self.get_site()
        titles = list(pagegenerators.TextfilePageGenerator(filename, site))
        self.assertPagelistTitles(titles, self.expected_titles[site.case()])

    def test_lines(self):
        filename = os.path.join(_data_dir, 'pagelist-lines.txt')
        site = self.get_site()
        titles = list(pagegenerators.TextfilePageGenerator(filename, site))
        self.assertPagelistTitles(titles, self.expected_titles[site.case()])


class TestPreloadingGenerator(DefaultSiteTestCase):

    """Test preloading generator on lists."""

    def test_basic(self):
        """Test PreloadingGenerator with a list of pages."""
        mainpage = self.get_mainpage()
        links = list(self.site.pagelinks(mainpage, total=10))
        count = 0
        for page in PreloadingGenerator(links, step=20):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertTrue(hasattr(page, "_text"))
                self.assertEqual(len(page._revisions), 1)
                self.assertFalse(hasattr(page, '_pageprops'))
            count += 1
        self.assertEqual(len(links), count)

    def test_low_step(self):
        """Test PreloadingGenerator with a list of pages."""
        mainpage = self.get_mainpage()
        links = list(self.site.pagelinks(mainpage, total=20))
        count = 0
        for page in PreloadingGenerator(links, step=10):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertTrue(hasattr(page, "_text"))
                self.assertEqual(len(page._revisions), 1)
                self.assertFalse(hasattr(page, '_pageprops'))
            count += 1
        self.assertEqual(len(links), count)


class TestDequePreloadingGenerator(DefaultSiteTestCase):

    """Test preloading generator on lists."""

    def test_deque_preloading(self):
        """Test pages being added to a DequePreloadingGenerator."""
        mainpage = self.get_mainpage()

        pages = pywikibot.tools.DequeGenerator([mainpage])
        gen = pagegenerators.DequePreloadingGenerator(pages)
        pages_out = list()
        for page in gen:
            pages_out.append(page)
            # Add a page to the generator
            if not page.isTalkPage():
                pages.extend([page.toggleTalkPage()])

        self.assertTrue(all(isinstance(page, pywikibot.Page) for page in pages_out))
        self.assertIn(mainpage, pages_out)
        self.assertIn(mainpage.toggleTalkPage(), pages_out)
        self.assertEqual(len(pages_out), 2)
        self.assertTrue(pages_out[1].isTalkPage())


class TestPreloadingItemGenerator(WikidataTestCase):

    """Test preloading item generator."""

    def test_non_item_gen(self):
        """Test TestPreloadingItemGenerator with ReferringPageGenerator."""
        site = self.get_site()
        instance_of_page = pywikibot.Page(site, 'Property:P31')
        ref_gen = pagegenerators.ReferringPageGenerator(instance_of_page, total=5)
        gen = pagegenerators.PreloadingItemGenerator(ref_gen)
        self.assertTrue(all(isinstance(item, pywikibot.ItemPage) for item in gen))


class TestFactoryGenerator(DefaultSiteTestCase):

    """Test pagegenerators.GeneratorFactory."""

    def test_newpages_default(self):
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-newpages')
        gen = gf.getCombinedGenerator()
        pages = set(gen)
        self.assertGreater(len(pages), 0)
        self.assertLessEqual(len(pages), 60)

    def test_newpages_ns_default(self):
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-newpages:10')
        gen = gf.getCombinedGenerator()
        self.assertPagesInNamespaces(gen, 0)

    def test_newpages_ns(self):
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-ns:1')
        gf.handleArg('-newpages:10')
        gen = gf.getCombinedGenerator()
        self.assertPagesInNamespaces(gen, 1)

    def test_recentchanges_ns_default(self):
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-recentchanges:50')
        gen = gf.getCombinedGenerator()
        self.assertPagesInNamespacesAll(gen, set([0, 1, 2]), skip=True)

    def test_recentchanges_ns(self):
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-ns:1')
        gf.handleArg('-recentchanges:10')
        gen = gf.getCombinedGenerator()
        self.assertPagesInNamespaces(gen, 1)

    def test_recentchanges_ns_multi(self):
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-ns:1')
        gf.handleArg('-ns:3')
        gf.handleArg('-recentchanges:10')
        gen = gf.getCombinedGenerator()
        self.assertPagesInNamespaces(gen, set([1, 3]))


class TestLogeventsFactoryGenerator(DefaultSiteTestCase):

    """Test GeneratorFactory with pagegenerators.LogeventsPageGenerator."""

    user = True

    @unittest.expectedFailure
    def test_logevents_parse(self):
        gf = pagegenerators.GeneratorFactory()
        self.assertFalse(gf.handleArg("-log"))
        self.assertFalse(gf.handleArg("-log:text_here"))
        # TODO: Throw an error for incorrect logtypes
        self.assertRaises(gf.handleArg("-this_will_never_be_a_typelog"),
                          Exception)

    def test_logevents_default(self):
        gf = pagegenerators.GeneratorFactory(site=self.site)
        self.assertTrue(gf.handleArg('-newuserslog'))
        gen = gf.getCombinedGenerator()
        pages = set(gen)
        self.assertLessEqual(len(pages), 500)
        self.assertTrue(all(isinstance(item, pywikibot.Page) for item in pages))

    def test_logevents_default_multi(self):
        gf = pagegenerators.GeneratorFactory(site=self.site)
        self.assertTrue(gf.handleArg('-newuserslog:10'))
        gen = gf.getCombinedGenerator()
        pages = set(gen)
        self.assertLessEqual(len(pages), 10)
        self.assertTrue(all(isinstance(item, pywikibot.Page) for item in pages))

    def test_logevents_ns(self):
        gf = pagegenerators.GeneratorFactory(site=self.site)
        gf.handleArg('-ns:1')
        gf.handleArg('-newuserslog:10')
        gen = gf.getCombinedGenerator()
        self.assertPagesInNamespaces(gen, 1)
        self.assertTrue(all(isinstance(item, pywikibot.Page) for item in gen))

    def test_logevents_user_multi(self):
        gf = pagegenerators.GeneratorFactory(site=self.site)
        user = self.get_site().user()
        self.assertTrue(gf.handleArg('-newuserslog:' + user + ';10'))
        gen = gf.getCombinedGenerator()
        pages = set(gen)

        if not pages:
            raise unittest.SkipTest('No user creation log entries for ' + user)

        # TODO: Check if the pages generated correspond to the user
        # (no easy way of checking from pages)

        self.assertLessEqual(len(pages), 10)
        self.assertTrue(all(isinstance(item, pywikibot.Page) for item in pages))


class PageGeneratorIntersectTestCase(DefaultSiteTestCase,
                                     GeneratorIntersectTestCase):

    """Page intersect_generators test cases."""

    def test_intersect_newpages_twice(self):
        site = self.get_site()
        self.assertEqualItertools(
            [pagegenerators.NewpagesPageGenerator(site=site, total=10),
             pagegenerators.NewpagesPageGenerator(site=site, total=10)])

    def test_intersect_newpages_and_recentchanges(self):
        site = self.get_site()
        self.assertEqualItertools(
            [pagegenerators.NewpagesPageGenerator(site=site, total=50),
             pagegenerators.RecentChangesPageGenerator(site=site, total=200)])


class EnglishWikipediaPageGeneratorIntersectTestCase(GeneratorIntersectTestCase):

    """Page intersect_generators test cases."""

    family = 'wikipedia'
    code = 'en'

    def test_intersect_newpages_csd(self):
        site = self.get_site()
        self.assertEqualItertools(
            [pagegenerators.NewpagesPageGenerator(site=site, total=10),
             pagegenerators.CategorizedPageGenerator(
                pywikibot.Category(site,
                                   'Category:Candidates_for_speedy_deletion'))
             ])


if __name__ == "__main__":
    try:
        unittest.main()
    except SystemExit:
        pass
