#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Test pagegenerators module."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
__version__ = '$Id$'

import sys
import pywikibot
from pywikibot import pagegenerators

from tests.aspects import (
    unittest,
    TestCase,
    WikidataTestCase,
    DefaultSiteTestCase,
)
from tests.thread_tests import GeneratorIntersectTestCase


class TestPageGenerators(TestCase):

    """Test pagegenerators methods."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    titles = [
        # just a bunch of randomly selected titles
        u"Cities in Burkina Faso",
        u"Eastern Sayan",
        u"The Addams Family (pinball)",
        u"Talk:Hispanic (U.S. Census)",
        u"Talk:Stołpce",
        u"Talk:Nowy Sącz",
        u"Talk:Battle of Węgierska Górka",
        u"Template:!",
        u"Template:!/Doc",
        u"Template:!/Meta",
        u"Template:Template",
        u"Template:Template/Doc",
        u"Template:Template/Meta",
    ]

    def setUp(self):
        super(TestPageGenerators, self).setUp()
        self.site = self.get_site()

    def assertFunction(self, obj):
        self.assertTrue(hasattr(pagegenerators, obj))
        self.assertTrue(hasattr(getattr(pagegenerators, obj), '__call__'))

    def test_module_import(self):
        self.assertIn("pywikibot.pagegenerators", sys.modules)

    def test_PagesFromTitlesGenerator(self):
        self.assertFunction("PagesFromTitlesGenerator")
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        self.assertEqual(len(self.titles), len(tuple(gen)))

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
        self.assertEqual(len(tuple(gen)), 2)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, '/doc',
                                                      quantifier='none')
        self.assertEqual(len(tuple(gen)), 11)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['/doc', '/meta'])
        self.assertEqual(len(tuple(gen)), 4)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['/doc', '/meta'],
                                                      quantifier='none')
        self.assertEqual(len(tuple(gen)), 9)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['/doc', '/meta'],
                                                      quantifier='all')
        self.assertEqual(len(tuple(gen)), 0)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['Template', '/meta'],
                                                      quantifier='all')
        self.assertEqual(len(tuple(gen)), 1)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles, self.site)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['template', '/meta'],
                                                      quantifier='any')
        self.assertEqual(len(tuple(gen)), 4)
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
        self.assertEqual(len(tuple(gen)), 2)
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
        self.assertEqual(len(tuple(gen)), 2)
        gen = pagegenerators.RegexBodyFilterPageGenerator(iter(pages), 'This')
        self.assertEqual(len(tuple(gen)), 13)
        gen = pagegenerators.RegexBodyFilterPageGenerator(iter(pages), 'talk',
                                                          quantifier='none')
        self.assertEqual(len(tuple(gen)), 9)


class TestRepeatingGenerator(TestCase):

    """Test RepeatingGenerator."""

    family = 'wikipedia'
    code = 'en'

    cached = True

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
