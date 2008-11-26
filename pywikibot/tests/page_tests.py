# -*- coding: utf-8  -*-
"""
Tests for the page module.
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'


import unittest
import pywikibot
import pywikibot.page

site = pywikibot.Site()
mainpage = pywikibot.Page(pywikibot.page.Link("Main Page", site))
maintalk = pywikibot.Page(pywikibot.page.Link("Talk:Main Page", site))
badpage = pywikibot.Page(pywikibot.page.Link("There is no page with this title",
                                        site))

class TestLinkObject(unittest.TestCase):
    """Test cases for Link objects"""

    enwiki = pywikibot.Site("en", "wikipedia")
    namespaces = {0: [u""],        # en.wikipedia.org namespaces for testing
                  1: [u"Talk:"],   # canonical form first, then others
                  2: [u"User:"],   # must end with :
                  3: [u"User talk:", u"User_talk:"],
                  4: [u"Wikipedia:", u"Project:", u"WP:"],
                  5: [u"Wikipedia talk:", u"Project talk:", u"Wikipedia_talk:",
                      u"Project_talk:", u"WT:"],
                  6: [u"Image:"],
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
        u"Cities in Burkina Faso"       : u"Cities in Burkina Faso",
        u"eastern Sayan"                : u"Eastern Sayan",
        u"The_Addams_Family_(pinball)"  : u"The Addams Family (pinball)",
        u"Hispanic  (U.S.  Census)"     : u"Hispanic (U.S. Census)",
        u"Stołpce"                      : u"Stołpce",
        u"Nowy_Sącz"                    : u"Nowy Sącz",
        u"battle of Węgierska  Górka"   : u"Battle of Węgierska Górka",
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
                m = pywikibot.page.Link(":"+self.namespaces[num][0]+title)
                self.assertEqual(m.title, self.titles[title])


class TestPageObject(unittest.TestCase):
    def testGeneral(self):
        self.assertEqual(str(mainpage), "[[%s:%s]]"
                                        % (site.lang, mainpage.title()))
        self.assertTrue(mainpage < maintalk)

    def testSite(self):
        """Test site() method"""
        self.assertEqual(mainpage.site(), site)
        self.assertEqual(mainpage.encoding(), site.encoding())

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
        p2 = pywikibot.Page(site, u"Image:Jean-Léon Gérôme 003.jpg")
        self.assertEqual(p2.title(),
                         u"Image:Jean-Léon Gérôme 003.jpg")
        self.assertEqual(p2.title(underscore=True),
                         u"Image:Jean-Léon_Gérôme_003.jpg")
        self.assertEqual(p2.title(withNamespace=False),
                         u"Jean-Léon Gérôme 003.jpg")
        self.assertEqual(p2.title(withSection=False),
                         u"Image:Jean-Léon Gérôme 003.jpg")
        self.assertEqual(p2.title(withNamespace=False, withSection=False),
                         u"Jean-Léon Gérôme 003.jpg")
        self.assertEqual(p2.title(asUrl=True),
                         u"Image%3AJean-L%C3%A9on_G%C3%A9r%C3%B4me_003.jpg")
        self.assertEqual(p2.title(asLink=True),
                         u"[[Image:Jean-Léon Gérôme 003.jpg]]")
        self.assertEqual(p2.title(asLink=True, forceInterwiki=True),
                         u"[[en:Image:Jean-Léon Gérôme 003.jpg]]")
        self.assertEqual(p2.title(asLink=True, textlink=True),
                         u"[[:Image:Jean-Léon Gérôme 003.jpg]]")
        self.assertEqual(p2.title(as_filename=True),
                         u"Image_Jean-Léon_Gérôme_003.jpg")

    def testSection(self):
        """Test section() method."""
        # use same pages as in previous test
        p1 = pywikibot.Page(site, u"Help:Test page#Testing")
        p2 = pywikibot.Page(site, u"Image:Jean-Léon Gérôme 003.jpg")
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
        p2 = pywikibot.Page(site, u"Image:Second page")
        p3 = pywikibot.Page(site, u"Image talk:Second page")
        self.assertEqual(p1.isImage(), False)
        self.assertEqual(p2.isImage(), True)
        self.assertEqual(p3.isImage(), False)
    
    def testApiMethods(self):
        """Test various methods that rely on API."""
        # since there is no way to predict what data the wiki will return,
        # we only check that the returned objects are of correct type.
        self.assertTrue(isinstance(mainpage.get(), unicode))
        self.assertTrue(isinstance(maintalk.get(), unicode))
        self.assertRaises(pywikibot.NoPage, badpage.get)
        self.assertTrue(isinstance(mainpage.latestRevision(), int))
        self.assertTrue(isinstance(mainpage.userName(), unicode))
        self.assertTrue(isinstance(mainpage.isIpEdit(), bool))
        self.assertTrue(isinstance(mainpage.exists(), bool))
        self.assertTrue(isinstance(mainpage.isRedirectPage(), bool))
        self.assertTrue(isinstance(mainpage.isEmpty(), bool))
        self.assertEqual(mainpage.toggleTalkPage(), maintalk)
        self.assertEqual(maintalk.toggleTalkPage(), mainpage)
        self.assertTrue(isinstance(mainpage.isDisambig(), bool))
        self.assertTrue(isinstance(mainpage.canBeEdited(), bool))
        self.assertTrue(isinstance(mainpage.botMayEdit(), bool))
        self.assertTrue(isinstance(mainpage.editTime(), unicode))
        self.assertTrue(isinstance(mainpage.previousRevision(), int))
        self.assertTrue(isinstance(mainpage.permalink(), basestring))

    def testReferences(self):
        pywikibot.set_debug("comm")
        count = 0
        for p in mainpage.getReferences():
            count += 1
            self.assertTrue(isinstance(p, pywikibot.Page))
            if count >= 10:
                break
        count = 0
        for p in mainpage.backlinks():
            count += 1
            self.assertTrue(isinstance(p, pywikibot.Page))
            if count >= 10:
                break
        count = 0
        for p in mainpage.embeddedin():
            count += 1
            self.assertTrue(isinstance(p, pywikibot.Page))
            if count >= 10:
                break

    def testLinks(self):
        for p in mainpage.linkedPages():
            self.assertTrue(isinstance(p, pywikibot.Page))
## Not implemented:
##        for p in mainpage.interwiki():
##            self.assertTrue(isinstance(p, pywikibot.Link))
        for p in mainpage.langlinks():
            self.assertTrue(isinstance(p, pywikibot.Link))
        for p in mainpage.imagelinks():
            self.assertTrue(isinstance(p, pywikibot.ImagePage))
        for p in mainpage.templates():
            self.assertTrue(isinstance(p, pywikibot.Page))
        for t, params in mainpage.templatesWithParams():
            self.assertTrue(isinstance(t, pywikibot.Page))
            self.assertTrue(isinstance(params, list))
        for p in mainpage.categories():
            self.assertTrue(isinstance(p, pywikibot.Category))
        for p in mainpage.extlinks():
            self.assertTrue(isinstance(p, unicode))

# methods that still need tests implemented or expanded:

##    def autoFormat(self):
##    def isAutoTitle(self):
##    def get(self, force=False, get_redirect=False, sysop=False):
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
##    def getRedirectTarget(self):
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
