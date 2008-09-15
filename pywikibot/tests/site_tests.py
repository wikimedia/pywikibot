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

    def testBaseMethods(self):
        """Test cases for BaseSite methods"""

        self.assertEqual(mysite.family.name, pywikibot.config.family)
        self.assertEqual(mysite.code, pywikibot.config.mylang)
        self.assertTrue(isinstance(mysite.language(), basestring))
        self.assertTrue(isinstance(mysite == pywikibot.Site("en", "wikipedia"),
                                   bool))
        self.assertTrue(isinstance(mysite.user(), (basestring, type(None))))
        self.assertEqual(mysite.sitename(),
                         "%s:%s" % (pywikibot.config.family, pywikibot.config.mylang))
        self.assertEqual(repr(mysite),
                         'Site("%s", "%s")'
                         % (pywikibot.config.mylang, pywikibot.config.family))
        self.assertTrue(isinstance(mysite.linktrail(), basestring))
        langs = mysite.languages()
        self.assertTrue(isinstance(langs, list))
        self.assertTrue(mysite.code in langs)
        obs = mysite.family.obsolete
        ipf = mysite.interwiki_putfirst()
        self.assertTrue(isinstance(ipf, list))
        for item in ipf:
            self.assertTrue(item in langs or item in obs)
        self.assertEqual(mysite.ns_index("Talk"), 1)
        ns = mysite.namespaces()
        self.assertTrue(isinstance(ns, dict))
        for x in xrange(0, 16): # built-in namespaces always present
            self.assertTrue(x in ns)
            self.assertTrue(isinstance(ns[x], list))
        self.assertTrue(isinstance(mysite.ns_normalize("project"), basestring))
        self.assertTrue(isinstance(mysite.redirect(), basestring))
        self.assertTrue(isinstance(mysite.disambcategory(), pywikibot.Category))
        self.assertTrue(isinstance(mysite.redirectRegex().pattern, basestring))
        self.assertTrue(isinstance(mysite.category_on_one_line(), bool))
        for grp in ("user", "autoconfirmed", "bot", "sysop", "nosuchgroup"):
            self.assertTrue(isinstance(mysite.has_group(grp), bool))
        for rgt in ("read", "edit", "move", "delete", "rollback", "block",
                    "nosuchright"):
            self.assertTrue(isinstance(mysite.has_right(rgt), bool))

    def testApiMethods(self):
        """Test generic ApiSite methods"""
        
        self.assertTrue(isinstance(mysite.logged_in(), bool))
        self.assertTrue(isinstance(mysite.getuserinfo(), dict))
        self.assertTrue(isinstance(mysite.is_blocked(), bool))
        self.assertTrue(isinstance(mysite.messages(), bool))
        self.assertTrue(isinstance(mysite.getcurrenttimestamp(), basestring))
        self.assertTrue(isinstance(mysite.siteinfo, dict))
        self.assertTrue(isinstance(mysite.case(), basestring))
        self.assertTrue(isinstance(mysite.namespaces(), dict))
        self.assertTrue(all(isinstance(key, int)
                            for key in mysite.namespaces()))
        self.assertTrue(all(isinstance(val, list)
                            for val in mysite.namespaces().values()))
        self.assertTrue(all(isinstance(name, basestring)
                            for val in mysite.namespaces().values()
                            for name in val))
        self.assertTrue(all(isinstance(mysite.namespace(key), basestring)
                            for key in mysite.namespaces()))
        self.assertTrue(all(isinstance(mysite.namespace(key, True), list)
                            for key in mysite.namespaces()))
        self.assertTrue(all(isinstance(item, basestring)
                            for key in mysite.namespaces()
                            for item in mysite.namespace(key, True)))
        ver = mysite.live_version()
        self.assertTrue(isinstance(ver, tuple))
        self.assertTrue(all(isinstance(ver[i], int) for i in (0, 1)))
        self.assertTrue(isinstance(ver[2], basestring))
        for msg in ("1movedto2", "about", "aboutpage", "aboutsite",
                    "accesskey-n-portal"):
            self.assertTrue(mysite.has_mediawiki_message(msg))
            self.assertTrue(isinstance(mysite.mediawiki_message(msg),
                                       basestring))
        self.assertFalse(mysite.has_mediawiki_message("nosuchmessage"))
        self.assertRaises(KeyError, mysite.mediawiki_message, "nosuchmessage")

    def testPageMethods(self):
        """Test ApiSite methods for getting page-specific info"""
        
        self.assertTrue(isinstance(mysite.page_exists(mainpage), bool))
        self.assertTrue(isinstance(mysite.page_restrictions(mainpage), dict))
        self.assertTrue(isinstance(mysite.page_can_be_edited(mainpage), bool))
        self.assertTrue(isinstance(mysite.page_isredirect(mainpage), bool))
        if mysite.page_isredirect(mainpage):
            self.assertTrue(isinstance(mysite.getredirtarget(mainpage),
                                       pywikibot.Page))
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
            self.assertTrue(isinstance(mysite.token(mainpage, ttype),
                                       basestring))

    def testLinkMethods(self):
        """Test site methods for getting links to and from a page"""
        
        backlinks = set(mysite.pagebacklinks(mainpage, namespaces=[0]))
        embedded = set(mysite.page_embeddedin(mainpage, namespaces=[0]))
        refs = set(mysite.pagereferences(mainpage, namespaces=[0]))
        for bl in backlinks:
            self.assertTrue(isinstance(bl, pywikibot.Page))
            self.assertTrue(bl in refs)
        for ei in embedded:
            self.assertTrue(isinstance(ei, pywikibot.Page))
            self.assertTrue(ei in refs)
        for ref in refs:
            self.assertTrue(ref in backlinks or ref in embedded)
        for pl in mysite.pagelinks(mainpage):
            self.assertTrue(isinstance(pl, pywikibot.Page))
        for cat in mysite.pagecategories(mainpage):
            self.assertTrue(isinstance(cat, pywikibot.Category))
            for cm in mysite.categorymembers(cat):
                self.assertTrue(isinstance(cat, pywikibot.Page))
        self.assertTrue(all(isinstance(im, pywikibot.ImagePage)
                            for im in mysite.pageimages(mainpage)))
        self.assertTrue(all(isinstance(te, pywikibot.Page)
                            for te in mysite.pagetemplates(mainpage)))
        for ll in mysite.pagelanglinks(mainpage):
            self.assertTrue(isinstance(ll, pywikibot.Link))
        self.assertTrue(all(isinstance(el, basestring)
                            for el in mysite.page_extlinks(mainpage)))

    def testLoadRevisions(self):
        """Test the site.loadrevisions() method"""
        
        mysite.loadrevisions(mainpage)
        self.assertTrue(hasattr(mainpage, "_revid"))
        self.assertTrue(hasattr(mainpage, "_revisions"))
        self.assertTrue(mainpage._revisions.has_key(mainpage._revid))

    def testAllPages(self):
        """Test the site.allpages() method"""
        
        ap = list(mysite.allpages(limit=10))
        self.assertTrue(len(ap) <= 10)
        for page in ap:
            self.assertTrue(isinstance(page, pywikibot.Page))
            self.assertTrue(mysite.page_exists(page))
        # TODO: test various optional arguments to allpages

    def testAllLinks(self):
        """Test the site.alllinks() method"""
        
        al = list(mysite.alllinks(limit=10))
        self.assertTrue(len(al) <= 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page) for link in al))
        # TODO: test various optional arguments to alllinks

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
            self.assertTrue(isinstance(user, dict))
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
        self.assertTrue(isinstance(us[0], dict))

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
