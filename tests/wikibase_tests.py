# -*- coding: utf-8  -*-
"""
Tests for the Wikidata parts of the page module.
"""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import os
import pywikibot
import json

from utils import PywikibotTestCase, unittest

site = pywikibot.Site('en', 'wikipedia')
mainpage = pywikibot.Page(pywikibot.page.Link("Main Page", site))
wikidata = site.data_repository()


class TestGeneral(PywikibotTestCase):
    def testWikibase(self):
        if not site.has_transcluded_data:
            return
        repo = site.data_repository()
        item = pywikibot.ItemPage.fromPage(mainpage)
        self.assertType(item, pywikibot.ItemPage)
        self.assertEqual(item.getID(), 'Q5296')
        self.assertEqual(item.title(), 'Q5296')
        self.assertTrue('en' in item.labels)
        self.assertEqual(item.labels['en'], 'Main Page')
        self.assertTrue('en' in item.aliases)
        self.assertTrue('HomePage' in item.aliases['en'])
        self.assertEqual(item.namespace(), 0)
        item2 = pywikibot.ItemPage(repo, 'q5296')
        self.assertEqual(item2.getID(), 'Q5296')
        self.assertEqual(item.labels['en'], 'Main Page')
        prop = pywikibot.PropertyPage(repo, 'Property:P21')
        self.assertEqual(prop.getType(), 'wikibase-item')
        self.assertEqual(prop.namespace(), 120)
        claim = pywikibot.Claim(repo, 'p21')
        self.assertRaises(ValueError, claim.setTarget, value="test")
        claim.setTarget(pywikibot.ItemPage(repo, 'q1'))
        self.assertEqual(claim._formatDataValue(), {'entity-type': 'item', 'numeric-id': 1})

        # test WbTime
        t = pywikibot.WbTime(year=2010, hour=12, minute=43)
        self.assertEqual(t.toTimestr(), '+00000002010-01-01T12:43:00Z')

        # test WikibasePage.__cmp__
        self.assertEqual(pywikibot.ItemPage.fromPage(mainpage), pywikibot.ItemPage(repo, 'q5296'))

    def testItemPageExtensionability(self):
        class MyItemPage(pywikibot.ItemPage):
            pass
        self.assertIsInstance(MyItemPage.fromPage(mainpage), MyItemPage)


class TestLinks(PywikibotTestCase):
    """Test cases to test links stored in wikidata"""
    def setUp(self):
        super(TestLinks, self).setUp()
        self.wdp = pywikibot.ItemPage(wikidata, 'Q60')
        self.wdp.id = 'Q60'
        self.wdp._content = json.load(open(os.path.join(os.path.split(__file__)[0], 'pages', 'Q60_only_sitelinks.wd')))
        self.wdp.get()

    def test_iterlinks_page_object(self):
        page = [pg for pg in self.wdp.iterlinks() if pg.site.language() == 'af'][0]
        self.assertEquals(page, pywikibot.Page(pywikibot.Site('af', 'wikipedia'), u'New York Stad'))

    def test_iterlinks_filtering(self):
        wikilinks = list(self.wdp.iterlinks('wikipedia'))
        wvlinks = list(self.wdp.iterlinks('wikivoyage'))

        self.assertEquals(len(wikilinks), 3)
        self.assertEquals(len(wvlinks), 2)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
