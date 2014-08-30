#!/usr/bin/python
# -*- coding: utf-8  -*-
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
__version__ = '$Id$'

import sys
import pywikibot
from pywikibot import pagegenerators

from tests.utils import unittest, PywikibotTestCase


class TestPageGenerators(PywikibotTestCase):

    """Test pagegenerators methods."""

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
        self.site = pywikibot.Site('en', 'wikipedia')
        super(TestPageGenerators, self).setUp()

    def assertFunction(self, obj):
        self.assertTrue(hasattr(pagegenerators, obj))
        self.assertTrue(hasattr(getattr(pagegenerators, obj), '__call__'))

    def test_module_import(self):
        self.assertIn("pywikibot.pagegenerators", sys.modules)

    def test_PagesFromTitlesGenerator(self):
        self.assertFunction("PagesFromTitlesGenerator")
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles)
        self.assertEqual(len(self.titles), len(tuple(gen)))

    def test_NamespaceFilterPageGenerator(self):
        self.assertFunction("NamespaceFilterPageGenerator")
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles)
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, 0)
        self.assertEqual(len(tuple(gen)), 3)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles)
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, 1)
        self.assertEqual(len(tuple(gen)), 4)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles)
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, 10)
        self.assertEqual(len(tuple(gen)), 6)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles)
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, (1, 10))
        self.assertEqual(len(tuple(gen)), 10)

    def test_RegexFilterPageGenerator(self):
        self.assertFunction("RegexFilterPageGenerator")
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles)
        gen = pagegenerators.RegexFilterPageGenerator(gen, '/doc')
        self.assertEqual(len(tuple(gen)), 2)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles)
        gen = pagegenerators.RegexFilterPageGenerator(gen, '/doc',
                                                      quantifier='none')
        self.assertEqual(len(tuple(gen)), 11)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['/doc', '/meta'])
        self.assertEqual(len(tuple(gen)), 4)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['/doc', '/meta'],
                                                      quantifier='none')
        self.assertEqual(len(tuple(gen)), 9)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['/doc', '/meta'],
                                                      quantifier='all')
        self.assertEqual(len(tuple(gen)), 0)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles)
        gen = pagegenerators.RegexFilterPageGenerator(gen, ['Template', '/meta'],
                                                      quantifier='all')
        self.assertEqual(len(tuple(gen)), 1)
        gen = pagegenerators.PagesFromTitlesGenerator(self.titles)
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

if __name__ == "__main__":
    try:
        unittest.main()
    except SystemExit:
        pass
