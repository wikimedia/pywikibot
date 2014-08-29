# -*- coding: utf-8  -*-
"""Tests for the page module."""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


import pywikibot
import pywikibot.page

from tests.utils import PywikibotTestCase, unittest

site = pywikibot.Site('en', 'wikipedia')
mainpage = pywikibot.Page(pywikibot.page.Link("Main Page", site))
maintalk = pywikibot.Page(pywikibot.page.Link("Talk:Main Page", site))
badpage = pywikibot.Page(pywikibot.page.Link("There is no page with this title",
                         site))


class TestLinkObject(PywikibotTestCase):

    """Test cases for Link objects."""

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
                l = pywikibot.page.Link(prefix + self.titles.keys()[0],
                                        self.enwiki)
                self.assertEqual(l.namespace, num)
                # namespace prefixes are case-insensitive
                m = pywikibot.page.Link(prefix.lower() + self.titles.keys()[1],
                                        self.enwiki)
                self.assertEqual(m.namespace, num)

    def testTitles(self):
        """Test that Link() normalizes titles"""
        for title in self.titles:
            for num in (0, 1):
                l = pywikibot.page.Link(self.namespaces[num][0] + title,
                                        self.enwiki)
                self.assertEqual(l.title, self.titles[title])
                # prefixing name with ":" shouldn't change result
                m = pywikibot.page.Link(":" + self.namespaces[num][0] + title,
                                        self.enwiki)
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


class TestPageObject(PywikibotTestCase):

    def testGeneral(self):
        family_name = (site.family.name + ':'
                       if pywikibot.config2.family != site.family.name
                       else u'')
        self.assertEqual(str(mainpage), "[[%s%s:%s]]"
                                        % (family_name, site.code,
                                           mainpage.title()))
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
        self.assertEqual(p1.title(asLink=True, insite=site),
                         u"[[Help:Test page#Testing]]")
        self.assertEqual(p1.title(asLink=True, forceInterwiki=True, insite=site),
                         u"[[en:Help:Test page#Testing]]")
        self.assertEqual(p1.title(asLink=True, textlink=True, insite=site),
                         p1.title(asLink=True, textlink=False, insite=site))
        self.assertEqual(p1.title(asLink=True, withNamespace=False, insite=site),
                         u"[[Help:Test page#Testing|Test page]]")
        self.assertEqual(p1.title(asLink=True, forceInterwiki=True,
                                  withNamespace=False, insite=site),
                         u"[[en:Help:Test page#Testing|Test page]]")
        self.assertEqual(p1.title(asLink=True, textlink=True,
                                  withNamespace=False, insite=site),
                         p1.title(asLink=True, textlink=False,
                                  withNamespace=False, insite=site))
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
        self.assertEqual(p2.title(asLink=True, insite=site),
                         u"[[File:Jean-Léon Gérôme 003.jpg]]")
        self.assertEqual(p2.title(asLink=True, forceInterwiki=True, insite=site),
                         u"[[en:File:Jean-Léon Gérôme 003.jpg]]")
        self.assertEqual(p2.title(asLink=True, textlink=True, insite=site),
                         u"[[:File:Jean-Léon Gérôme 003.jpg]]")
        self.assertEqual(p2.title(as_filename=True),
                         u"File_Jean-Léon_Gérôme_003.jpg")
        self.assertEqual(p2.title(asLink=True, withNamespace=False, insite=site),
                         u"[[File:Jean-Léon Gérôme 003.jpg|Jean-Léon Gérôme 003.jpg]]")
        self.assertEqual(p2.title(asLink=True, forceInterwiki=True,
                                  withNamespace=False, insite=site),
                         u"[[en:File:Jean-Léon Gérôme 003.jpg|Jean-Léon Gérôme 003.jpg]]")
        self.assertEqual(p2.title(asLink=True, textlink=True,
                                  withNamespace=False, insite=site),
                         u"[[:File:Jean-Léon Gérôme 003.jpg|Jean-Léon Gérôme 003.jpg]]")
        # at last test article namespace
        p2 = pywikibot.Page(site, u"Test page")
        self.assertEqual(p2.title(),
                         u"Test page")
        self.assertEqual(p2.title(underscore=True),
                         u"Test_page")
        self.assertEqual(p2.title(),
                         p2.title(withNamespace=False))
        self.assertEqual(p2.title(),
                         p2.title(withSection=False))
        self.assertEqual(p2.title(asUrl=True),
                         p2.title(underscore=True))
        self.assertEqual(p2.title(asLink=True, insite=site),
                         u"[[Test page]]")
        self.assertEqual(p2.title(as_filename=True),
                         p2.title(underscore=True))
        self.assertEqual(p2.title(underscore=True),
                         p2.title(underscore=True, withNamespace=False))
        self.assertEqual(p2.title(underscore=True),
                         p2.title(underscore=True, withSection=False))
        self.assertEqual(p2.title(underscore=True, asUrl=True),
                         p2.title(underscore=True))
        self.assertEqual(p2.title(underscore=True, asLink=True, insite=site),
                         p2.title(asLink=True, insite=site))
        self.assertEqual(p2.title(underscore=True, as_filename=True),
                         p2.title(underscore=True))
        self.assertEqual(p2.title(),
                         p2.title(withNamespace=False, withSection=False))
        self.assertEqual(p2.title(asUrl=True),
                         p2.title(withNamespace=False, asUrl=True))
        self.assertEqual(p2.title(asLink=True, insite=site),
                         p2.title(withNamespace=False, asLink=True, insite=site))
        self.assertEqual(p2.title(as_filename=True),
                         p2.title(withNamespace=False, as_filename=True))
        self.assertEqual(p2.title(withNamespace=False, asLink=True,
                                  forceInterwiki=True, insite=site),
                         u"[[en:Test page|Test page]]")

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
        self.assertIsInstance(mainpage.get(), unicode)
        self.assertIsInstance(maintalk.get(), unicode)
        self.assertRaises(pywikibot.NoPage, badpage.get)
        self.assertIsInstance(mainpage.latestRevision(), int)
        self.assertIsInstance(mainpage.userName(), unicode)
        self.assertIsInstance(mainpage.isIpEdit(), bool)
        self.assertIsInstance(mainpage.exists(), bool)
        self.assertIsInstance(mainpage.isRedirectPage(), bool)
        self.assertIsInstance(mainpage.isEmpty(), bool)
        self.assertEqual(mainpage.toggleTalkPage(), maintalk)
        self.assertEqual(maintalk.toggleTalkPage(), mainpage)
        self.assertIsInstance(mainpage.isDisambig(), bool)
        self.assertIsInstance(mainpage.canBeEdited(), bool)
        self.assertIsInstance(mainpage.botMayEdit(), bool)
        self.assertIsInstance(mainpage.editTime(), pywikibot.Timestamp)
        self.assertIsInstance(mainpage.previousRevision(), int)
        self.assertIsInstance(mainpage.permalink(), basestring)
        self.assertIsInstance(mainpage.purge(), bool)

    def testIsDisambig(self):
        """
        Test the integration with
        Extension:Disambiguator
        """
        if not site.has_extension('Disambiguator'):
            raise unittest.SkipTest('Disambiguator extension not loaded on test site')
        pg = pywikibot.Page(site, 'Random')
        pg._pageprops = set(['disambiguation', ''])
        self.assertTrue(pg.isDisambig())
        pg._pageprops = set()
        self.assertFalse(pg.isDisambig())

    def testReferences(self):
        count = 0
        # Ignore redirects for time considerations
        for p in mainpage.getReferences(follow_redirects=False):
            count += 1
            self.assertIsInstance(p, pywikibot.Page)
            if count >= 10:
                break
        count = 0
        for p in mainpage.backlinks(followRedirects=False):
            count += 1
            self.assertIsInstance(p, pywikibot.Page)
            if count >= 10:
                break
        count = 0
        for p in mainpage.embeddedin():
            count += 1
            self.assertIsInstance(p, pywikibot.Page)
            if count >= 10:
                break

    def testLinks(self):
        for p in mainpage.linkedPages():
            self.assertIsInstance(p, pywikibot.Page)
        iw = list(mainpage.interwiki(expand=True))
        for p in iw:
            self.assertIsInstance(p, pywikibot.Link)
        for p2 in mainpage.interwiki(expand=False):
            self.assertIsInstance(p2, pywikibot.Link)
            self.assertTrue(p2 in iw)
        for p in mainpage.langlinks():
            self.assertIsInstance(p, pywikibot.Link)
        for p in mainpage.imagelinks():
            self.assertIsInstance(p, pywikibot.FilePage)
        for p in mainpage.templates():
            self.assertIsInstance(p, pywikibot.Page)
        for t, params in mainpage.templatesWithParams():
            self.assertIsInstance(t, pywikibot.Page)
            self.assertIsInstance(params, list)
        for p in mainpage.categories():
            self.assertIsInstance(p, pywikibot.Category)
        for p in mainpage.extlinks():
            self.assertIsInstance(p, unicode)

    def testPickleAbility(self):
        import pickle
        pickle.dumps(mainpage)
        self.assertTrue(True)  # No exception thrown!

    def testRepr(self):
        s = repr(mainpage)
        self.assertIsInstance(s, str)

    def testReprUnicode(self):
        site = pywikibot.Site('ar', 'wikipedia')
        page = pywikibot.Page(site, 'Main Page')
        page = page.toggleTalkPage()
        s = repr(page)
        self.assertIsInstance(s, str)

# methods that still need tests implemented or expanded:

#    def autoFormat(self):
#    def isAutoTitle(self):
#    def getOldVersion(self, oldid, force=False, get_redirect=False,
#                      sysop=False):
#    text = property(_textgetter, _textsetter, _cleartext,
#                    "The edited wikitext (unicode) of this Page")
#    def getReferences(self, follow_redirects=True, withTemplateInclusion=True,
#                      onlyTemplateInclusion=False, redirectsOnly=False,
#                      namespaces=None):
#    def backlinks(self, followRedirects=True, filterRedirects=None,
#                  namespaces=None):
#    def embeddedin(self, filter_redirects=None, namespaces=None):
#    def getVersionHistory(self, reverseOrder=False, getAll=False,
#                          revCount=500):
#    def getVersionHistoryTable(self, forceReload=False, reverseOrder=False,
#                               getAll=False, revCount=500):
#    def fullVersionHistory(self):
#    def contributingUsers(self):


class TestCategoryObject(PywikibotTestCase):

    def test_isEmptyCategory(self):
        """Test if category is empty or not"""
        site = pywikibot.Site('en', 'wikipedia')
        cat_empty = pywikibot.Category(site, u'Category:foooooo')
        cat_not_empty = pywikibot.Category(site, u'Category:Wikipedia categories')
        self.assertTrue(cat_empty.isEmptyCategory())
        self.assertFalse(cat_not_empty.isEmptyCategory())


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
