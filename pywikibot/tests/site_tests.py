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
        self.assertTrue(isinstance(mysite.user(), (basestring, type(None))))
        self.assertEqual(mysite.sitename(),
                         "%s:%s" % (pywikibot.config.family, pywikibot.config.mylang))
        self.assertTrue(isinstance(mysite.ns_normalize("project"), basestring))
        self.assertTrue(isinstance(mysite.redirect(), basestring))

    def testApiMethods(self):
        """Test generic ApiSite methods"""
        
        self.assertTrue(isinstance(mysite.logged_in(), bool))
        self.assertTrue(isinstance(mysite.getuserinfo(), dict))
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
        
        backlinks = set(mysite.pagebacklinks(mainpage))
        embedded = set(mysite.page_embeddedin(mainpage))
        refs = set(mysite.pagereferences(mainpage))
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


if __name__ == '__main__':
#    pywikibot.logging.getLogger().setLevel(pywikibot.logging.DEBUG)
    try:
        try:
            unittest.main()
        except SystemExit:
            pass
    finally:
        pywikibot.stopme()
