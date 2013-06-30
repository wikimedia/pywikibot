# -*- coding: utf-8  -*-
"""
Tests for the page module.
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


import unittest
import pywikibot
import pywikibot.page

site = pywikibot.Site('en', 'wikipedia')
mainpage = pywikibot.Page(pywikibot.page.Link("Main Page", site))
maintalk = pywikibot.Page(pywikibot.page.Link("Talk:Main Page", site))
badpage = pywikibot.Page(pywikibot.page.Link("There is no page with this title",
                         site))


class TestLinkObject(unittest.TestCase):
    """Test cases for Link objects"""

    enwiki = pywikibot.Site("en", "wikipedia")
    frwiki = pywikibot.Site("fr", "wikipedia")
    itwikt = pywikibot.Site("it", "wiktionary")

    namespaces = {0: [u""],        # en.wikipedia.org namespaces for testing
                  1: [u"Talk:"],   # canonical form first, then others
                  2: [u"User:"],   # must end with :
                  3: [u"User talk:", u"User_talk:"],
                  4: [u"Wikipedia:", u"Project:", u"WP:"],
                  5: [u"Wikipedia talk:", u"Project talk:", u"Wikipedia_talk:",
                      u"Project_talk:", u"WT:"],
                  6: [u"File:"],
                  7: [u"Image talk:", u"Image_talk:"],
                  8: [u"MediaWiki:"],
                  9: [u"MediaWiki talk:", u"MediaWiki_talk:"],
                  10: [u"Template:"],
                  11: [u"Template talk:", u"Template_talk:"],
                  12: [u"Help:"],
                  13: [u"Help talk:", u"Help_talk:"],
                  14: [u"Category:"],
                  15: [u"Category talk:", u"Category_talk:"],
                  100: [u"Portal:"],
                  101: [u"Portal talk:", u"Portal_talk:"],
                  }
    titles = {
        # just a bunch of randomly selected titles
        # input format                  : expected output format
        u"Cities in Burkina Faso":        u"Cities in Burkina Faso",
        u"eastern Sayan":                 u"Eastern Sayan",
        u"The_Addams_Family_(pinball)":   u"The Addams Family (pinball)",
        u"Hispanic  (U.S.  Census)":      u"Hispanic (U.S. Census)",
        u"Stołpce":                       u"Stołpce",
        u"Nowy_Sącz":                     u"Nowy Sącz",
        u"battle of Węgierska  Górka":    u"Battle of Węgierska Górka",
    }
    # random bunch of possible section titles
    sections = [u"",
                u"#Phase_2",
                u"#History",
                u"#later life",
                ]

    def testNamespaces(self):
        """Test that Link() normalizes namespace names"""
        for num in self.namespaces:
            for prefix in self.namespaces[num]:
                l = pywikibot.page.Link(prefix+self.titles.keys()[0],
                                        self.enwiki)
                self.assertEqual(l.namespace, num)
                # namespace prefixes are case-insensitive
                m = pywikibot.page.Link(prefix.lower()+self.titles.keys()[1],
                                        self.enwiki)
                self.assertEqual(m.namespace, num)

    def testTitles(self):
        """Test that Link() normalizes titles"""
        for title in self.titles:
            for num in (0, 1):
                l = pywikibot.page.Link(self.namespaces[num][0]+title)
                self.assertEqual(l.title, self.titles[title])
                # prefixing name with ":" shouldn't change result
                m = pywikibot.page.Link(":" + self.namespaces[num][0] + title)
                self.assertEqual(m.title, self.titles[title])

    def testHashCmp(self):
        # All links point to en:wikipedia:Test
        l1 = pywikibot.page.Link('Test', source=self.enwiki)
        l2 = pywikibot.page.Link('en:Test', source=self.frwiki)
        l3 = pywikibot.page.Link('wikipedia:en:Test', source=self.itwikt)

        def assertHashCmp(link1, link2):
            self.assertEqual(link1, link2)
            self.assertEqual(hash(link1), hash(link2))

        assertHashCmp(l1, l2)
        assertHashCmp(l1, l3)
        assertHashCmp(l2, l3)

        # fr:wikipedia:Test
        other = pywikibot.page.Link('Test', source=self.frwiki)

        self.assertNotEqual(l1, other)
        self.assertNotEqual(hash(l1), hash(other))


class TestPageObject(unittest.TestCase):
    def assertType(self, obj, cls):
        """Assert that obj is an instance of type cls"""
        return self.assertTrue(isinstance(obj, cls))

    def testGeneral(self):
        self.assertEqual(str(mainpage), "[[%s:%s]]"
                                        % (site.lang, mainpage.title()))
        self.assertTrue(mainpage < maintalk)

    def testSite(self):
        """Test site() method"""
        self.assertEqual(mainpage.site, site)

    def testNamespace(self):
        """Test namespace() method"""
        self.assertEqual(mainpage.namespace(), 0)
        self.assertEqual(maintalk.namespace(), 1)
        self.assertEqual(badpage.namespace(), 0)

    def testTitle(self):
        """Test title() method options."""
        p1 = pywikibot.Page(site, u"Help:Test page#Testing")
        self.assertEqual(p1.title(),
                         u"Help:Test page#Testing")
        self.assertEqual(p1.title(underscore=True),
                         u"Help:Test_page#Testing")
        self.assertEqual(p1.title(withNamespace=False),
                         u"Test page#Testing")
        self.assertEqual(p1.title(withSection=False),
                         u"Help:Test page")
        self.assertEqual(p1.title(withNamespace=False, withSection=False),
                         u"Test page")
        self.assertEqual(p1.title(asUrl=True),
                         "Help%3ATest_page%23Testing")
        self.assertEqual(p1.title(asLink=True),
                         u"[[Help:Test page#Testing]]")
        self.assertEqual(p1.title(asLink=True, forceInterwiki=True),
                         u"[[en:Help:Test page#Testing]]")
        self.assertEqual(p1.title(asLink=True, textlink=True),
                         p1.title(asLink=True))
        # also test a page with non-ASCII chars and a different namespace
        p2 = pywikibot.Page(site, u"File:Jean-Léon Gérôme 003.jpg")
        self.assertEqual(p2.title(),
                         u"File:Jean-Léon Gérôme 003.jpg")
        self.assertEqual(p2.title(underscore=True),
                         u"File:Jean-Léon_Gérôme_003.jpg")
        self.assertEqual(p2.title(withNamespace=False),
                         u"Jean-Léon Gérôme 003.jpg")
        self.assertEqual(p2.title(withSection=False),
                         u"File:Jean-Léon Gérôme 003.jpg")
        self.assertEqual(p2.title(withNamespace=False, withSection=False),
                         u"Jean-Léon Gérôme 003.jpg")
        self.assertEqual(p2.title(asUrl=True),
                         u"File%3AJean-L%C3%A9on_G%C3%A9r%C3%B4me_003.jpg")
        self.assertEqual(p2.title(asLink=True),
                         u"[[File:Jean-Léon Gérôme 003.jpg]]")
        self.assertEqual(p2.title(asLink=True, forceInterwiki=True),
                         u"[[en:File:Jean-Léon Gérôme 003.jpg]]")
        self.assertEqual(p2.title(asLink=True, textlink=True),
                         u"[[:File:Jean-Léon Gérôme 003.jpg]]")
        self.assertEqual(p2.title(as_filename=True),
                         u"File_Jean-Léon_Gérôme_003.jpg")

    def testSection(self):
        """Test section() method."""
        # use same pages as in previous test
        p1 = pywikibot.Page(site, u"Help:Test page#Testing")
        p2 = pywikibot.Page(site, u"File:Jean-Léon Gérôme 003.jpg")
        self.assertEqual(p1.section(), u"Testing")
        self.assertEqual(p2.section(), None)

    def testIsTalkPage(self):
        """Test isTalkPage() method."""
        p1 = pywikibot.Page(site, u"First page")
        p2 = pywikibot.Page(site, u"Talk:First page")
        p3 = pywikibot.Page(site, u"User:Second page")
        p4 = pywikibot.Page(site, u"User talk:Second page")
        self.assertEqual(p1.isTalkPage(), False)
        self.assertEqual(p2.isTalkPage(), True)
        self.assertEqual(p3.isTalkPage(), False)
        self.assertEqual(p4.isTalkPage(), True)

    def testIsCategory(self):
        """Test isCategory method."""
        p1 = pywikibot.Page(site, u"First page")
        p2 = pywikibot.Page(site, u"Category:Second page")
        p3 = pywikibot.Page(site, u"Category talk:Second page")
        self.assertEqual(p1.isCategory(), False)
        self.assertEqual(p2.isCategory(), True)
        self.assertEqual(p3.isCategory(), False)

    def testIsImage(self):
        p1 = pywikibot.Page(site, u"First page")
        p2 = pywikibot.Page(site, u"File:Second page")
        p3 = pywikibot.Page(site, u"Image talk:Second page")
        self.assertEqual(p1.isImage(), False)
        self.assertEqual(p2.isImage(), True)
        self.assertEqual(p3.isImage(), False)

    def testIsRedirect(self):
        p1 = pywikibot.Page(site, u'User:Legoktm/R1')
        p2 = pywikibot.Page(site, u'User:Legoktm/R2')
        self.assertTrue(p1.isRedirectPage())
        self.assertEqual(p1.getRedirectTarget(), p2)

    def testPageGet(self):
        p1 = pywikibot.Page(site, u'User:Legoktm/R2')
        p2 = pywikibot.Page(site, u'User:Legoktm/R1')
        p3 = pywikibot.Page(site, u'User:Legoktm/R3')

        text = u'This page is used in the [[mw:Manual:Pywikipediabot]] testing suite.'
        self.assertEqual(p1.get(), text)
        self.assertRaises(pywikibot.exceptions.IsRedirectPage, p2.get)
        self.assertRaises(pywikibot.exceptions.NoPage, p3.get)

    def testApiMethods(self):
        """Test various methods that rely on API."""
        # since there is no way to predict what data the wiki will return,
        # we only check that the returned objects are of correct type.
        self.assertType(mainpage.get(), unicode)
        self.assertType(maintalk.get(), unicode)
        self.assertRaises(pywikibot.NoPage, badpage.get)
        self.assertType(mainpage.latestRevision(), int)
        self.assertType(mainpage.userName(), unicode)
        self.assertType(mainpage.isIpEdit(), bool)
        self.assertType(mainpage.exists(), bool)
        self.assertType(mainpage.isRedirectPage(), bool)
        self.assertType(mainpage.isEmpty(), bool)
        self.assertEqual(mainpage.toggleTalkPage(), maintalk)
        self.assertEqual(maintalk.toggleTalkPage(), mainpage)
        self.assertType(mainpage.isDisambig(), bool)
        self.assertType(mainpage.canBeEdited(), bool)
        self.assertType(mainpage.botMayEdit(), bool)
        self.assertType(mainpage.editTime(), pywikibot.Timestamp)
        self.assertType(mainpage.previousRevision(), int)
        self.assertType(mainpage.permalink(), basestring)

    def testReferences(self):
        count = 0
        #Ignore redirects for time considerations
        for p in mainpage.getReferences(follow_redirects=False):
            count += 1
            self.assertType(p, pywikibot.Page)
            if count >= 10:
                break
        count = 0
        for p in mainpage.backlinks(followRedirects=False):
            count += 1
            self.assertType(p, pywikibot.Page)
            if count >= 10:
                break
        count = 0
        for p in mainpage.embeddedin():
            count += 1
            self.assertType(p, pywikibot.Page)
            if count >= 10:
                break

    def testLinks(self):
        for p in mainpage.linkedPages():
            self.assertType(p, pywikibot.Page)
        iw = list(mainpage.interwiki(expand=True))
        for p in iw:
            self.assertType(p, pywikibot.Link)
        for p2 in mainpage.interwiki(expand=False):
            self.assertType(p2, pywikibot.Link)
            self.assertTrue(p2 in iw)
        for p in mainpage.langlinks():
            self.assertType(p, pywikibot.Link)
        for p in mainpage.imagelinks():
            self.assertType(p, pywikibot.ImagePage)
        for p in mainpage.templates():
            self.assertType(p, pywikibot.Page)
        for t, params in mainpage.templatesWithParams():
            self.assertType(t, pywikibot.Page)
            self.assertType(params, list)
        for p in mainpage.categories():
            self.assertType(p, pywikibot.Category)
        for p in mainpage.extlinks():
            self.assertType(p, unicode)

    def testWikibase(self):
        if not site.has_transcluded_data:
            return
        repo = site.data_repository()
        item = pywikibot.ItemPage.fromPage(mainpage)
        self.assertType(item, pywikibot.ItemPage)
        self.assertEqual(item.getID(), 'q5296')
        self.assertEqual(item.title(), 'Q5296')
        self.assertTrue('en' in item.labels)
        self.assertEqual(item.labels['en'], 'Main Page')
        self.assertTrue('en' in item.aliases)
        self.assertTrue('HomePage' in item.aliases['en'])
        self.assertEqual(item.namespace(), 0)
        item2 = pywikibot.ItemPage(repo, 'q5296')
        self.assertEqual(item2.getID(), 'q5296')
        self.assertEqual(item.labels['en'], 'Main Page')
        prop = pywikibot.PropertyPage(repo, 'Property:P21')
        self.assertEqual(prop.getType(), 'wikibase-item')
        self.assertEqual(prop.namespace(), 120)
        claim = pywikibot.Claim(repo, 'p21')
        self.assertRaises(ValueError, claim.setTarget, value="test")
        claim.setTarget(pywikibot.ItemPage(repo, 'q1'))
        self.assertEqual(claim._formatDataValue(), {'entity-type': 'item', 'numeric-id': 1})

        # test WikibasePage.__cmp__
        self.assertEqual(pywikibot.ItemPage.fromPage(mainpage), pywikibot.ItemPage(repo, 'q5296'))

    def testItemPageExtensionability(self):
        class MyItemPage(pywikibot.ItemPage):
            pass
        self.assertIsInstance(MyItemPage.fromPage(mainpage), MyItemPage)

# methods that still need tests implemented or expanded:

##    def autoFormat(self):
##    def isAutoTitle(self):
##    def getOldVersion(self, oldid, force=False, get_redirect=False,
##                      sysop=False):
##    text = property(_textgetter, _textsetter, _cleartext,
##                    "The edited wikitext (unicode) of this Page")
##    def getReferences(self, follow_redirects=True, withTemplateInclusion=True,
##                      onlyTemplateInclusion=False, redirectsOnly=False,
##                      namespaces=None):
##    def backlinks(self, followRedirects=True, filterRedirects=None,
##                  namespaces=None):
##    def embeddedin(self, filter_redirects=None, namespaces=None):
##    def getVersionHistory(self, reverseOrder=False, getAll=False,
##                          revCount=500):
##    def getVersionHistoryTable(self, forceReload=False, reverseOrder=False,
##                               getAll=False, revCount=500):
##    def fullVersionHistory(self):
##    def contributingUsers(self):


if __name__ == '__main__':
    try:
        try:
            unittest.main()
        except SystemExit:
            pass
    finally:
        pywikibot.stopme()
