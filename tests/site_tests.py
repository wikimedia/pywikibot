# -*- coding: utf-8  -*-
"""Tests for the site module."""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


import sys
from distutils.version import LooseVersion as LV
from collections import Iterable
from datetime import datetime
import re

import pywikibot
from tests.aspects import (
    unittest, TestCase,
    DefaultSiteTestCase,
    WikimediaDefaultSiteTestCase,
)

if sys.version_info[0] > 2:
    basestring = (str, )
    unicode = str


class TestSiteObjectDeprecatedFunctions(DefaultSiteTestCase):

    """Test cases for Site deprecated methods."""

    cached = True
    user = True

    def test_live_version(self):
        """Test live_version."""
        mysite = self.get_site()
        ver = mysite.live_version()
        self.assertIsInstance(ver, tuple)
        self.assertTrue(all(isinstance(ver[i], int) for i in (0, 1)))
        self.assertIsInstance(ver[2], basestring)

    def test_token(self):
        """Test ability to get page tokens."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        ttype = "edit"
        try:
            token = mysite.tokens[ttype]
        except KeyError:
            raise unittest.SkipTest(
                "Testing '%s' token not possible with user on %s"
                % (ttype, self.site))
        self.assertEqual(token, mysite.token(mainpage, ttype))


class TestSiteObject(DefaultSiteTestCase):

    """Test cases for Site methods."""

    cached = True

    def testPickleAbility(self):
        import pickle
        mysite = self.get_site()
        mysite_str = pickle.dumps(mysite)
        mysite_pickled = pickle.loads(mysite_str)
        self.assertEqual(mysite, mysite_pickled)

    def testBaseMethods(self):
        """Test cases for BaseSite methods."""
        mysite = self.get_site()
        self.assertEqual(mysite.family.name, self.family)
        self.assertEqual(mysite.code, self.code)
        self.assertIsInstance(mysite.lang, basestring)
        self.assertEqual(mysite, pywikibot.Site(self.code, self.family))
        self.assertIsInstance(mysite.user(), (basestring, type(None)))
        self.assertEqual(mysite.sitename(),
                         "%s:%s" % (self.family,
                                    self.code))
        self.assertEqual(repr(mysite),
                         'Site("%s", "%s")'
                         % (self.code, self.family))
        self.assertIsInstance(mysite.linktrail(), basestring)
        self.assertIsInstance(mysite.redirect(default=True), basestring)
        try:
            dabcat = mysite.disambcategory()
        except pywikibot.Error as e:
            self.assertIn('No disambiguation category name found', str(e))
        else:
            self.assertIsInstance(dabcat, pywikibot.Category)

        foo = unicode(pywikibot.Link("foo", source=mysite))
        self.assertEqual(foo, u"[[foo]]" if mysite.nocapitalize else u"[[Foo]]")

        self.assertFalse(mysite.isInterwikiLink("foo"))
        self.assertIsInstance(mysite.redirectRegex().pattern, basestring)
        self.assertIsInstance(mysite.category_on_one_line(), bool)
        for grp in ("user", "autoconfirmed", "bot", "sysop", "nosuchgroup"):
            self.assertIsInstance(mysite.has_group(grp), bool)
        for rgt in ("read", "edit", "move", "delete", "rollback", "block",
                    "nosuchright"):
            self.assertIsInstance(mysite.has_right(rgt), bool)

    def testConstructors(self):
        """Test cases for site constructors."""
        self.assertEqual(pywikibot.site.APISite.fromDBName('enwiki'), pywikibot.Site('en', 'wikipedia'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('eswikisource'), pywikibot.Site('es', 'wikisource'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('dewikinews'), pywikibot.Site('de', 'wikinews'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('ukwikivoyage'), pywikibot.Site('uk', 'wikivoyage'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('metawiki'), pywikibot.Site('meta', 'meta'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('commonswiki'), pywikibot.Site('commons', 'commons'))
        self.assertEqual(pywikibot.site.APISite.fromDBName('wikidatawiki'), pywikibot.Site('wikidata', 'wikidata'))

    def testLanguageMethods(self):
        """Test cases for languages() and related methods"""
        mysite = self.get_site()
        langs = mysite.languages()
        self.assertIsInstance(langs, list)
        self.assertIn(mysite.code, langs)
        mysite.family.obsolete
        ipf = mysite.interwiki_putfirst()
        if ipf:  # Not all languages use this
            self.assertIsInstance(ipf, list)

        for item in mysite.validLanguageLinks():
            self.assertIn(item, langs)

    def testNamespaceMethods(self):
        """Test cases for methods manipulating namespace names."""
        mysite = self.get_site()
        builtins = {
            '': 0,  # these should work in any MW wiki
            'Talk': 1,
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
        self.assertIsInstance(ns, dict)
        self.assertTrue(all(x in ns for x in range(0, 16)))
        # built-in namespaces always present
        self.assertIsInstance(mysite.ns_normalize("project"), basestring)
        self.assertTrue(all(isinstance(key, int)
                            for key in ns))
        self.assertTrue(all(isinstance(val, Iterable)
                            for val in ns.values()))
        self.assertTrue(all(isinstance(name, basestring)
                            for val in ns.values()
                            for name in val))
        self.assertTrue(all(isinstance(mysite.namespace(key), basestring)
                            for key in ns))
        self.assertTrue(all(isinstance(mysite.namespace(key, True), Iterable)
                            for key in ns))
        self.assertTrue(all(isinstance(item, basestring)
                            for key in ns
                            for item in mysite.namespace(key, True)))

    def testApiMethods(self):
        """Test generic ApiSite methods."""
        mysite = self.get_site()
        self.assertIsInstance(mysite.logged_in(), bool)
        self.assertIsInstance(mysite.logged_in(True), bool)
        self.assertIsInstance(mysite.userinfo, dict)
        self.assertIsInstance(mysite.is_blocked(), bool)
        self.assertIsInstance(mysite.messages(), bool)
        self.assertIsInstance(mysite.has_right("edit"), bool)
        self.assertFalse(mysite.has_right("nonexistent_right"))
        self.assertIsInstance(mysite.has_group("bots"), bool)
        self.assertFalse(mysite.has_group("nonexistent_group"))
        try:
            self.assertIsInstance(mysite.is_blocked(True), bool)
            self.assertIsInstance(mysite.has_right("edit", True), bool)
            self.assertFalse(mysite.has_right("nonexistent_right", True))
            self.assertIsInstance(mysite.has_group("bots", True), bool)
            self.assertFalse(mysite.has_group("nonexistent_group", True))
        except pywikibot.NoUsername:
            pywikibot.warning(
                "Cannot test Site methods for sysop; no sysop account configured.")

        for msg in ("1movedto2", "about", "aboutpage", "aboutsite",
                    "accesskey-n-portal"):
            self.assertTrue(mysite.has_mediawiki_message(msg))
            self.assertIsInstance(mysite.mediawiki_message(msg), basestring)
        self.assertFalse(mysite.has_mediawiki_message("nosuchmessage"))
        self.assertRaises(KeyError, mysite.mediawiki_message, "nosuchmessage")

        msg = ("1movedto2", "about", "aboutpage")
        self.assertIsInstance(mysite.mediawiki_messages(msg), dict)
        self.assertTrue(mysite.mediawiki_messages(msg))

        msg = ("nosuchmessage1", "about", "aboutpage", "nosuchmessage")
        self.assertFalse(mysite.has_all_mediawiki_messages(msg))
        self.assertRaises(KeyError, mysite.mediawiki_messages, msg)

        # Load all messages and check that '*' is not a valid key.
        self.assertIsInstance(mysite.mediawiki_messages('*'), dict)
        self.assertGreater(len(mysite.mediawiki_messages(['*'])), 10)
        self.assertNotIn('*', mysite.mediawiki_messages(['*']))

        self.assertIsInstance(mysite.getcurrenttime(), pywikibot.Timestamp)
        ts = mysite.getcurrenttimestamp()
        self.assertIsInstance(ts, basestring)
        self.assertRegexpMatches(ts, r'(19|20)\d\d[0-1]\d[0-3]\d[0-2]\d[0-5]\d[0-5]\d')

        self.assertIsInstance(mysite.siteinfo, pywikibot.site.Siteinfo)
        self.assertIsInstance(mysite.months_names, list)
        ver = mysite.version()
        self.assertIsInstance(ver, basestring)
        self.assertIsNotNone(re.search('^\d+\.\d+.*?\d*$', ver))
        self.assertEqual(mysite.list_to_text(('pywikibot',)), 'pywikibot')

    def testEnglishSpecificMethods(self):
        """Test Site methods using English specific inputs and outputs."""
        mysite = self.get_site()
        if mysite.lang != 'en':
            raise unittest.SkipTest(
                'English-specific tests not valid on %s' % mysite)

        self.assertEqual(mysite.months_names[4], (u'May', u'May'))
        self.assertEqual(mysite.list_to_text(('Pride', 'Prejudice')), 'Pride and Prejudice')
        self.assertEqual(mysite.list_to_text(('This', 'that', 'the other')), 'This, that and the other')

    def testPageMethods(self):
        """Test ApiSite methods for getting page-specific info."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        self.assertIsInstance(mysite.page_exists(mainpage), bool)
        self.assertIsInstance(mysite.page_restrictions(mainpage), dict)
        self.assertIsInstance(mysite.page_can_be_edited(mainpage), bool)
        self.assertIsInstance(mysite.page_isredirect(mainpage), bool)
        if mysite.page_isredirect(mainpage):
            self.assertIsInstance(mysite.getredirtarget(mainpage), pywikibot.Page)
        else:
            self.assertRaises(pywikibot.IsNotRedirectPage,
                              mysite.getredirtarget, mainpage)
        a = list(mysite.preloadpages([mainpage]))
        self.assertEqual(len(a), int(mysite.page_exists(mainpage)))
        if a:
            self.assertEqual(a[0], mainpage)

    def testPreload(self):
        """Test that preloading works."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        count = 0
        for page in mysite.preloadpages(mysite.pagelinks(mainpage, total=10)):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertIsInstance(page.exists(), bool)
            if page.exists():
                self.assertTrue(hasattr(page, "_text"))
            count += 1
            if count >= 5:
                break

    def testItemPreload(self):
        """Test that ItemPage preloading works."""
        mysite = self.get_site()
        if not mysite.has_data_repository:
            raise unittest.SkipTest('%s does not have a data repository'
                                    % mysite)

        datasite = mysite.data_repository()

        items = [pywikibot.ItemPage(datasite, 'q' + str(num)) for num in range(1, 6)]
        for page in datasite.preloaditempages(items):
            self.assertTrue(hasattr(page, '_content'))

    def testLinkMethods(self):
        """Test site methods for getting links to and from a page."""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        backlinks = set(mysite.pagebacklinks(mainpage, namespaces=[0]))
        # only non-redirects:
        filtered = set(mysite.pagebacklinks(mainpage, namespaces=0,
                                            filterRedirects=False))
        # only redirects:
        redirs = set(mysite.pagebacklinks(mainpage, namespaces=0,
                                          filterRedirects=True))
        # including links to redirect pages (but not the redirects):
        indirect = set(mysite.pagebacklinks(mainpage, namespaces=[0],
                                            followRedirects=True,
                                            filterRedirects=False))
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
            self.assertIsInstance(bl, pywikibot.Page)
            self.assertIn(bl, refs)
        for ei in embedded:
            self.assertIsInstance(ei, pywikibot.Page)
            self.assertIn(ei, refs)
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
            self.assertIsInstance(pl, pywikibot.Page)
        # test links arguments
        self.assertTrue(links.issuperset(
            set(mysite.pagelinks(mainpage, namespaces=[0, 1]))))
        for target in mysite.preloadpages(mysite.pagelinks(mainpage,
                                                           follow_redirects=True,
                                                           total=5)):
            self.assertIsInstance(target, pywikibot.Page)
            self.assertFalse(target.isRedirectPage())
        # test pagecategories
        for cat in mysite.pagecategories(mainpage):
            self.assertIsInstance(cat, pywikibot.Category)
            for cm in mysite.categorymembers(cat):
                self.assertIsInstance(cat, pywikibot.Page)
        # test pageimages
        self.assertTrue(all(isinstance(im, pywikibot.FilePage)
                            for im in mysite.pageimages(mainpage)))
        # test pagetemplates
        self.assertTrue(all(isinstance(te, pywikibot.Page)
                            for te in mysite.pagetemplates(mainpage)))
        self.assertTrue(set(mysite.pagetemplates(mainpage)).issuperset(
                        set(mysite.pagetemplates(mainpage, namespaces=[10]))))
        # test pagelanglinks
        for ll in mysite.pagelanglinks(mainpage):
            self.assertIsInstance(ll, pywikibot.Link)
        # test page_extlinks
        self.assertTrue(all(isinstance(el, basestring)
                            for el in mysite.page_extlinks(mainpage)))

    def testAllPages(self):
        """Test the site.allpages() method"""
        mysite = self.get_site()
        fwd = list(mysite.allpages(total=10))
        self.assertLessEqual(len(fwd), 10)
        for page in fwd:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
        rev = list(mysite.allpages(reverse=True, start="Aa", total=12))
        self.assertLessEqual(len(rev), 12)
        for page in rev:
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertLessEqual(page.title(), "Aa")
        for page in mysite.allpages(start="Py", total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertGreaterEqual(page.title(), "Py")
        for page in mysite.allpages(prefix="Pre", total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title().startswith("Pre"))
        for page in mysite.allpages(namespace=1, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 1)
        for page in mysite.allpages(filterredir=True, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.isRedirectPage())
        for page in mysite.allpages(filterredir=False, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertEqual(page.namespace(), 0)
            self.assertFalse(page.isRedirectPage())
#        for page in mysite.allpages(filterlanglinks=True, total=5):
#            self.assertIsInstance(page, pywikibot.Page)
#            self.assertTrue(mysite.page_exists(page))
#            self.assertEqual(page.namespace(), 0)
#        for page in mysite.allpages(filterlanglinks=False, total=5):
#            self.assertIsInstance(page, pywikibot.Page)
#            self.assertTrue(mysite.page_exists(page))
#            self.assertEqual(page.namespace(), 0)
        for page in mysite.allpages(minsize=100, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertGreaterEqual(len(page.text), 100)
        for page in mysite.allpages(maxsize=200, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            if len(page.text) > 200 and mysite.data_repository() == mysite:
                print('%s.text is > 200 bytes while raw JSON is <= 200'
                      % page)
                continue
            self.assertLessEqual(len(page.text), 200)
        for page in mysite.allpages(protect_type="edit", total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertIn("edit", page._protection)
        for page in mysite.allpages(protect_type="edit",
                                    protect_level="sysop", total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertTrue(mysite.page_exists(page))
            self.assertIn("edit", page._protection)
            self.assertIn("sysop", page._protection["edit"])

    def testAllLinks(self):
        """Test the site.alllinks() method"""
        mysite = self.get_site()
        fwd = list(mysite.alllinks(total=10))
        self.assertLessEqual(len(fwd), 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page) for link in fwd))
        uniq = list(mysite.alllinks(total=10, unique=True))
        self.assertTrue(all(link in uniq for link in fwd))
        for page in mysite.alllinks(start="Link", total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 0)
            self.assertGreaterEqual(page.title(), "Link")
        for page in mysite.alllinks(prefix="Fix", total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 0)
            self.assertTrue(page.title().startswith("Fix"))
        for page in mysite.alllinks(namespace=1, total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertEqual(page.namespace(), 1)
        for page in mysite.alllinks(start="From", namespace=4, fromids=True,
                                    total=5):
            self.assertIsInstance(page, pywikibot.Page)
            self.assertGreaterEqual(page.title(withNamespace=False), "From")
            self.assertTrue(hasattr(page, "_fromid"))
        errgen = mysite.alllinks(unique=True, fromids=True)
        self.assertRaises(pywikibot.Error, next, errgen)

    def testAllCategories(self):
        """Test the site.allcategories() method"""
        mysite = self.get_site()
        ac = list(mysite.allcategories(total=10))
        self.assertLessEqual(len(ac), 10)
        self.assertTrue(all(isinstance(cat, pywikibot.Category)
                            for cat in ac))
        for cat in mysite.allcategories(total=5, start="Abc"):
            self.assertIsInstance(cat, pywikibot.Category)
            self.assertGreaterEqual(cat.title(withNamespace=False), "Abc")
        for cat in mysite.allcategories(total=5, prefix="Def"):
            self.assertIsInstance(cat, pywikibot.Category)
            self.assertTrue(cat.title(withNamespace=False).startswith("Def"))
#        # Bug # 15985
#        for cat in mysite.allcategories(total=5, start="Hij", reverse=True):
#            self.assertIsInstance(cat, pywikibot.Category)
#            self.assertLessEqual(cat.title(withNamespace=False), "Hij")

    def testAllUsers(self):
        """Test the site.allusers() method"""
        mysite = self.get_site()
        au = list(mysite.allusers(total=10))
        self.assertLessEqual(len(au), 10)
        for user in au:
            self.assertIsInstance(user, dict)
            self.assertIn("name", user)
            self.assertIn("editcount", user)
            self.assertIn("registration", user)
        for user in mysite.allusers(start="B", total=5):
            self.assertIsInstance(user, dict)
            self.assertIn("name", user)
            self.assertGreaterEqual(user["name"], "B")
            self.assertIn("editcount", user)
            self.assertIn("registration", user)
        for user in mysite.allusers(prefix="C", total=5):
            self.assertIsInstance(user, dict)
            self.assertIn("name", user)
            self.assertTrue(user["name"].startswith("C"))
            self.assertIn("editcount", user)
            self.assertIn("registration", user)
        for user in mysite.allusers(prefix="D", group="sysop", total=5):
            self.assertIsInstance(user, dict)
            self.assertIn("name", user)
            self.assertTrue(user["name"].startswith("D"))
            self.assertIn("editcount", user)
            self.assertIn("registration", user)
            self.assertTrue("groups" in user and "sysop" in user["groups"])

    def testAllImages(self):
        """Test the site.allimages() method"""
        mysite = self.get_site()
        ai = list(mysite.allimages(total=10))
        self.assertLessEqual(len(ai), 10)
        self.assertTrue(all(isinstance(image, pywikibot.FilePage)
                            for image in ai))
        for impage in mysite.allimages(start="Ba", total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertGreaterEqual(impage.title(withNamespace=False), "Ba")
#        # Bug # 15985
#        for impage in mysite.allimages(start="Da", reverse=True, total=5):
#            self.assertIsInstance(impage, pywikibot.FilePage)
#            self.assertTrue(mysite.page_exists(impage))
#            self.assertLessEqual(impage.title(), "Da")
        for impage in mysite.allimages(prefix="Ch", total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertTrue(impage.title(withNamespace=False).startswith("Ch"))
        for impage in mysite.allimages(minsize=100, total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertGreaterEqual(impage._imageinfo["size"], 100)
        for impage in mysite.allimages(maxsize=2000, total=5):
            self.assertIsInstance(impage, pywikibot.FilePage)
            self.assertTrue(mysite.page_exists(impage))
            self.assertLessEqual(impage._imageinfo["size"], 2000)

    def testBlocks(self):
        """Test the site.blocks() method"""
        mysite = self.get_site()
        props = ("id", "by", "timestamp", "expiry", "reason")
        bl = list(mysite.blocks(total=10))
        self.assertLessEqual(len(bl), 10)
        for block in bl:
            self.assertIsInstance(block, dict)
            for prop in props:
                self.assertIn(prop, block)
        # timestamps should be in descending order
        timestamps = [block['timestamp'] for block in bl]
        for t in range(1, len(timestamps)):
            self.assertLessEqual(timestamps[t], timestamps[t - 1])

        b2 = list(mysite.blocks(total=10, reverse=True))
        self.assertLessEqual(len(b2), 10)
        for block in b2:
            self.assertIsInstance(block, dict)
            for prop in props:
                self.assertIn(prop, block)
        # timestamps should be in ascending order
        timestamps = [block['timestamp'] for block in b2]
        for t in range(1, len(timestamps)):
            self.assertGreaterEqual(timestamps[t], timestamps[t - 1])

        for block in mysite.blocks(starttime="2008-07-01T00:00:01Z", total=5):
            self.assertIsInstance(block, dict)
            for prop in props:
                self.assertIn(prop, block)
        for block in mysite.blocks(endtime="2008-07-31T23:59:59Z", total=5):
            self.assertIsInstance(block, dict)
            for prop in props:
                self.assertIn(prop, block)
        for block in mysite.blocks(starttime="2008-08-02T00:00:01Z",
                                   endtime="2008-08-02T23:59:59Z",
                                   reverse=True, total=5):
            self.assertIsInstance(block, dict)
            for prop in props:
                self.assertIn(prop, block)
        for block in mysite.blocks(starttime="2008-08-03T23:59:59Z",
                                   endtime="2008-08-03T00:00:01Z",
                                   total=5):
            self.assertIsInstance(block, dict)
            for prop in props:
                self.assertIn(prop, block)
        # starttime earlier than endtime
        self.assertRaises(pywikibot.Error, mysite.blocks,
                          starttime="2008-08-03T00:00:01Z",
                          endtime="2008-08-03T23:59:59Z", total=5)
        # reverse: endtime earlier than starttime
        self.assertRaises(pywikibot.Error, mysite.blocks,
                          starttime="2008-08-03T23:59:59Z",
                          endtime="2008-08-03T00:00:01Z", reverse=True, total=5)
        for block in mysite.blocks(users=mysite.user(), total=5):
            self.assertIsInstance(block, dict)
            self.assertEqual(block['user'], mysite.user())

    def testExturlusage(self):
        """Test the site.exturlusage() method"""
        mysite = self.get_site()
        url = "www.google.com"
        eu = list(mysite.exturlusage(url, total=10))
        self.assertLessEqual(len(eu), 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page)
                            for link in eu))
        for link in mysite.exturlusage(url, namespaces=[2, 3], total=5):
            self.assertIsInstance(link, pywikibot.Page)
            self.assertIn(link.namespace(), (2, 3))

    def testImageusage(self):
        """Test the site.imageusage() method"""
        mysite = self.get_site()
        # Find a page which uses an image, so we can test imageusage
        # If there are no images included in pages it'll skip this test
        for page in mysite.allpages(filterredir=False):
            try:
                imagepage = next(iter(page.imagelinks()))  # 1st image of page
            except StopIteration:
                pass
            else:
                break
        else:
            raise unittest.SkipTest("No images on site {0!r}".format(mysite))

        iu = list(mysite.imageusage(imagepage, total=10))
        self.assertLessEqual(len(iu), 10)
        self.assertTrue(all(isinstance(link, pywikibot.Page)
                            for link in iu))
        for using in mysite.imageusage(imagepage, namespaces=[3, 4], total=5):
            self.assertIsInstance(using, pywikibot.Page)
            self.assertIn(imagepage, list(using.imagelinks()))
        for using in mysite.imageusage(imagepage, filterredir=True, total=5):
            self.assertIsInstance(using, pywikibot.Page)
            self.assertTrue(using.isRedirectPage())
        for using in mysite.imageusage(imagepage, filterredir=False, total=5):
            self.assertIsInstance(using, pywikibot.Page)
            self.assertFalse(using.isRedirectPage())


class SiteUserTestCase(DefaultSiteTestCase):

    """Test site method using a user."""

    user = True

    def testLogEvents(self):
        """Test the site.logevents() method"""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        le = list(mysite.logevents(total=10))
        self.assertLessEqual(len(le), 10)
        self.assertTrue(all(isinstance(entry, pywikibot.logentries.LogEntry)
                            for entry in le))
        for typ in ("block", "protect", "rights", "delete", "upload",
                    "move", "import", "patrol", "merge"):
            for entry in mysite.logevents(logtype=typ, total=3):
                self.assertEqual(entry.type(), typ)
        for entry in mysite.logevents(page=mainpage, total=3):
            self.assertEqual(entry.title().title(), mainpage.title())
        for entry in mysite.logevents(user=mysite.user(), total=3):
            self.assertEqual(entry.user(), mysite.user())
        for entry in mysite.logevents(start="2008-09-01T00:00:01Z", total=5):
            self.assertIsInstance(entry, pywikibot.logentries.LogEntry)
            self.assertLessEqual(str(entry.timestamp()), "2008-09-01T00:00:01Z")
        for entry in mysite.logevents(end="2008-09-02T23:59:59Z", total=5):
            self.assertIsInstance(entry, pywikibot.logentries.LogEntry)
            self.assertGreaterEqual(str(entry.timestamp()), "2008-09-02T23:59:59Z")
        for entry in mysite.logevents(start="2008-02-02T00:00:01Z",
                                      end="2008-02-02T23:59:59Z",
                                      reverse=True, total=5):
            self.assertIsInstance(entry, pywikibot.logentries.LogEntry)
            self.assertTrue(
                "2008-02-02T00:00:01Z" <= str(entry.timestamp()) <= "2008-02-02T23:59:59Z")
        for entry in mysite.logevents(start="2008-02-03T23:59:59Z",
                                      end="2008-02-03T00:00:01Z",
                                      total=5):
            self.assertIsInstance(entry, pywikibot.logentries.LogEntry)
            self.assertTrue(
                "2008-02-03T00:00:01Z" <= str(entry.timestamp()) <= "2008-02-03T23:59:59Z")
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
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        try:
            # 1st image on main page
            imagepage = next(iter(mysite.allimages()))
        except StopIteration:
            print("No images on site {0!r}".format(mysite))
            imagepage = None
        rc = list(mysite.recentchanges(total=10))
        self.assertLessEqual(len(rc), 10)
        self.assertTrue(all(isinstance(change, dict)
                            for change in rc))
        for change in mysite.recentchanges(start="2008-10-01T01:02:03Z",
                                           total=5):
            self.assertIsInstance(change, dict)
            self.assertLessEqual(change['timestamp'], "2008-10-01T01:02:03Z")
        for change in mysite.recentchanges(end="2008-04-01T02:03:04Z",
                                           total=5):
            self.assertIsInstance(change, dict)
            self.assertGreaterEqual(change['timestamp'], "2008-10-01T02:03:04Z")
        for change in mysite.recentchanges(start="2008-10-01T03:05:07Z",
                                           total=5, reverse=True):
            self.assertIsInstance(change, dict)
            self.assertGreaterEqual(change['timestamp'], "2008-10-01T03:05:07Z")
        for change in mysite.recentchanges(end="2008-10-01T04:06:08Z",
                                           total=5, reverse=True):
            self.assertIsInstance(change, dict)
            self.assertLessEqual(change['timestamp'], "2008-10-01T04:06:08Z")
        for change in mysite.recentchanges(start="2008-10-03T11:59:59Z",
                                           end="2008-10-03T00:00:01Z",
                                           total=5):
            self.assertIsInstance(change, dict)
            self.assertTrue(
                "2008-10-03T00:00:01Z" <= change['timestamp'] <= "2008-10-03T11:59:59Z")
        for change in mysite.recentchanges(start="2008-10-05T06:00:01Z",
                                           end="2008-10-05T23:59:59Z",
                                           reverse=True, total=5):
            self.assertIsInstance(change, dict)
            self.assertTrue(
                "2008-10-05T06:00:01Z" <= change['timestamp'] <= "2008-10-05T23:59:59Z")
        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.recentchanges,
                          start="2008-02-03T00:00:01Z",
                          end="2008-02-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.recentchanges,
                          start="2008-02-03T23:59:59Z",
                          end="2008-02-03T00:00:01Z", reverse=True, total=5)
        for change in mysite.recentchanges(namespaces=[6, 7], total=5):
            self.assertIsInstance(change, dict)
            self.assertTrue("title" in change and "ns" in change)
            title = change['title']
            self.assertIn(":", title)
            prefix = title[:title.index(":")]
            self.assertIn(mysite.ns_index(prefix), [6, 7])
            self.assertIn(change["ns"], [6, 7])
        if LV(mysite.version()) <= LV("1.14"):
            pagelist = [mainpage]
            if imagepage:
                pagelist += [imagepage]
            titlelist = set(page.title() for page in pagelist)
            for change in mysite.recentchanges(pagelist=pagelist,
                                               total=5):
                self.assertIsInstance(change, dict)
                self.assertIn("title", change)
                self.assertIn(change["title"], titlelist)
        for typ in ("edit", "new", "log"):
            for change in mysite.recentchanges(changetype=typ, total=5):
                self.assertIsInstance(change, dict)
                self.assertIn("type", change)
                self.assertEqual(change["type"], typ)
        for change in mysite.recentchanges(showMinor=True, total=5):
            self.assertIsInstance(change, dict)
            self.assertIn("minor", change)
        for change in mysite.recentchanges(showMinor=False, total=5):
            self.assertIsInstance(change, dict)
            self.assertNotIn("minor", change)
        for change in mysite.recentchanges(showBot=True, total=5):
            self.assertIsInstance(change, dict)
            self.assertIn("bot", change)
        for change in mysite.recentchanges(showBot=False, total=5):
            self.assertIsInstance(change, dict)
            self.assertNotIn("bot", change)
        for change in mysite.recentchanges(showAnon=True, total=5):
            self.assertIsInstance(change, dict)
        for change in mysite.recentchanges(showAnon=False, total=5):
            self.assertIsInstance(change, dict)
        for change in mysite.recentchanges(showRedirects=True, total=5):
            self.assertIsInstance(change, dict)
            self.assertIn("redirect", change)
        for change in mysite.recentchanges(showRedirects=False, total=5):
            self.assertIsInstance(change, dict)
            self.assertNotIn("redirect", change)
        for change in mysite.recentchanges(showPatrolled=True, total=5):
            self.assertIsInstance(change, dict)
            if mysite.has_right('patrol'):
                self.assertIn("patrolled", change)
        for change in mysite.recentchanges(showPatrolled=False, total=5):
            self.assertIsInstance(change, dict)
            if mysite.has_right('patrol'):
                self.assertNotIn("patrolled", change)

    def testSearch(self):
        """Test the site.search() method"""
        mysite = self.get_site()
        try:
            se = list(mysite.search("wiki", total=100))
            self.assertLessEqual(len(se), 100)
            self.assertTrue(all(isinstance(hit, pywikibot.Page)
                                for hit in se))
            self.assertTrue(all(hit.namespace() == 0 for hit in se))
            for hit in mysite.search("common", namespaces=4, total=5):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertEqual(hit.namespace(), 4)
            for hit in mysite.search("word", namespaces=[5, 6, 7], total=5):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertIn(hit.namespace(), [5, 6, 7])
            for hit in mysite.search("another", namespaces="8|9|10", total=5):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertIn(hit.namespace(), [8, 9, 10])
            for hit in mysite.search("wiki", namespaces=0, total=10,
                                     getredirects=True):
                self.assertIsInstance(hit, pywikibot.Page)
                self.assertEqual(hit.namespace(), 0)
        except pywikibot.data.api.APIError as e:
            if e.code == "gsrsearch-error" and "timed out" in e.info:
                raise unittest.SkipTest("gsrsearch returned timeout on site: %r" % e)
            raise

    def testUsercontribs(self):
        """Test the site.usercontribs() method"""
        mysite = self.get_site()
        uc = list(mysite.usercontribs(user=mysite.user(), total=10))
        self.assertLessEqual(len(uc), 10)
        self.assertTrue(all(isinstance(contrib, dict)
                            for contrib in uc))
        self.assertTrue(all("user" in contrib
                            and contrib["user"] == mysite.user()
                            for contrib in uc))
        for contrib in mysite.usercontribs(userprefix="John", total=5):
            self.assertIsInstance(contrib, dict)
            for key in ("user", "title", "ns", "pageid", "revid"):
                self.assertIn(key, contrib)
            self.assertTrue(contrib["user"].startswith("John"))
        for contrib in mysite.usercontribs(userprefix="Jane",
                                           start="2008-10-06T01:02:03Z",
                                           total=5):
            self.assertLessEqual(contrib['timestamp'], "2008-10-06T01:02:03Z")
        for contrib in mysite.usercontribs(userprefix="Jane",
                                           end="2008-10-07T02:03:04Z",
                                           total=5):
            self.assertGreaterEqual(contrib['timestamp'], "2008-10-07T02:03:04Z")
        for contrib in mysite.usercontribs(userprefix="Brion",
                                           start="2008-10-08T03:05:07Z",
                                           total=5, reverse=True):
            self.assertGreaterEqual(contrib['timestamp'], "2008-10-08T03:05:07Z")
        for contrib in mysite.usercontribs(userprefix="Brion",
                                           end="2008-10-09T04:06:08Z",
                                           total=5, reverse=True):
            self.assertLessEqual(contrib['timestamp'], "2008-10-09T04:06:08Z")
        for contrib in mysite.usercontribs(userprefix="Tim",
                                           start="2008-10-10T11:59:59Z",
                                           end="2008-10-10T00:00:01Z",
                                           total=5):
            self.assertTrue(
                "2008-10-10T00:00:01Z" <= contrib['timestamp'] <= "2008-10-10T11:59:59Z")
        for contrib in mysite.usercontribs(userprefix="Tim",
                                           start="2008-10-11T06:00:01Z",
                                           end="2008-10-11T23:59:59Z",
                                           reverse=True, total=5):
            self.assertTrue(
                "2008-10-11T06:00:01Z" <= contrib['timestamp'] <= "2008-10-11T23:59:59Z")
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
            self.assertIsInstance(contrib, dict)
            self.assertIn("title", contrib)
            self.assertTrue(contrib["title"].startswith(mysite.namespace(14)))
        for contrib in mysite.usercontribs(user=mysite.user(),
                                           namespaces=[10, 11], total=5):
            self.assertIsInstance(contrib, dict)
            self.assertIn("title", contrib)
            self.assertIn(contrib["ns"], (10, 11))
        for contrib in mysite.usercontribs(user=mysite.user(),
                                           showMinor=True, total=5):
            self.assertIsInstance(contrib, dict)
            self.assertIn("minor", contrib)
        for contrib in mysite.usercontribs(user=mysite.user(),
                                           showMinor=False, total=5):
            self.assertIsInstance(contrib, dict)
            self.assertNotIn("minor", contrib)

    def testWatchlistrevs(self):
        """Test the site.watchlist_revs() method"""
        mysite = self.get_site()
        wl = list(mysite.watchlist_revs(total=10))
        self.assertLessEqual(len(wl), 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in wl))
        for rev in mysite.watchlist_revs(start="2008-10-11T01:02:03Z",
                                         total=5):
            self.assertIsInstance(rev, dict)
            self.assertLessEqual(rev['timestamp'], "2008-10-11T01:02:03Z")
        for rev in mysite.watchlist_revs(end="2008-04-01T02:03:04Z",
                                         total=5):
            self.assertIsInstance(rev, dict)
            self.assertGreaterEqual(rev['timestamp'], "2008-10-11T02:03:04Z")
        for rev in mysite.watchlist_revs(start="2008-10-11T03:05:07Z",
                                         total=5, reverse=True):
            self.assertIsInstance(rev, dict)
            self.assertGreaterEqual(rev['timestamp'], "2008-10-11T03:05:07Z")
        for rev in mysite.watchlist_revs(end="2008-10-11T04:06:08Z",
                                         total=5, reverse=True):
            self.assertIsInstance(rev, dict)
            self.assertLessEqual(rev['timestamp'], "2008-10-11T04:06:08Z")
        for rev in mysite.watchlist_revs(start="2008-10-13T11:59:59Z",
                                         end="2008-10-13T00:00:01Z",
                                         total=5):
            self.assertIsInstance(rev, dict)
            self.assertTrue(
                "2008-10-13T00:00:01Z" <= rev['timestamp'] <= "2008-10-13T11:59:59Z")
        for rev in mysite.watchlist_revs(start="2008-10-15T06:00:01Z",
                                         end="2008-10-15T23:59:59Z",
                                         reverse=True, total=5):
            self.assertIsInstance(rev, dict)
            self.assertTrue(
                "2008-10-15T06:00:01Z" <= rev['timestamp'] <= "2008-10-15T23:59:59Z")
        # start earlier than end
        self.assertRaises(pywikibot.Error, mysite.watchlist_revs,
                          start="2008-09-03T00:00:01Z",
                          end="2008-09-03T23:59:59Z", total=5)
        # reverse: end earlier than start
        self.assertRaises(pywikibot.Error, mysite.watchlist_revs,
                          start="2008-09-03T23:59:59Z",
                          end="2008-09-03T00:00:01Z", reverse=True, total=5)
        for rev in mysite.watchlist_revs(namespaces=[6, 7], total=5):
            self.assertIsInstance(rev, dict)
            self.assertTrue("title" in rev and "ns" in rev)
            title = rev['title']
            self.assertIn(":", title)
            prefix = title[:title.index(":")]
            self.assertIn(mysite.ns_index(prefix), [6, 7])
            self.assertIn(rev["ns"], [6, 7])
        for rev in mysite.watchlist_revs(showMinor=True, total=5):
            self.assertIsInstance(rev, dict)
            self.assertIn("minor", rev)
        for rev in mysite.watchlist_revs(showMinor=False, total=5):
            self.assertIsInstance(rev, dict)
            self.assertNotIn("minor", rev)
        for rev in mysite.watchlist_revs(showBot=True, total=5):
            self.assertIsInstance(rev, dict)
            self.assertIn("bot", rev)
        for rev in mysite.watchlist_revs(showBot=False, total=5):
            self.assertIsInstance(rev, dict)
            self.assertNotIn("bot", rev)
        for rev in mysite.watchlist_revs(showAnon=True, total=5):
            self.assertIsInstance(rev, dict)
        for rev in mysite.watchlist_revs(showAnon=False, total=5):
            self.assertIsInstance(rev, dict)

    def testDeletedrevs(self):
        """Test the site.deletedrevs() method"""
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        if not mysite.logged_in(True):
            try:
                mysite.login(True)
            except pywikibot.NoUsername:
                pywikibot.warning(
                    "Cannot test Site.deleted_revs; no sysop account configured.")
                return
        gen = mysite.deletedrevs(total=10, page=mainpage)
        for dr in gen:
            break
        else:
            raise unittest.SkipTest(
                '{0} contains no deleted revisions.'.format(mainpage))
        self.assertLessEqual(len(dr['revisions']), 10)
        self.assertTrue(all(isinstance(rev, dict)
                            for rev in dr['revisions']))
        for item in mysite.deletedrevs(start="2008-10-11T01:02:03Z",
                                       page=mainpage, total=5):
            for rev in item['revisions']:
                self.assertIsInstance(rev, dict)
                self.assertLessEqual(rev['timestamp'], "2008-10-11T01:02:03Z")
        for item in mysite.deletedrevs(end="2008-04-01T02:03:04Z",
                                       page=mainpage, total=5):
            for rev in item['revisions']:
                self.assertIsInstance(rev, dict)
                self.assertGreaterEqual(rev['timestamp'], "2008-10-11T02:03:04Z")
        for item in mysite.deletedrevs(start="2008-10-11T03:05:07Z",
                                       page=mainpage, total=5,
                                       reverse=True):
            for rev in item['revisions']:
                self.assertIsInstance(rev, dict)
                self.assertGreaterEqual(rev['timestamp'], "2008-10-11T03:05:07Z")
        for item in mysite.deletedrevs(end="2008-10-11T04:06:08Z",
                                       page=mainpage, total=5,
                                       reverse=True):
            for rev in item['revisions']:
                self.assertIsInstance(rev, dict)
                self.assertLessEqual(rev['timestamp'], "2008-10-11T04:06:08Z")
        for item in mysite.deletedrevs(start="2008-10-13T11:59:59Z",
                                       end="2008-10-13T00:00:01Z",
                                       page=mainpage, total=5):
            for rev in item['revisions']:
                self.assertIsInstance(rev, dict)
                self.assertLessEqual(rev['timestamp'], "2008-10-13T11:59:59Z")
                self.assertGreaterEqual(rev['timestamp'], "2008-10-13T00:00:01Z")
        for item in mysite.deletedrevs(start="2008-10-15T06:00:01Z",
                                       end="2008-10-15T23:59:59Z",
                                       page=mainpage, reverse=True,
                                       total=5):
            for rev in item['revisions']:
                self.assertIsInstance(rev, dict)
                self.assertLessEqual(rev['timestamp'], "2008-10-15T23:59:59Z")
                self.assertGreaterEqual(rev['timestamp'], "2008-10-15T06:00:01Z")

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
        mysite = self.get_site()
        us = list(mysite.users(mysite.user()))
        self.assertEqual(len(us), 1)
        self.assertIsInstance(us[0], dict)
        for user in mysite.users(
                ["Jimbo Wales", "Brion VIBBER", "Tim Starling"]):
            self.assertIsInstance(user, dict)
            self.assertTrue(user["name"]
                            in ["Jimbo Wales", "Brion VIBBER", "Tim Starling"])


class SiteRandomTestCase(DefaultSiteTestCase):

    """Test random methods of a site."""

    def testRandompages(self):
        """Test the site.randompages() method"""
        mysite = self.get_site()
        rn = list(mysite.randompages(total=10))
        self.assertLessEqual(len(rn), 10)
        self.assertTrue(all(isinstance(a_page, pywikibot.Page)
                            for a_page in rn))
        self.assertFalse(all(a_page.isRedirectPage() for a_page in rn))
        for rndpage in mysite.randompages(total=5, redirects=True):
            self.assertIsInstance(rndpage, pywikibot.Page)
            self.assertTrue(rndpage.isRedirectPage())
        for rndpage in mysite.randompages(total=5, namespaces=[6, 7]):
            self.assertIsInstance(rndpage, pywikibot.Page)
            self.assertIn(rndpage.namespace(), [6, 7])

    # TODO: test newimages, longpages, shortpages, ancientpages, unwatchedpages
    #       and the other following methods in site.py


class TestSiteTokens(DefaultSiteTestCase):

    """Test cases for tokens in Site methods."""

    user = True

    def setUp(self):
        """Store version."""
        self.mysite = self.get_site()
        self._version = LV(self.mysite.version())
        self.orig_version = self.mysite.version

    def tearDown(self):
        """Restore version."""
        self.mysite.version = self.orig_version

    def _test_tokens(self, version, test_version, in_tested, additional_token):
        if version and self._version < LV(version):
            raise unittest.SkipTest(
                u'Site %s version %s is too low for this tests.'
                % (self.mysite, self._version))
        self.mysite.version = lambda: test_version
        for ttype in ("edit", "move", additional_token):
            try:
                token = self.mysite.tokens[ttype]
            except pywikibot.Error as error_msg:
                self.assertRegexpMatches(
                    unicode(error_msg),
                    "Action '[a-z]+' is not allowed for user .* on .* wiki.")
            else:
                self.assertIsInstance(token, basestring)
                self.assertEqual(token, self.mysite.tokens[ttype])
        # test __contains__
        self.assertIn(in_tested, self.mysite.tokens)

    def test_tokens_in_mw_119(self):
        """Test ability to get page tokens."""
        self._test_tokens(None, '1.19', 'edit', 'delete')

    def test_tokens_in_mw_120_124wmf18(self):
        """Test ability to get page tokens."""
        self._test_tokens('1.20', '1.21', 'edit', 'deleteglobalaccount')

    def test_tokens_in_mw_124wmf19(self):
        """Test ability to get page tokens."""
        self._test_tokens('1.24wmf19', '1.24wmf20', 'csrf', 'deleteglobalaccount')

    def testInvalidToken(self):
        self.assertRaises(pywikibot.Error, lambda t: self.mysite.tokens[t], "invalidtype")


class TestSiteExtensions(WikimediaDefaultSiteTestCase):

    """Test cases for Site extensions."""

    cached = True

    def testExtensions(self):
        mysite = self.get_site()
        # test automatically getting extensions cache
        if 'extensions' in mysite.siteinfo:
            del mysite.siteinfo._cache['extensions']
        self.assertTrue(mysite.has_extension('Disambiguator'))

        # test case-sensitivity
        self.assertTrue(mysite.has_extension('disambiguator'))

        self.assertFalse(mysite.has_extension('ThisExtensionDoesNotExist'))


class TestSiteAPILimits(TestCase):

    """Test cases for Site method that use API limits."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def test_API_limits_with_site_methods(self):
        # test step/total parameters for different sitemethods
        mysite = self.get_site()
        mypage = pywikibot.Page(mysite, 'Albert Einstein')
        mycat = pywikibot.Page(mysite, 'Category:1879 births')

        cats = [c for c in mysite.pagecategories(mypage, step=5, total=12)]
        self.assertEqual(len(cats), 12)

        cat_members = [cm for cm in mysite.categorymembers(mycat, step=5, total=12)]
        self.assertEqual(len(cat_members), 12)

        images = [im for im in mysite.pageimages(mypage, step=3, total=5)]
        self.assertEqual(len(images), 5)

        templates = [tl for tl in mysite.pagetemplates(mypage, step=3, total=5)]
        self.assertEqual(len(templates), 5)

        mysite.loadrevisions(mypage, step=5, total=12)
        self.assertEqual(len(mypage._revisions), 12)


class TestSiteInfo(WikimediaDefaultSiteTestCase):

    """Test cases for Site metadata and capabilities."""

    cached = True

    def testSiteinfo(self):
        """Test the siteinfo property."""
        mysite = self.get_site()
        # general enteries
        mysite = self.get_site()
        self.assertIsInstance(mysite.siteinfo['timeoffset'], (int, float))
        self.assertTrue(-12 * 60 <= mysite.siteinfo['timeoffset'] <= +14 * 60)
        self.assertEqual(mysite.siteinfo['timeoffset'] % 15, 0)
        self.assertRegexpMatches(mysite.siteinfo['timezone'], "([A-Z]{3,4}|[A-Z][a-z]+/[A-Z][a-z]+)")
        self.assertIsInstance(datetime.strptime(mysite.siteinfo['time'], "%Y-%m-%dT%H:%M:%SZ"), datetime)
        self.assertGreater(mysite.siteinfo['maxuploadsize'], 0)
        self.assertIn(mysite.case(), ["first-letter", "case-sensitive"])
        self.assertEqual(re.findall("\$1", mysite.siteinfo['articlepath']), ["$1"])

        def entered_loop(iterable):
            for iterable_item in iterable:
                return True
            return False

        self.assertIsInstance(mysite.siteinfo.get('restrictions'), dict)
        self.assertIn('restrictions', mysite.siteinfo)
        # the following line only works in 1.23+
        self.assertTrue(mysite.siteinfo.is_recognised('restrictions'))
        del mysite.siteinfo._cache['restrictions']
        self.assertIsInstance(mysite.siteinfo.get('restrictions', cache=False), dict)
        self.assertNotIn('restrictions', mysite.siteinfo)

        not_exists = 'this-property-does-not-exist'
        self.assertRaises(KeyError, mysite.siteinfo.__getitem__, not_exists)
        self.assertNotIn(not_exists, mysite.siteinfo)
        self.assertEqual(len(mysite.siteinfo.get(not_exists)), 0)
        self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists)))
        if sys.version_info[0] == 2:
            self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).iteritems()))
            self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).itervalues()))
            self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).iterkeys()))
        self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).items()))
        self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).values()))
        self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).keys()))


class TestSiteLoadRevisions(TestCase):

    """Test cases for Site.loadrevision() method."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    # Implemented without setUpClass(cls) and global variables as objects
    # were not completely disposed and recreated but retained 'memory'
    def setUp(self):
        super(TestSiteLoadRevisions, self).setUp()
        self.mysite = self.get_site()
        self.mainpage = pywikibot.Page(pywikibot.Link("Main Page", self.mysite))

    def testLoadRevisions_basic(self):
        """Test the site.loadrevisions() method"""
        self.mysite.loadrevisions(self.mainpage, total=15)
        self.assertTrue(hasattr(self.mainpage, "_revid"))
        self.assertTrue(hasattr(self.mainpage, "_revisions"))
        self.assertIn(self.mainpage._revid, self.mainpage._revisions)
        self.assertEqual(len(self.mainpage._revisions), 15)
        self.assertEqual(self.mainpage._text, None)

    def testLoadRevisions_getText(self):
        """Test the site.loadrevisions() method with getText=True"""
        self.mysite.loadrevisions(self.mainpage, getText=True, total=5)
        self.assertGreater(len(self.mainpage._text), 0)

    def testLoadRevisions_revids(self):
        """Test the site.loadrevisions() method, listing based on revid."""
        # revids as list of int
        self.mysite.loadrevisions(self.mainpage, revids=[139992, 139993])
        self.assertTrue(all(rev in self.mainpage._revisions for rev in [139992, 139993]))
        # revids as list of str
        self.mysite.loadrevisions(self.mainpage, revids=['139994', '139995'])
        self.assertTrue(all(rev in self.mainpage._revisions for rev in [139994, 139995]))
        # revids as int
        self.mysite.loadrevisions(self.mainpage, revids=140000)
        self.assertIn(140000, self.mainpage._revisions)
        # revids as str
        self.mysite.loadrevisions(self.mainpage, revids='140001')
        self.assertIn(140001, self.mainpage._revisions)
        # revids belonging to a different page raises Exception
        self.assertRaises(pywikibot.Error, self.mysite.loadrevisions,
                          self.mainpage, revids=130000)

    def testLoadRevisions_querycontinue(self):
        """Test the site.loadrevisions() method with query-continue"""
        self.mysite.loadrevisions(self.mainpage, step=5, total=12)
        self.assertEqual(len(self.mainpage._revisions), 12)

    def testLoadRevisions_revdir(self):
        """Test the site.loadrevisions() method with rvdir=True"""
        self.mysite.loadrevisions(self.mainpage, rvdir=True, total=15)
        self.assertEqual(len(self.mainpage._revisions), 15)

    def testLoadRevisions_timestamp(self):
        """Test the site.loadrevisions() method, listing based on timestamp."""
        self.mysite.loadrevisions(self.mainpage, rvdir=True, total=15)
        self.assertEqual(len(self.mainpage._revisions), 15)
        revs = self.mainpage._revisions
        timestamps = [str(revs[rev].timestamp) for rev in revs]
        self.assertTrue(all(ts < "2002-01-31T00:00:00Z" for ts in timestamps))

        # Retrieve oldest revisions; listing based on timestamp.
        # Raises "loadrevisions: starttime > endtime with rvdir=True"
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=True,
                          starttime="2002-02-01T00:00:00Z", endtime="2002-01-01T00:00:00Z")

        # Retrieve newest revisions; listing based on timestamp.
        # Raises "loadrevisions: endtime > starttime with rvdir=False"
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=False,
                          starttime="2002-01-01T00:00:00Z", endtime="2002-02-01T000:00:00Z")

    def testLoadRevisions_rev_id(self):
        """Test the site.loadrevisions() method, listing based on rev_id."""
        self.mysite.loadrevisions(self.mainpage, rvdir=True, total=15)
        self.assertEqual(len(self.mainpage._revisions), 15)
        revs = self.mainpage._revisions
        self.assertTrue(all(139900 <= rev <= 140100 for rev in revs))

        # Retrieve oldest revisions; listing based on revid.
        # Raises "loadrevisions: startid > endid with rvdir=True"
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=True,
                          startid="200000", endid="100000")

        # Retrieve newest revisions; listing based on revid.
        # Raises "loadrevisions: endid > startid with rvdir=False
        self.assertRaises(ValueError, self.mysite.loadrevisions,
                          self.mainpage, rvdir=False,
                          startid="100000", endid="200000")

    def testLoadRevisions_user(self):
        """Test the site.loadrevisions() method, filtering by user."""
        # Only list revisions made by this user.
        self.mainpage._revisions = {}
        self.mysite.loadrevisions(self.mainpage, rvdir=True,
                                  user="Magnus Manske")
        revs = self.mainpage._revisions
        self.assertTrue(all(revs[rev].user == "Magnus Manske" for rev in revs))

    def testLoadRevisions_excludeuser(self):
        """Test the site.loadrevisions() method, excluding user."""
        # Do not list revisions made by this user.
        self.mainpage._revisions = {}
        self.mysite.loadrevisions(self.mainpage, rvdir=True,
                                  excludeuser="Magnus Manske")
        revs = self.mainpage._revisions
        self.assertFalse(any(revs[rev].user == "Magnus Manske" for rev in revs))

        # TODO test other optional arguments


class TestCommonsSite(TestCase):

    """Test cases for Site methods on Commons."""

    family = "commons"
    code = "commons"

    cached = True

    def testInterWikiForward(self):
        self.site = self.get_site()
        self.mainpage = pywikibot.Page(pywikibot.Link("Main Page", self.site))
        # test pagelanglinks on commons,
        # which forwards interwikis to wikipedia
        ll = next(self.site.pagelanglinks(self.mainpage))
        self.assertIsInstance(ll, pywikibot.Link)
        self.assertEqual(ll.site.family.name, 'wikipedia')


class TestWiktionarySite(TestCase):

    family = 'wiktionary'
    code = 'en'

    cached = True

    def testNamespaceCase(self):
        site = self.get_site()

        main_namespace = site.namespaces()[0]
        self.assertEqual(main_namespace.case, 'case-sensitive')
        user_namespace = site.namespaces()[2]
        self.assertEqual(user_namespace.case, 'first-letter')


class TestNonEnglishWikipediaSite(TestCase):

    family = 'wikipedia'
    code = 'nn'

    cached = True

    def testNamespaceAliases(self):
        site = self.get_site()

        namespaces = site.namespaces()
        image_namespace = namespaces[6]
        self.assertEqual(image_namespace.custom_name, 'Fil')
        self.assertEqual(image_namespace.canonical_name, 'File')
        self.assertEqual(str(image_namespace), ':File:')
        self.assertEqual(image_namespace.custom_prefix(), ':Fil:')
        self.assertEqual(image_namespace.canonical_prefix(), ':File:')
        self.assertEqual(image_namespace.aliases, ['Image'])
        self.assertEqual(len(image_namespace), 3)

        self.assertEqual(len(namespaces[1].aliases), 0)
        self.assertEqual(len(namespaces[4].aliases), 1)
        self.assertEqual(namespaces[4].aliases[0], 'WP')
        self.assertIn('WP', namespaces[4])


class TestUploadEnabledSite(TestCase):

    sites = {
        'wikidatatest': {
            'family': 'wikidata',
            'code': 'test',
        },
        'wikipediatest': {
            'family': 'wikipedia',
            'code': 'test',
        }
    }

    def test_is_uploaddisabled_wp(self):
        site = self.get_site('wikipediatest')
        self.assertFalse(site.is_uploaddisabled())

    def test_is_uploaddisabled_wd(self):
        site = self.get_site('wikidatatest')
        self.assertTrue(site.is_uploaddisabled())


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
