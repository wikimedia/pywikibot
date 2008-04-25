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

site = pywikibot.Site("en", "wikipedia")


class TestLinkObject(unittest.TestCase):
    """Test cases for Link objects"""
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
                                        site)
                self.assertEqual(l.namespace, num)
                # namespace prefixes are case-insensitive
                m = pywikibot.page.Link(prefix.lower()+self.titles.keys()[1],
                                        site)
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
    def testSite(self):
        """Test site() method"""
        p1 = pywikibot.Page(site, u"Help:Test page#Testing")
        self.assertEqual(p1.site(), site)

    def testNamespace(self):
        """Test namespace() method"""
        # TODO

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

    # testIsImage -- todo
    
    def testApiMethods(self):
        """Test various methods that rely on API."""
        # since there is no way to predict what data the wiki will return,
        # we only check that the returned objects are of correct type.
        main = pywikibot.Page(site, u"Main Page")
        self.assertEqual(type(main.get()), unicode)
        self.assertEqual(type(main.latestRevision()), int)
        self.assertEqual(type(main.userName()), unicode)
        self.assertEqual(type(main.isIpEdit()), bool)
        self.assertEqual(type(main.exists()), bool)
        self.assertEqual(type(main.isRedirectPage()), bool)
        self.assertEqual(type(main.isEmpty()), bool)
        self.assertEqual(type(main.toggleTalkPage()), type(main))
        self.assertEqual(type(main.isDisambig()), bool)
        self.assertEqual(type(main.canBeEdited()), bool)
        self.assertEqual(type(main.botMayEdit()), bool)
        for p in main.getReferences():
            self.assertEqual(type(p), type(main))
        for p in main.backlinks():
            self.assertEqual(type(p), type(main))
        for p in main.embeddedin():
            self.assertEqual(type(p), type(main))
        for p in main.linkedPages():
            self.assertEqual(type(p), type(main))
        for p in main.interwiki():
            self.assertEqual(type(p), pywikibot.page.Link)
        for p in main.langlinks():
            self.assertEqual(type(p), pywikibot.page.Link)
        for p in main.imagelinks():
            self.assertEqual(type(p), pywikibot.page.ImagePage)
        for p in main.templates():
            self.assertEqual(type(p), type(main))
        # todo - templatesWithParameters
        for p in main.categories():
            self.assertEqual(type(p), pywikibot.page.Category)
        for p in main.extlinks():
            self.assertEqual(type(p), unicode)
        # more to come

if __name__ == '__main__':
    try:
        try:
            unittest.main()
        except SystemExit:
            pass
    finally:
        pywikibot.stopme()
