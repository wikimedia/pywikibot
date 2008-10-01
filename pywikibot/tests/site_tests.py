# -*- coding: utf-8  -*-
"""
Tests for the site module.
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'


import unittest
import pywikibot

mysite = pywikibot.Site()
mainpage = pywikibot.Page(pywikibot.Link("Main Page", mysite))


class TestSiteObject(unittest.TestCase):
    """Test cases for Site methods."""

    def assertType(self, obj, cls):
        """Assert that obj is an instance of type cls"""
        return self.assertTrue(isinstance(obj, cls))

    def testBaseMethods(self):
        """Test cases for BaseSite methods"""

        self.assertEqual(mysite.family.name, pywikibot.config.family)
        self.assertEqual(mysite.code, pywikibot.config.mylang)
        self.assertType(mysite.lang, basestring)
        self.assertType(mysite == pywikibot.Site("en", "wikipedia"), bool)
        self.assertType(mysite.user(), (basestring, type(None)))
        self.assertEqual(mysite.sitename(),
                         "%s:%s" % (pywikibot.config.family,
                                    pywikibot.config.mylang))
        self.assertEqual(repr(mysite),
                         'Site("%s", "%s")'
                         % (pywikibot.config.mylang, pywikibot.config.family))
        self.assertType(mysite.linktrail(), basestring)
        self.assertType(mysite.redirect(default=True), basestring)
        self.assertType(mysite.disambcategory(), pywikibot.Category)
        self.assertEqual(mysite.linkto("foo"), u"[[Foo]]")
        self.assertFalse(mysite.isInterwikiLink("foo"))
        self.assertType(mysite.redirectRegex().pattern, basestring)
        self.assertType(mysite.category_on_one_line(), bool)
        for grp in ("user", "autoconfirmed", "bot", "sysop", "nosuchgroup"):
            self.assertType(mysite.has_group(grp), bool)
        for rgt in ("read", "edit", "move", "delete", "rollback", "block",
                    "nosuchright"):
            self.assertType(mysite.has_right(rgt), bool)

    def testLanguageMethods(self):
        """Test cases for languages() and related methods"""
        
        langs = mysite.languages()
        self.assertType(langs, list)
        self.assertTrue(mysite.code in langs)
        obs = mysite.family.obsolete
        ipf = mysite.interwiki_putfirst()
        self.assertType(ipf, list)
        self.assertTrue(all(item in langs or item in obs
                            for item in ipf))
        self.assertTrue(all(item in langs
                            for item in mysite.validLanguageLinks()))

    def testNamespaceMethods(self):
        """Test cases for methods manipulating namespace names"""

        builtins = {'Talk': 1, # these should work in any MW wiki
                    'User': 2,
                    'User talk': 3,
                    'Project': 4,
                    'Project talk': 5,
                    'Image': 6,
                    'Image talk': 7,
                    'MediaWiki': 8,
                    'MediaWiki talk': 9,
                    'Template': 10,
                    'Template talk': 11,
                    'Help': 12,
                    'Help talk': 13,
                    'Category': 14,
                    'Category talk': 15,
        }
        self.assertTrue(all(mysite.ns_index(b) == builtins[b]
                            for b in builtins))
        ns = mysite.namespaces()
        self.assertType(ns, dict)
        self.assertTrue(all(x in ns for x in xrange(0, 16)))
            # built-in namespaces always present
        self.assertType(mysite.ns_normalize("project"), basestring)
        self.assertTrue(all(isinstance(key, int)
                            for key in ns))
        self.assertTrue(all(isinstance(val, list)
                            for val in ns.values()))
        self.assertTrue(all(isinstance(name, basestring)
                            for val in ns.values()
                            for name in val))
        self.assertTrue(all(isinstance(mysite.namespace(key), basestring)
                            for key in ns))
        self.assertTrue(all(isinstance(mysite.namespace(key, True), list)
                            for key in ns))
        self.assertTrue(all(isinstance(item, basestring)
                            for key in ns
                            for item in mysite.namespace(key, True)))

    def testApiMethods(self):
        """Test generic ApiSite methods"""
        
        self.assertType(mysite.logged_in(), bool)
        self.assertType(mysite.logged_in(True), bool)
        self.assertType(mysite.userinfo, dict)
        self.assertType(mysite.is_blocked(), bool)
        self.assertType(mysite.is_blocked(True), bool)
        self.assertType(mysite.messages(), bool)
        self.assertType(mysite.has_right("edit"), bool)
        self.assertFalse(mysite.has_right("nonexistent_right"))
        self.assertType(mysite.has_right("edit", True), bool)
        self.assertFalse(mysite.has_right("nonexistent_right", True))
        self.assertType(mysite.has_group("bots"), bool)
        self.assertFalse(mysite.has_group("nonexistent_group"))
        self.assertType(mysite.has_group("bots", True), bool)
        self.assertFalse(mysite.has_group("nonexistent_group", True))
        for msg in ("1movedto2", "about", "aboutpage", "aboutsite",
                    "accesskey-n-portal"):
            self.assertTrue(mysite.has_mediawiki_message(msg))
            self.assertType(mysite.mediawiki_message(msg), basestring)
        self.assertFalse(mysite.has_mediawiki_message("nosuchmessage"))
        self.assertRaises(KeyError, mysite.mediawiki_message, "nosuchmessage")
        self.assertType(mysite.getcurrenttimestamp(), basestring)
        self.assertType(mysite.siteinfo, dict)
        self.assertType(mysite.case(), basestring)
        ver = mysite.live_version()
        self.assertType(ver, tuple)
        self.assertTrue(all(isinstance(ver[i], int) for i in (0, 1)))
        self.assertType(ver[2], basestring)

    def testPageMethods(self):
        """Test ApiSite methods for getting page-specific info"""
        
        self.assertType(mysite.page_exists(mainpage), bool)
        self.assertType(mysite.page_restrictions(mainpage), dict)
        self.assertType(mysite.page_can_be_edited(mainpage), bool)
        self.assertType(mysite.page_isredirect(mainpage), bool)
        if mysite.page_isredirect(mainpage):
            self.assertType(mysite.getredirtarget(mainpage), pywikibot.Page)
        else:
            self.assertRaises(pywikibot.IsNotRedirectPage,
                              mysite.getredirtarget, mainpage)
        a = list(mysite.preloadpages([mainpage]))
        self.assertEqual(len(a), int(mysite.page_exists(mainpage)))
        if a:
            self.assertEqual(a[0], mainpage)

    def testTokens(self):
        """Test ability to get page tokens"""
        
        for ttype in ("edit", "move"): # token types for non-sysops
            self.assertType(mysite.token(mainpage, ttype), basestring)
        self.assertRaises(KeyError, mysite.token, mainpage, "invalidtype")

    def testPreload(self):
        """Test that preloading works"""

        count = 0
        for page in mysite.preloadpages(mysite.pagelinks(mainpage, limit=10)):
            self.assertType(page, pywikibot.Page)
            self.assertType(page.exists(), bool)
            if page.exists():
                self.assertTrue(hasattr(page, "_text"))
            count += 1
            if count >= 5:
                break

    def testLinkMethods(self):
        """Test site methods for getting links to and from a page"""
        
        backlinks = set(mysite.pagebacklinks(mainpage, namespaces=[0]))
        embedded = set(mysite.page_embeddedin(mainpage, namespaces=[0]))
        refs = set(mysite.pagereferences(mainpage, namespaces=[0]))
        for bl in backlinks:
            self.assertType(bl, pywikibot.Page)
            self.assertTrue(bl in refs)
        for ei in embedded:
            self.assertType(ei, pywikibot.Page)
            self.assertTrue(ei in refs)
        for ref in refs:
            self.assertTrue(ref in backlinks or ref in embedded)
        # test backlinks arguments
        self.assertTrue(backlinks.issubset(
                    set(mysite.pagebacklinks(mainpage,
                                             followRedirects=True,
                                             namespaces=[0]))))
        self.assertTrue(backlinks.issuperset(
                    set(mysite.pagebacklinks(mainpage,
                                             filterRedirects=True,
                                             namespaces=[0]))))
        self.assertTrue(backlinks.issuperset(
                    set(mysite.pagebacklinks(mainpage,
                                             filterRedirects=False,
                                             namespaces=[0]))))
        self.assertTrue(backlinks.issubset(
                    set(mysite.pagebacklinks(mainpage, namespaces=[0, 2]))))
        # test embeddedin arguments
        self.assertTrue(embedded.issuperset(
                    set(mysite.page_embeddedin(mainpage, filterRedirects=True,
                                               namespaces=[0]))))
        self.assertTrue(embedded.issuperset(
                    set(mysite.page_embeddedin(mainpage, filterRedirects=False,
                                               namespaces=[0]))))
        self.assertTrue(embedded.issubset(
                    set(mysite.page_embeddedin(mainpage, namespaces=[0, 2]))))
        links = set(mysite.pagelinks(mainpage))
        for pl in links:
            self.assertType(pl, pywikibot.Page)
        # test links arguments
        self.assertTrue(links.issuperset(
                    set(mysite.pagelinks(mainpage, namespaces=[0, 1]))))
        for target in mysite.preloadpages(
                            mysite.pagelinks(mainpage, follow_redirects=True,
                                             limit=10)):
            self.assertType(target, pywikibot.Page)
            self.assertFalse(target.isRedirectPage())
        # test pagecategories
        for cat in mysite.pagecategories(mainpage):
            self.assertType(cat, pywikibot.Category)
            for cm in mysite.categorymembers(cat):
                self.assertType(cat, pywikibot.Page)
        # test pageimages
        self.assertTrue(all(isinstance(im, pywikibot.ImagePage)
                            for im in mysite.pageimages(mainpage)))
        # test pagetemplates
        self.assertTrue(all(isinstance(te, pywikibot.Page)
                            for te in mysite.pagetemplates(mainpage)))
        self.assertTrue(set(mysite.pagetemplates(mainpage)).issuperset(
                        set(mysite.pagetemplates(mainpage, namespaces=[10]))))
        # test pagelanglinks
        for ll in mysite.pagelanglinks(mainpage):
            self.assertType(ll, pywikibot.Link)
        # test page_extlinks
        self.assertTrue(all(isinstance(el, basestring)
                            for el in mysite.page_extlinks(mainpage)))

    def testLoadRevisions(self):
        """Test the site.loadrevisions() method"""
        
        mysite.loadrevisions(mainpage)
        self.assertTrue(hasattr(mainpage, "_revid"))
        self.assertTrue(hasattr(mainpage, "_revisions"))
        self.assertTrue(mainpage._revisions.has_key(mainpage._revid))
        # TODO test all the optional arguments

    def testAllPages(self):
        """Test the site.allpages() method"""

        fwd = list(mysite.allpages(limit=10))
        self.assertTrue(len(fwd) <= 10)
        for page in fwd:
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
        rev = list(mysite.allpages(reverse=True, start="Aa", limit=12))
        self.assertTrue(len(rev) <= 12)
        for page in rev:
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title() <= "Aa")
        for page in mysite.allpages(start="Py", limit=10):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title() >= "Py")
        for page in mysite.allpages(prefix="Pre", limit=10):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title().startswith("Pre"))
        for page in mysite.allpages(namespace=1, limit=10):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 1)
        for page in mysite.allpages(filterredir=True, limit=10):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.isRedirectPage())
        for page in mysite.allpages(filterredir=False, limit=10):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertFalse(page.isRedirectPage())
        for page in mysite.allpages(filterlanglinks=True, limit=10):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
        for page in mysite.allpages(filterlanglinks=False, limit=10):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
        for page in mysite.allpages(minsize=100, limit=10):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertTrue(len(page.text) >= 100)
        for page in mysite.allpages(maxsize=200, limit=10):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertTrue(len(page.text) <= 200)
        for page in mysite.allpages(protect_type="edit", limit=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertTrue("edit" in page._protection)
        for page in mysite.allpages(protect_type="edit",
                                    protect_level="sysop", limit=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertTrue("edit" in page._protection)
            self.assertTrue("sysop" in page._protection["edit"])

    def testAllLinks(self):
        """Test the site.alllinks() method"""
        
        fwd = list(mysite.alllinks(limit=10))
        self.assertTrue(len(fwd) <= 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page) for link in fwd))
        uniq = list(mysite.alllinks(limit=10, unique=True))
        self.assertTrue(all(link in uniq for link in fwd))
        # TODO: test various optional arguments to alllinks
        for page in mysite.alllinks(start="Link", limit=10):
            self.assertType(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title() >= "Link")
        for page in mysite.alllinks(prefix="Fix", limit=10):
            self.assertType(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title().startswith("Fix"))
        for page in mysite.alllinks(namespace=1, limit=10):
            self.assertType(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 1)
        for page in mysite.alllinks(start="From", namespace=4, fromids=True,
                                    limit=10):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(page.title(withNamespace=False) >= "From")
            self.assertTrue(hasattr(page, "_fromid"))

    def testAllCategories(self):
        """Test the site.allcategories() method"""
        
        ac = list(mysite.allcategories(limit=10))
        self.assertTrue(len(ac) <= 10)
        self.assertTrue(all(isinstance(cat, pywikibot.Category)
                            for cat in ac))
        # TODO: test various optional arguments to allcategories

    def testAllUsers(self):
        """Test the site.allusers() method"""
        
        au = list(mysite.allusers(limit=10))
        self.assertTrue(len(au) <= 10)
        for user in au:
            self.assertType(user, dict)
            self.assertTrue(user.has_key("name"))
            self.assertTrue(user.has_key("editcount"))
            self.assertTrue(user.has_key("registration"))

    def testAllImages(self):
        """Test the site.allimages() method"""

        ai = list(mysite.allimages(limit=10))
        self.assertTrue(len(ai) <= 10)
        self.assertTrue(all(isinstance(image, pywikibot.ImagePage)
                            for image in ai))

    def testBlocks(self):
        """Test the site.blocks() method"""

        bl = list(mysite.blocks(limit=10))
        self.assertTrue(len(bl) <= 10)
        self.assertTrue(all(isinstance(block, dict)
                            for block in bl))

    def testExturlusage(self):
        """Test the site.exturlusage() method"""

        url = "www.google.com"
        eu = list(mysite.exturlusage(url, limit=10))
        self.assertTrue(len(eu) <= 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page)
                            for link in eu))

    def testImageusage(self):
        """Test the site.imageusage() method"""

        imagepage = pywikibot.ImagePage(pywikibot.Link("Image:Wiki.png", mysite))
        iu = list(mysite.imageusage(imagepage, limit=10))
        self.assertTrue(len(iu) <= 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page)
                            for link in iu))

    def testLogEvents(self):
        """Test the site.logevents() method"""

        le = list(mysite.logevents(limit=10))
        self.assertTrue(len(le) <= 10)
        self.assertTrue(all(isinstance(entry, dict) and entry.has_key("type")
                            for entry in le))

    def testRecentchanges(self):
        """Test the site.recentchanges() method"""

        rc = list(mysite.recentchanges(limit=10))
        self.assertTrue(len(rc) <= 10)
        self.assertTrue(all(isinstance(change, dict)
                            for change in rc))

    def testSearch(self):
        """Test the site.search() method"""

        se = list(mysite.search("wiki", limit=10))
        self.assertTrue(len(se) <= 10)
        self.assertTrue(all(isinstance(hit, pywikibot.Page)
                            for hit in se))

    def testUsercontribs(self):
        """Test the site.usercontribs() method"""

        uc = list(mysite.usercontribs(user=mysite.user(), limit=10))
        self.assertTrue(len(uc) <= 10)
        self.assertTrue(all(isinstance(contrib, dict)
                            for contrib in uc))

    def testWatchlistrevs(self):
        """Test the site.watchlist_revs() method"""

        wl = list(mysite.watchlist_revs(limit=10))
        self.assertTrue(len(wl) <= 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in wl))

    def testDeletedrevs(self):
        """Test the site.deletedrevs() method"""

        if not mysite.logged_in(True):
            return
        dr = list(mysite.deletedrevs(limit=10))
        self.assertTrue(len(dr) <= 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in dr))
        dr2 = list(mysite.deletedrevs(titles=mainpage.title(withSection=False),
                                     limit=10))
        self.assertTrue(len(dr2) <= 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in dr2))

    def testUsers(self):
        """Test the site.users() method"""

        us = list(mysite.users([mysite.user()]))
        self.assertEqual(len(us), 1)
        self.assertType(us[0], dict)

    def testRandompages(self):
        """Test the site.randompages() method"""
        rn = list(mysite.randompages(limit=10))
        self.assertTrue(len(rn) <= 10)
        self.assertTrue(all(isinstance(a_page, pywikibot.Page)
                            for a_page in rn))


if __name__ == '__main__':
#    pywikibot.logging.getLogger().setLevel(pywikibot.logging.DEBUG)
    try:
        try:
            unittest.main()
        except SystemExit:
            pass
    finally:
        pywikibot.stopme()
