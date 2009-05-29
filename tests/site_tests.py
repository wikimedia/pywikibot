# -*- coding: utf-8  -*-
"""
Tests for the site module.
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


import unittest
import pywikibot
import warnings

logger = pywikibot.logging.getLogger("wiki.site.tests")

mysite = pywikibot.Site()
mainpage = pywikibot.Page(pywikibot.Link("Main Page", mysite))
imagepage = iter(mainpage.imagelinks()).next() # 1st image on main page


class TestSiteObject(unittest.TestCase):
    """Test cases for Site methods."""

    def assertType(self, obj, cls):
        """Assert that obj is an instance of type cls"""
        return self.assertTrue(isinstance(obj, cls))

    def testBaseMethods(self):
        """Test cases for BaseSite methods"""

        self.assertEqual(mysite.family.name, pywikibot.config2.family)
        self.assertEqual(mysite.code, pywikibot.config2.mylang)
        self.assertType(mysite.lang, basestring)
        self.assertType(mysite == pywikibot.Site("en", "wikipedia"), bool)
        self.assertType(mysite.user(), (basestring, type(None)))
        self.assertEqual(mysite.sitename(),
                         "%s:%s" % (pywikibot.config2.family,
                                    pywikibot.config2.mylang))
        self.assertEqual(repr(mysite),
                         'Site("%s", "%s")'
                         % (pywikibot.config2.mylang, pywikibot.config2.family))
        self.assertType(mysite.linktrail(), basestring)
        self.assertType(mysite.redirect(default=True), basestring)
        self.assertType(mysite.disambcategory(), pywikibot.Category)
        self.assertEqual(mysite.linkto("foo"), u"[[Foo]]") # deprecated
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
                            for val in ns.itervalues()))
        self.assertTrue(all(isinstance(name, basestring)
                            for val in ns.itervalues()
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
        self.assertType(mysite.messages(), bool)
        self.assertType(mysite.has_right("edit"), bool)
        self.assertFalse(mysite.has_right("nonexistent_right"))
        self.assertType(mysite.has_group("bots"), bool)
        self.assertFalse(mysite.has_group("nonexistent_group"))
        try:
            self.assertType(mysite.is_blocked(True), bool)
            self.assertType(mysite.has_right("edit", True), bool)
            self.assertFalse(mysite.has_right("nonexistent_right", True))
            self.assertType(mysite.has_group("bots", True), bool)
            self.assertFalse(mysite.has_group("nonexistent_group", True))
        except pywikibot.NoUsername:
            logger.warn(
             "Cannot test Site methods for sysop; no sysop account configured.")
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
        for page in mysite.preloadpages(mysite.pagelinks(mainpage, total=10)):
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
        # only non-redirects:
        filtered = set(mysite.pagebacklinks(mainpage, namespaces=0,
                                            filterRedirects=False))
        # only redirects:
        redirs = set(mysite.pagebacklinks(mainpage, namespaces=0,
                                          filterRedirects=True))
        # including links to redirect pages (but not the redirects):
        indirect = set(mysite.pagebacklinks(mainpage, namespaces=[0],
                                            followRedirects=True))
        self.assertEqual(filtered & redirs, set([]))
        self.assertEqual(indirect & redirs, set([]))
        self.assertTrue(filtered.issubset(indirect))
        self.assertTrue(filtered.issubset(backlinks))
        self.assertTrue(redirs.issubset(backlinks))
        self.assertTrue(backlinks.issubset(
                        set(mysite.pagebacklinks(mainpage, namespaces=[0, 2]))))

        # pagereferences includes both backlinks and embeddedin
        embedded = set(mysite.page_embeddedin(mainpage, namespaces=[0]))
        refs = set(mysite.pagereferences(mainpage, namespaces=[0]))
        self.assertTrue(backlinks.issubset(refs))
        self.assertTrue(embedded.issubset(refs))
        for bl in backlinks:
            self.assertType(bl, pywikibot.Page)
            self.assertTrue(bl in refs)
        for ei in embedded:
            self.assertType(ei, pywikibot.Page)
            self.assertTrue(ei in refs)
        for ref in refs:
            self.assertTrue(ref in backlinks or ref in embedded)
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
                                             total=5)):
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
        self.assertTrue(mainpage._revid in mainpage._revisions)
        # TODO test all the optional arguments

    def testAllPages(self):
        """Test the site.allpages() method"""

        fwd = list(mysite.allpages(total=10))
        self.assertTrue(len(fwd) <= 10)
        for page in fwd:
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
        rev = list(mysite.allpages(reverse=True, start="Aa", total=12))
        self.assertTrue(len(rev) <= 12)
        for page in rev:
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title() <= "Aa")
        for page in mysite.allpages(start="Py", total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title() >= "Py")
        for page in mysite.allpages(prefix="Pre", total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title().startswith("Pre"))
        for page in mysite.allpages(namespace=1, total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 1)
        for page in mysite.allpages(filterredir=True, total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.isRedirectPage())
        for page in mysite.allpages(filterredir=False, total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertFalse(page.isRedirectPage())
##        for page in mysite.allpages(filterlanglinks=True, total=5):
##            self.assertType(page, pywikibot.Page)
##            self.assertTrue(mysite.page_exists(page))
##            self.assertEqual(page.namespace(), 0)
##        for page in mysite.allpages(filterlanglinks=False, total=5):
##            self.assertType(page, pywikibot.Page)
##            self.assertTrue(mysite.page_exists(page))
##            self.assertEqual(page.namespace(), 0)
        for page in mysite.allpages(minsize=100, total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertTrue(len(page.text) >= 100)
        for page in mysite.allpages(maxsize=200, total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertTrue(len(page.text) <= 200)
        for page in mysite.allpages(protect_type="edit", total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertTrue("edit" in page._protection)
        for page in mysite.allpages(protect_type="edit",
                                    protect_level="sysop", total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertTrue("edit" in page._protection)
            self.assertTrue("sysop" in page._protection["edit"])

    def testAllLinks(self):
        """Test the site.alllinks() method"""
        
        fwd = list(mysite.alllinks(total=10))
        self.assertTrue(len(fwd) <= 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page) for link in fwd))
        uniq = list(mysite.alllinks(total=10, unique=True))
        self.assertTrue(all(link in uniq for link in fwd))
        for page in mysite.alllinks(start="Link", total=5):
            self.assertType(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title() >= "Link")
        for page in mysite.alllinks(prefix="Fix", total=5):
            self.assertType(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title().startswith("Fix"))
        for page in mysite.alllinks(namespace=1, total=5):
            self.assertType(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 1)
        for page in mysite.alllinks(start="From", namespace=4, fromids=True,
                                    total=5):
            self.assertType(page, pywikibot.Page)
            self.assertTrue(page.title(withNamespace=False) >= "From")
            self.assertTrue(hasattr(page, "_fromid"))
        errgen = mysite.alllinks(unique=True, fromids=True)
        self.assertRaises(pywikibot.Error, errgen.next)

    def testAllCategories(self):
        """Test the site.allcategories() method"""
        
        ac = list(mysite.allcategories(total=10))
        self.assertTrue(len(ac) <= 10)
        self.assertTrue(all(isinstance(cat, pywikibot.Category)
                            for cat in ac))
        for cat in mysite.allcategories(total=5, start="Abc"):
            self.assertType(cat, pywikibot.Category)
            self.assertTrue(cat.title(withNamespace=False) >= "Abc")
        for cat in mysite.allcategories(total=5, prefix="Def"):
            self.assertType(cat, pywikibot.Category)
            self.assertTrue(cat.title(withNamespace=False).startswith("Def"))
##        # Bug # 15985
##        for cat in mysite.allcategories(total=5, start="Hij", reverse=True):
##            self.assertType(cat, pywikibot.Category)
##            self.assertTrue(cat.title(withNamespace=False) <= "Hij")

    def testAllUsers(self):
        """Test the site.allusers() method"""
        
        au = list(mysite.allusers(total=10))
        self.assertTrue(len(au) <= 10)
        for user in au:
            self.assertType(user, dict)
            self.assertTrue("name" in user)
            self.assertTrue("editcount" in user)
            self.assertTrue("registration" in user)
        for user in mysite.allusers(start="B", total=5):
            self.assertType(user, dict)
            self.assertTrue("name" in user)
            self.assertTrue(user["name"] >= "B")
            self.assertTrue("editcount" in user)
            self.assertTrue("registration" in user)
        for user in mysite.allusers(prefix="C", total=5):
            self.assertType(user, dict)
            self.assertTrue("name" in user)
            self.assertTrue(user["name"].startswith("C"))
            self.assertTrue("editcount" in user)
            self.assertTrue("registration" in user)
        for user in mysite.allusers(prefix="D", group="sysop", total=5):
            self.assertType(user, dict)
            self.assertTrue("name" in user)
            self.assertTrue(user["name"].startswith("D"))
            self.assertTrue("editcount" in user)
            self.assertTrue("registration" in user)
            self.assertTrue("groups" in user and "sysop" in user["groups"])

    def testAllImages(self):
        """Test the site.allimages() method"""

        ai = list(mysite.allimages(total=10))
        self.assertTrue(len(ai) <= 10)
        self.assertTrue(all(isinstance(image, pywikibot.ImagePage)
                            for image in ai))
        for impage in mysite.allimages(start="Ba", total=5):
            self.assertType(impage, pywikibot.ImagePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertTrue(impage.title(withNamespace=False) >= "Ba")
##        # Bug # 15985
##        for impage in mysite.allimages(start="Da", reverse=True, total=5):
##            self.assertType(impage, pywikibot.ImagePage)
##            self.assertTrue(mysite.page_exists(impage))
##            self.assertTrue(impage.title() <= "Da")
        for impage in mysite.allimages(prefix="Ch", total=5):
            self.assertType(impage, pywikibot.ImagePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertTrue(impage.title(withNamespace=False).startswith("Ch"))
        for impage in mysite.allimages(minsize=100, total=5):
            self.assertType(impage, pywikibot.ImagePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertTrue(impage._imageinfo["size"] >= 100)
        for impage in mysite.allimages(maxsize=2000, total=5):
            self.assertType(impage, pywikibot.ImagePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertTrue(impage._imageinfo["size"] <= 2000)

    def testBlocks(self):
        """Test the site.blocks() method"""

        props = ("id", "by", "timestamp", "expiry", "reason")
        bl = list(mysite.blocks(total=10))
        self.assertTrue(len(bl) <= 10)
        for block in bl:
            self.assertType(block, dict)
            for prop in props:
                self.assertTrue(prop in block)
        # timestamps should be in descending order
        timestamps = [block['timestamp'] for block in bl]
        for t in xrange(1, len(timestamps)):
            self.assertTrue(timestamps[t] <= timestamps[t-1])

        b2 = list(mysite.blocks(total=10, reverse=True))
        self.assertTrue(len(b2) <= 10)
        for block in b2:
            self.assertType(block, dict)
            for prop in props:
                self.assertTrue(prop in block)
        # timestamps should be in ascending order
        timestamps = [block['timestamp'] for block in b2]
        for t in xrange(1, len(timestamps)):
            self.assertTrue(timestamps[t] >= timestamps[t-1])

        for block in mysite.blocks(starttime="2008-07-01T00:00:01Z", total=5):
            self.assertType(block, dict)
            for prop in props:
                self.assertTrue(prop in block)
        for block in mysite.blocks(endtime="2008-07-31T23:59:59Z", total=5):
            self.assertType(block, dict)
            for prop in props:
                self.assertTrue(prop in block)
        for block in mysite.blocks(starttime="2008-08-02T00:00:01Z",
                                   endtime="2008-08-02T23:59:59Z",
                                   reverse=True, total=5):
            self.assertType(block, dict)
            for prop in props:
                self.assertTrue(prop in block)
        for block in mysite.blocks(starttime="2008-08-03T23:59:59Z",
                                   endtime="2008-08-03T00:00:01Z",
                                   total=5):
            self.assertType(block, dict)
            for prop in props:
                self.assertTrue(prop in block)
        # starttime earlier than endtime
        self.assertRaises(pywikibot.Error, mysite.blocks,
                          starttime="2008-08-03T00:00:01Z",
                          endtime="2008-08-03T23:59:59Z", total=5)
        # reverse: endtime earlier than starttime
        self.assertRaises(pywikibot.Error, mysite.blocks,
                          starttime="2008-08-03T23:59:59Z",
                          endtime="2008-08-03T00:00:01Z", reverse=True, total=5)
        for block in mysite.blocks(users=mysite.user(), total=5):
            self.assertType(block, dict)
            self.assertEqual(block['user'], mysite.user())

    def testExturlusage(self):
        """Test the site.exturlusage() method"""

        url = "www.google.com"
        eu = list(mysite.exturlusage(url, total=10))
        self.assertTrue(len(eu) <= 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page)
                            for link in eu))
        for link in mysite.exturlusage(url, namespaces=[2, 3], total=5):
            self.assertType(link, pywikibot.Page)
            self.assertTrue(link.namespace() in (2, 3))

    def testImageusage(self):
        """Test the site.imageusage() method"""

        iu = list(mysite.imageusage(imagepage, total=10))
        self.assertTrue(len(iu) <= 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page)
                            for link in iu))
        for using in mysite.imageusage(imagepage, namespaces=[3,4], total=5):
            self.assertType(using, pywikibot.Page)
            self.assertTrue(imagepage in list(using.imagelinks()))
        for using in mysite.imageusage(imagepage, filterredir=True, total=5):
            self.assertType(using, pywikibot.Page)
            self.assertTrue(using.isRedirectPage())
        for using in mysite.imageusage(imagepage, filterredir=True, total=5):
            self.assertType(using, pywikibot.Page)
            self.assertFalse(using.isRedirectPage())

    def testLogEvents(self):
        """Test the site.logevents() method"""

        le = list(mysite.logevents(total=10))
        self.assertTrue(len(le) <= 10)
        self.assertTrue(all(isinstance(entry, dict) and "type" in entry
                            for entry in le))
        for typ in ("block", "protect", "rights", "delete", "upload",
                "move", "import", "patrol", "merge"):
            for entry in mysite.logevents(logtype=typ, total=3):
                self.assertEqual(entry["type"], typ)
        for entry in mysite.logevents(page=mainpage, total=3):
            self.assertTrue("title" in entry
                            and entry["title"] == mainpage.title())
        for entry in mysite.logevents(user=mysite.user(), total=3):
            self.assertTrue("user" in entry
                            and entry["user"] == mysite.user())
        for entry in mysite.logevents(start="2008-09-01T00:00:01Z", total=5):
            self.assertType(entry, dict)
            self.assertTrue(entry['timestamp'] <= "2008-09-01T00:00:01Z")
        for entry in mysite.logevents(end="2008-09-02T23:59:59Z", total=5):
            self.assertType(entry, dict)
            self.assertTrue(entry['timestamp'] >= "2008-09-02T23:59:59Z")
        for entry in mysite.logevents(start="2008-02-02T00:00:01Z",
                                      end="2008-02-02T23:59:59Z",
                                      reverse=True, total=5):
            self.assertType(entry, dict)
            self.assertTrue("2008-02-02T00:00:01Z" <= entry['timestamp']
                                <= "2008-02-02T23:59:59Z")
        for entry in mysite.logevents(start="2008-02-03T23:59:59Z",
                                      end="2008-02-03T00:00:01Z",
                                      total=5):
            self.assertType(entry, dict)
            self.assertTrue("2008-02-03T00:00:01Z" <= entry['timestamp']
                                <= "2008-02-03T23:59:59Z")
        # starttime earlier than endtime
        self.assertRaises(pywikibot.Error, mysite.logevents,
                          start="2008-02-03T00:00:01Z",
                          end="2008-02-03T23:59:59Z", total=5)
        # reverse: endtime earlier than starttime
        self.assertRaises(pywikibot.Error, mysite.logevents,
                          start="2008-02-03T23:59:59Z",
                          end="2008-02-03T00:00:01Z", reverse=True, total=5)

    def testRecentchanges(self):
        """Test the site.recentchanges() method"""

        rc = list(mysite.recentchanges(total=10))
        self.assertTrue(len(rc) <= 10)
        self.assertTrue(all(isinstance(change, dict)
                            for change in rc))
        for change in mysite.recentchanges(start="2008-10-01T01:02:03Z",
                                           total=5):
            self.assertType(change, dict)
            self.assertTrue(change['timestamp'] <= "2008-10-01T01:02:03Z")
        for change in mysite.recentchanges(end="2008-04-01T02:03:04Z",
                                           total=5):
            self.assertType(change, dict)
            self.assertTrue(change['timestamp'] >= "2008-10-01T02:03:04Z")
        for change in mysite.recentchanges(start="2008-10-01T03:05:07Z",
                                           total=5, reverse=True):
            self.assertType(change, dict)
            self.assertTrue(change['timestamp'] >= "2008-10-01T03:05:07Z")
        for change in mysite.recentchanges(end="2008-10-01T04:06:08Z",
                                           total=5, reverse=True):
            self.assertType(change, dict)
            self.assertTrue(change['timestamp'] <= "2008-10-01T04:06:08Z")
        for change in mysite.recentchanges(start="2008-10-03T11:59:59Z",
                                           end="2008-10-03T00:00:01Z",
                                           total=5):
            self.assertType(change, dict)
            self.assertTrue("2008-10-03T00:00:01Z" <= change['timestamp']
                                <= "2008-10-03T11:59:59Z")
        for change in mysite.recentchanges(start="2008-10-05T06:00:01Z",
                                           end="2008-10-05T23:59:59Z",
                                           reverse=True, total=5):
            self.assertType(change, dict)
            self.assertTrue("2008-10-05T06:00:01Z" <= change['timestamp']
                                <= "2008-10-05T23:59:59Z")
        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.recentchanges,
                          start="2008-02-03T00:00:01Z",
                          end="2008-02-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.recentchanges,
                          start="2008-02-03T23:59:59Z",
                          end="2008-02-03T00:00:01Z", reverse=True, total=5)
        for change in mysite.recentchanges(namespaces=[6,7], total=5):
            self.assertType(change, dict)
            self.assertTrue("title" in change and "ns" in change)
            title = change['title']
            self.assertTrue(":" in title)
            prefix = title[ : title.index(":")]
            self.assertTrue(mysite.ns_index(prefix) in [6,7])
            self.assertTrue(change["ns"] in [6,7])
        for change in mysite.recentchanges(pagelist=[mainpage, imagepage],
                                           total=5):
            self.assertType(change, dict)
            self.assertTrue("title" in change)
            self.assertTrue(change["title"] in (mainpage.title(),
                                                imagepage.title()))
        for typ in ("edit", "new", "log"):
            for change in mysite.recentchanges(changetype=typ, total=5):
                self.assertType(change, dict)
                self.assertTrue("type" in change)
                self.assertEqual(change["type"], typ)
        for change in mysite.recentchanges(showMinor=True, total=5):
            self.assertType(change, dict)
            self.assertTrue("minor" in change)
        for change in mysite.recentchanges(showMinor=False, total=5):
            self.assertType(change, dict)
            self.assertTrue("minor" not in change)
        for change in mysite.recentchanges(showBot=True, total=5):
            self.assertType(change, dict)
            self.assertTrue("bot" in change)
        for change in mysite.recentchanges(showBot=False, total=5):
            self.assertType(change, dict)
            self.assertTrue("bot" not in change)
        for change in mysite.recentchanges(showAnon=True, total=5):
            self.assertType(change, dict)
        for change in mysite.recentchanges(showAnon=False, total=5):
            self.assertType(change, dict)
        for change in mysite.recentchanges(showRedirects=True, total=5):
            self.assertType(change, dict)
            self.assertTrue("redirect" in change)
        for change in mysite.recentchanges(showRedirects=False, total=5):
            self.assertType(change, dict)
            self.assertTrue("redirect" not in change)
        for change in mysite.recentchanges(showPatrolled=True, total=5):
            self.assertType(change, dict)
            self.assertTrue("patrolled" in change)
        for change in mysite.recentchanges(showPatrolled=False, total=5):
            self.assertType(change, dict)
            self.assertTrue("patrolled" not in change)

    def testSearch(self):
        """Test the site.search() method"""

        se = list(mysite.search("wiki", total=10))
        self.assertTrue(len(se) <= 10)
        self.assertTrue(all(isinstance(hit, pywikibot.Page)
                            for hit in se))
        self.assertTrue(all(hit.namespace() == 0 for hit in se))
        for hit in mysite.search("common", namespaces=4, total=5):
            self.assertType(hit, pywikibot.Page)
            self.assertEqual(hit.namespace(), 4)
        for hit in mysite.search("word", namespaces=[5,6,7], total=5):
            self.assertType(hit, pywikibot.Page)
            self.assertTrue(hit.namespace() in [5,6,7])
        for hit in mysite.search("another", namespaces="8|9|10", total=5):
            self.assertType(hit, pywikibot.Page)
            self.assertTrue(hit.namespace() in [8,9,10])
        for hit in mysite.search("wiki", namespaces=0, total=10,
                                 getredirects=True):
            self.assertType(hit, pywikibot.Page)
            self.assertEqual(hit.namespace(), 0)

    def testUsercontribs(self):
        """Test the site.usercontribs() method"""

        uc = list(mysite.usercontribs(user=mysite.user(), total=10))
        self.assertTrue(len(uc) <= 10)
        self.assertTrue(all(isinstance(contrib, dict)
                            for contrib in uc))
        self.assertTrue(all("user" in contrib
                            and contrib["user"] == mysite.user()
                            for contrib in uc))
        for contrib in mysite.usercontribs(userprefix="John", total=5):
            self.assertType(contrib, dict)
            for key in ("user", "title", "ns", "pageid", "revid"):
                self.assertTrue(key in contrib)
            self.assertTrue(contrib["user"].startswith("John"))
        for contrib in mysite.usercontribs(userprefix="Jane",
                                           start="2008-10-06T01:02:03Z",
                                           total=5):
            self.assertTrue(contrib['timestamp'] <= "2008-10-06T01:02:03Z")
        for contrib in mysite.usercontribs(userprefix="Jane",
                                           end="2008-10-07T02:03:04Z",
                                           total=5):
            self.assertTrue(contrib['timestamp'] >= "2008-10-07T02:03:04Z")
        for contrib in mysite.usercontribs(userprefix="Brion",
                                           start="2008-10-08T03:05:07Z",
                                           total=5, reverse=True):
            self.assertTrue(contrib['timestamp'] >= "2008-10-08T03:05:07Z")
        for contrib in mysite.usercontribs(userprefix="Brion",
                                           end="2008-10-09T04:06:08Z",
                                           total=5, reverse=True):
            self.assertTrue(contrib['timestamp'] <= "2008-10-09T04:06:08Z")
        for contrib in mysite.usercontribs(userprefix="Tim",
                                           start="2008-10-10T11:59:59Z",
                                           end="2008-10-10T00:00:01Z",
                                           total=5):
            self.assertTrue("2008-10-10T00:00:01Z" <= contrib['timestamp']
                                <= "2008-10-10T11:59:59Z")
        for contrib in mysite.usercontribs(userprefix="Tim",
                                           start="2008-10-11T06:00:01Z",
                                           end="2008-10-11T23:59:59Z",
                                           reverse=True, total=5):
            self.assertTrue("2008-10-11T06:00:01Z" <= contrib['timestamp']
                                <= "2008-10-11T23:59:59Z")
        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.usercontribs,
                          userprefix="Jim",
                          start="2008-10-03T00:00:01Z",
                          end="2008-10-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.usercontribs,
                          userprefix="Jim",
                          start="2008-10-03T23:59:59Z",
                          end="2008-10-03T00:00:01Z", reverse=True, total=5)

        for contrib in mysite.usercontribs(user=mysite.user(),
                                           namespaces=14, total=5):
            self.assertType(contrib, dict)
            self.assertTrue("title" in contrib)
            self.assertTrue(contrib["title"].startswith(mysite.namespace(14)))
        for contrib in mysite.usercontribs(user=mysite.user(),
                                           namespaces=[10,11], total=5):
            self.assertType(contrib, dict)
            self.assertTrue("title" in contrib)
            self.assertTrue(contrib["ns"] in (10, 11))
        for contrib in mysite.usercontribs(user=mysite.user(),
                                           showMinor=True, total=5):
            self.assertType(contrib, dict)
            self.assertTrue("minor" in contrib)
        for contrib in mysite.usercontribs(user=mysite.user(),
                                           showMinor=False, total=5):
            self.assertType(contrib, dict)
            self.assertTrue("minor" not in contrib)

    def testWatchlistrevs(self):
        """Test the site.watchlist_revs() method"""

        wl = list(mysite.watchlist_revs(total=10))
        self.assertTrue(len(wl) <= 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in wl))
        for rev in mysite.watchlist_revs(start="2008-10-11T01:02:03Z",
                                         total=5):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] <= "2008-10-11T01:02:03Z")
        for rev in mysite.watchlist_revs(end="2008-04-01T02:03:04Z",
                                         total=5):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] >= "2008-10-11T02:03:04Z")
        for rev in mysite.watchlist_revs(start="2008-10-11T03:05:07Z",
                                         total=5, reverse=True):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] >= "2008-10-11T03:05:07Z")
        for rev in mysite.watchlist_revs(end="2008-10-11T04:06:08Z",
                                         total=5, reverse=True):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] <= "2008-10-11T04:06:08Z")
        for rev in mysite.watchlist_revs(start="2008-10-13T11:59:59Z",
                                         end="2008-10-13T00:00:01Z",
                                         total=5):
            self.assertType(rev, dict)
            self.assertTrue("2008-10-13T00:00:01Z" <= rev['timestamp']
                                <= "2008-10-13T11:59:59Z")
        for rev in mysite.watchlist_revs(start="2008-10-15T06:00:01Z",
                                         end="2008-10-15T23:59:59Z",
                                         reverse=True, total=5):
            self.assertType(rev, dict)
            self.assertTrue("2008-10-15T06:00:01Z" <= rev['timestamp']
                                <= "2008-10-15T23:59:59Z")
        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.watchlist_revs,
                          start="2008-09-03T00:00:01Z",
                          end="2008-09-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.watchlist_revs,
                          start="2008-09-03T23:59:59Z",
                          end="2008-09-03T00:00:01Z", reverse=True, total=5)
        for rev in mysite.watchlist_revs(namespaces=[6,7], total=5):
            self.assertType(rev, dict)
            self.assertTrue("title" in rev and "ns" in rev)
            title = rev['title']
            self.assertTrue(":" in title)
            prefix = title[ : title.index(":")]
            self.assertTrue(mysite.ns_index(prefix) in [6,7])
            self.assertTrue(rev["ns"] in [6,7])
        for rev in mysite.watchlist_revs(showMinor=True, total=5):
            self.assertType(rev, dict)
            self.assertTrue("minor" in rev)
        for rev in mysite.watchlist_revs(showMinor=False, total=5):
            self.assertType(rev, dict)
            self.assertTrue("minor" not in rev)
        for rev in mysite.watchlist_revs(showBot=True, total=5):
            self.assertType(rev, dict)
            self.assertTrue("bot" in rev)
        for rev in mysite.watchlist_revs(showBot=False, total=5):
            self.assertType(rev, dict)
            self.assertTrue("bot" not in rev)
        for rev in mysite.watchlist_revs(showAnon=True, total=5):
            self.assertType(rev, dict)
        for rev in mysite.watchlist_revs(showAnon=False, total=5):
            self.assertType(rev, dict)

    def testDeletedrevs(self):
        """Test the site.deletedrevs() method"""

        if not mysite.logged_in(True):
            try:
                mysite.login(True)
            except pywikibot.NoUsername:
                logger.warn(
                 "Cannot test Site.deleted_revs; no sysop account configured.")
                return
        dr = list(mysite.deletedrevs(total=10, page=mainpage))
        self.assertTrue(len(dr) <= 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in dr))
        dr2 = list(mysite.deletedrevs(page=mainpage, total=10))
        self.assertTrue(len(dr2) <= 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in dr2))
        for rev in mysite.deletedrevs(start="2008-10-11T01:02:03Z",
                                      page=mainpage, total=5):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] <= "2008-10-11T01:02:03Z")
        for rev in mysite.deletedrevs(end="2008-04-01T02:03:04Z",
                                      page=mainpage, total=5):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] >= "2008-10-11T02:03:04Z")
        for rev in mysite.deletedrevs(start="2008-10-11T03:05:07Z",
                                      page=mainpage, total=5,
                                      reverse=True):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] >= "2008-10-11T03:05:07Z")
        for rev in mysite.deletedrevs(end="2008-10-11T04:06:08Z",
                                      page=mainpage, total=5,
                                      reverse=True):
            self.assertType(rev, dict)
            self.assertTrue(rev['timestamp'] <= "2008-10-11T04:06:08Z")
        for rev in mysite.deletedrevs(start="2008-10-13T11:59:59Z",
                                      end="2008-10-13T00:00:01Z",
                                      page=mainpage, total=5):
            self.assertType(rev, dict)
            self.assertTrue("2008-10-13T00:00:01Z" <= rev['timestamp']
                                <= "2008-10-13T11:59:59Z")
        for rev in mysite.deletedrevs(start="2008-10-15T06:00:01Z",
                                      end="2008-10-15T23:59:59Z",
                                      page=mainpage, reverse=True,
                                      total=5):
            self.assertType(rev, dict)
            self.assertTrue("2008-10-15T06:00:01Z" <= rev['timestamp']
                                <= "2008-10-15T23:59:59Z")
        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.deletedrevs,
                          page=mainpage, start="2008-09-03T00:00:01Z",
                          end="2008-09-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.deletedrevs,
                          page=mainpage, start="2008-09-03T23:59:59Z",
                          end="2008-09-03T00:00:01Z", reverse=True,
                          total=5)

    def testUsers(self):
        """Test the site.users() method"""

        us = list(mysite.users(mysite.user()))
        self.assertEqual(len(us), 1)
        self.assertType(us[0], dict)
        for user in mysite.users(
                ["Jimbo Wales", "Brion VIBBER", "Tim Starling"]):
            self.assertType(user, dict)
            self.assertTrue(user["name"]
                            in ["Jimbo Wales", "Brion VIBBER", "Tim Starling"])

    def testRandompages(self):
        """Test the site.randompages() method"""

        rn = list(mysite.randompages(total=10))
        self.assertTrue(len(rn) <= 10)
        self.assertTrue(all(isinstance(a_page, pywikibot.Page)
                            for a_page in rn))
        self.assertFalse(all(a_page.isRedirectPage() for a_page in rn))
        for rndpage in mysite.randompages(total=5, redirects=True):
            self.assertType(rndpage, pywikibot.Page)
            self.assertTrue(rndpage.isRedirectPage())
        for rndpage in mysite.randompages(total=5, namespaces=[6, 7]):
            self.assertType(rndpage, pywikibot.Page)
            self.assertTrue(rndpage.namespace() in [6, 7])


if __name__ == '__main__':
#    pywikibot.logging.getLogger("").setLevel(pywikibot.logging.DEBUG)
    try:
        try:
            unittest.main()
        except SystemExit:
            pass
    finally:
        pywikibot.stopme()
