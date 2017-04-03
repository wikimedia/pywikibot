# -*- coding: utf-8 -*-
"""Tests for the page module."""
#
# (C) Pywikibot team, 2008-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals


__version__ = '$Id$'


import pickle
import re
try:
    import unittest.mock as mock
except ImportError:
    import mock

import pywikibot
import pywikibot.page

from pywikibot import config
from pywikibot import InvalidTitle

from pywikibot.tools import (
    MediaWikiVersion,
    PY2,
    StringTypes as basestring,
    UnicodeType as unicode,
)

from tests.aspects import (
    unittest, TestCase, DefaultSiteTestCase, SiteAttributeTestCase,
    DefaultDrySiteTestCase, DeprecationTestCase,
)


EMPTY_TITLE_RE = r'Title must be specified and not empty if source is a Site\.'
INVALID_TITLE_RE = r'The link does not contain a page title'
NO_PAGE_RE = r"doesn't exist\."


class TestLinkObject(SiteAttributeTestCase):

    """Test cases for Link objects."""

    sites = {
        'enwiki': {
            'family': 'wikipedia',
            'code': 'en',
        },
        'frwiki': {
            'family': 'wikipedia',
            'code': 'fr',
        },
        'itwikt': {
            'family': 'wiktionary',
            'code': 'it',
        },
        'enws': {
            'family': 'wikisource',
            'code': 'en',
        },
        'itws': {
            'family': 'wikisource',
            'code': 'it',
        },
    }

    cached = True

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
        """Test that Link() normalizes namespace names."""
        for num in self.namespaces:
            for prefix in self.namespaces[num]:
                l = pywikibot.page.Link(prefix + list(self.titles.keys())[0],
                                        self.enwiki)
                self.assertEqual(l.namespace, num)
                # namespace prefixes are case-insensitive
                m = pywikibot.page.Link(prefix.lower() + list(self.titles.keys())[1],
                                        self.enwiki)
                self.assertEqual(m.namespace, num)

    def testTitles(self):
        """Test that Link() normalizes titles."""
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
        """Test hash comparison."""
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

    def test_ns_title(self):
        """Test that title is returned with correct namespace."""
        l1 = pywikibot.page.Link('Indice:Test', source=self.itws)
        self.assertEqual(l1.ns_title(), 'Index:Test')
        self.assertEqual(l1.ns_title(onsite=self.enws), 'Index:Test')

        # wikisource:it kept Autore as canonical name
        l2 = pywikibot.page.Link('Autore:Albert Einstein', source=self.itws)
        self.assertEqual(l2.ns_title(), 'Autore:Albert Einstein')
        self.assertEqual(l2.ns_title(onsite=self.enws), 'Author:Albert Einstein')

        # Translation namespace does not exist on wikisource:it
        l3 = pywikibot.page.Link('Translation:Albert Einstein', source=self.enws)
        self.assertEqual(l3.ns_title(), 'Translation:Albert Einstein')
        self.assertRaisesRegex(pywikibot.Error,
                               'No corresponding namespace found for '
                               'namespace Translation: on wikisource:it.',
                               l3.ns_title,
                               onsite=self.itws)


class TestPageObjectEnglish(TestCase):

    """Test Page Object using English Wikipedia."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def testGeneral(self):
        """Test general features of a page."""
        site = self.get_site()
        mainpage = self.get_mainpage()
        maintalk = mainpage.toggleTalkPage()

        family_name = (site.family.name + ':'
                       if pywikibot.config2.family != site.family.name
                       else u'')
        self.assertEqual(str(mainpage), u"[[%s%s:%s]]"
                                        % (family_name, site.code,
                                           mainpage.title()))
        self.assertLess(mainpage, maintalk)

    def testHelpTitle(self):
        """Test title() method options in Help namespace."""
        site = self.get_site()
        p1 = pywikibot.Page(site, u"Help:Test page#Testing")
        ns_name = u"Help"
        if site.namespaces[12][0] != ns_name:
            ns_name = site.namespaces[12][0]
        self.assertEqual(p1.title(),
                         ns_name + u":Test page#Testing")
        self.assertEqual(p1.title(underscore=True),
                         ns_name + u":Test_page#Testing")
        self.assertEqual(p1.title(withNamespace=False),
                         u"Test page#Testing")
        self.assertEqual(p1.title(withSection=False),
                         ns_name + u":Test page")
        self.assertEqual(p1.title(withNamespace=False, withSection=False),
                         u"Test page")
        self.assertEqual(p1.title(asUrl=True),
                         ns_name + "%3ATest_page%23Testing")
        self.assertEqual(p1.title(asLink=True, insite=site),
                         u"[[" + ns_name + u":Test page#Testing]]")
        self.assertEqual(p1.title(asLink=True, forceInterwiki=True, insite=site),
                         u"[[en:" + ns_name + u":Test page#Testing]]")
        self.assertEqual(p1.title(asLink=True, textlink=True, insite=site),
                         p1.title(asLink=True, textlink=False, insite=site))
        self.assertEqual(p1.title(asLink=True, withNamespace=False, insite=site),
                         u"[[" + ns_name + u":Test page#Testing|Test page]]")
        self.assertEqual(p1.title(asLink=True, forceInterwiki=True,
                                  withNamespace=False, insite=site),
                         u"[[en:" + ns_name + ":Test page#Testing|Test page]]")
        self.assertEqual(p1.title(asLink=True, textlink=True,
                                  withNamespace=False, insite=site),
                         p1.title(asLink=True, textlink=False,
                                  withNamespace=False, insite=site))

    def testFileTitle(self):
        """Test title() method options in File namespace."""
        # also test a page with non-ASCII chars and a different namespace
        site = self.get_site()
        p2 = pywikibot.Page(site, u"File:Jean-Léon Gérôme 003.jpg")
        ns_name = u"File"
        if site.namespaces[6][0] != ns_name:
            ns_name = site.namespaces[6][0]
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

    def test_creation(self):
        """Test Page.oldest_revision."""
        mainpage = self.get_mainpage()
        self.assertEqual(mainpage.oldest_revision.user, 'TwoOneTwo')
        self.assertIsInstance(mainpage.oldest_revision.timestamp, pywikibot.Timestamp)


class TestPageObject(DefaultSiteTestCase):

    """Test Page object."""

    cached = True

    def testSite(self):
        """Test site() method."""
        mainpage = self.get_mainpage()
        self.assertEqual(mainpage.site, self.site)

    def testNamespace(self):
        """Test namespace() method."""
        mainpage = self.get_mainpage()
        maintalk = mainpage.toggleTalkPage()

        if u':' not in mainpage.title():
            self.assertEqual(mainpage.namespace(), 0)
        self.assertEqual(maintalk.namespace(), mainpage.namespace() + 1)

        badpage = self.get_missing_article()
        self.assertEqual(badpage.namespace(), 0)

    def testBasePageConstructor(self):
        """Test BasePage constructor."""
        site = self.get_site()

        # Should not raise an error as the constructor only requires
        # the site parameter.
        # Empty string or None as title raises error.
        page = pywikibot.page.BasePage(site)
        self.assertRaisesRegex(InvalidTitle, INVALID_TITLE_RE, page.title)
        page = pywikibot.page.BasePage(site, title=u'')
        self.assertRaisesRegex(InvalidTitle, INVALID_TITLE_RE, page.title)
        self.assertRaisesRegex(ValueError, 'Title cannot be None.',
                               pywikibot.page.BasePage, site, title=None)

    def testPageConstructor(self):
        """Test Page constructor."""
        site = self.get_site()
        mainpage = self.get_mainpage()

        # Test that Page() needs a title when Site is used as source.
        self.assertRaisesRegex(ValueError, EMPTY_TITLE_RE,
                               pywikibot.Page, site)
        self.assertRaisesRegex(ValueError, EMPTY_TITLE_RE,
                               pywikibot.Page, site, '')

        # Test Page as source.
        p1 = pywikibot.Page(mainpage)
        self.assertEqual(p1, mainpage)

        # Test not valid source.
        self.assertRaisesRegex(pywikibot.Error,
                               'Invalid argument type \'<\\w* \'\\w*\'>\' in '
                               'Page constructor: dummy',
                               pywikibot.Page, 'dummy')

    def testTitle(self):
        """Test title() method options in article namespace."""
        # at last test article namespace
        site = self.get_site()
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
                         u"[[" + site.code + u":Test page|Test page]]")

    def testSection(self):
        """Test section() method."""
        # use same pages as in previous test
        site = self.get_site()
        p1 = pywikibot.Page(site, u"Help:Test page#Testing")
        p2 = pywikibot.Page(site, u"File:Jean-Léon Gérôme 003.jpg")
        self.assertEqual(p1.section(), u"Testing")
        self.assertEqual(p2.section(), None)

    def testIsTalkPage(self):
        """Test isTalkPage() method."""
        site = self.get_site()
        p1 = pywikibot.Page(site, u"First page")
        p2 = pywikibot.Page(site, u"Talk:First page")
        p3 = pywikibot.Page(site, u"User:Second page")
        p4 = pywikibot.Page(site, u"User talk:Second page")
        self.assertEqual(p1.isTalkPage(), False)
        self.assertEqual(p2.isTalkPage(), True)
        self.assertEqual(p3.isTalkPage(), False)
        self.assertEqual(p4.isTalkPage(), True)

    def testIsCategory(self):
        """Test is_categorypage method."""
        site = self.get_site()
        p1 = pywikibot.Page(site, u"First page")
        p2 = pywikibot.Page(site, u"Category:Second page")
        p3 = pywikibot.Page(site, u"Category talk:Second page")
        self.assertEqual(p1.is_categorypage(), False)
        self.assertEqual(p2.is_categorypage(), True)
        self.assertEqual(p3.is_categorypage(), False)

    def testIsFile(self):
        """Test C{Page.is_filepage} check."""
        site = self.get_site()
        p1 = pywikibot.Page(site, u"First page")
        p2 = pywikibot.Page(site, u"File:Second page")
        p3 = pywikibot.Page(site, u"Image talk:Second page")
        self.assertEqual(p1.is_filepage(), False)
        self.assertEqual(p2.is_filepage(), True)
        self.assertEqual(p3.is_filepage(), False)

    def testApiMethods(self):
        """Test various methods that rely on API."""
        mainpage = self.get_mainpage()
        # since there is no way to predict what data the wiki will return,
        # we only check that the returned objects are of correct type.
        self.assertIsInstance(mainpage.get(), unicode)
        self.assertIsInstance(mainpage.latestRevision(), int)
        self.assertIsInstance(mainpage.userName(), unicode)
        self.assertIsInstance(mainpage.isIpEdit(), bool)
        self.assertIsInstance(mainpage.exists(), bool)
        self.assertIsInstance(mainpage.isRedirectPage(), bool)
        self.assertIsInstance(mainpage.isEmpty(), bool)
        self.assertIsInstance(mainpage.isDisambig(), bool)
        self.assertIsInstance(mainpage.canBeEdited(), bool)
        self.assertIsInstance(mainpage.botMayEdit(), bool)
        self.assertIsInstance(mainpage.editTime(), pywikibot.Timestamp)
        self.assertIsInstance(mainpage.permalink(), basestring)

    def test_talk_page(self):
        """Test various methods that rely on API: talk page."""
        mainpage = self.get_mainpage()
        maintalk = mainpage.toggleTalkPage()
        if not maintalk.exists():
            raise unittest.SkipTest("No talk page for %s's main page"
                                    % self.get_site())
        self.assertIsInstance(maintalk.get(), unicode)
        self.assertEqual(mainpage.toggleTalkPage(), maintalk)
        self.assertEqual(maintalk.toggleTalkPage(), mainpage)

    def test_bad_page(self):
        """Test various methods that rely on API: bad page."""
        badpage = self.get_missing_article()
        self.assertRaisesRegex(pywikibot.NoPage, NO_PAGE_RE, badpage.get)

    def testIsDisambig(self):
        """Test the integration with Extension:Disambiguator."""
        site = self.get_site()
        if not site.has_extension('Disambiguator'):
            raise unittest.SkipTest('Disambiguator extension not loaded on test site')
        pg = pywikibot.Page(site, 'Random')
        pg._pageprops = set(['disambiguation', ''])
        self.assertTrue(pg.isDisambig())
        pg._pageprops = set()
        self.assertFalse(pg.isDisambig())

    def testReferences(self):
        """Test references to a page."""
        mainpage = self.get_mainpage()
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
        """Test the different types of links from a page."""
        if self.site.family.name in ('wpbeta', 'wsbeta'):
            raise unittest.SkipTest('Test fails on betawiki; T69931; T160308')
        mainpage = self.get_mainpage()
        for p in mainpage.linkedPages():
            self.assertIsInstance(p, pywikibot.Page)
        iw = list(mainpage.interwiki(expand=True))
        for p in iw:
            self.assertIsInstance(p, pywikibot.Link)
        for p2 in mainpage.interwiki(expand=False):
            self.assertIsInstance(p2, pywikibot.Link)
            self.assertIn(p2, iw)
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
        """Test the ability to pickle the page."""
        mainpage = self.get_mainpage()
        mainpage_str = pickle.dumps(mainpage, protocol=config.pickle_protocol)
        mainpage_unpickled = pickle.loads(mainpage_str)
        self.assertEqual(mainpage, mainpage_unpickled)

    def test_redirect(self):
        """Test that the redirect option is set correctly."""
        site = self.get_site()
        for page in site.allpages(filterredir=True, total=1):
            break
        else:
            raise unittest.SkipTest('No redirect pages on site {0!r}'.format(site))
        # This page is already initialised
        self.assertTrue(hasattr(page, '_isredir'))
        # call api.update_page without prop=info
        del page._isredir
        page.isDisambig()
        self.assertTrue(page.isRedirectPage())

        page_copy = pywikibot.Page(site, page.title())
        self.assertFalse(hasattr(page_copy, '_isredir'))
        page_copy.isDisambig()
        self.assertTrue(page_copy.isRedirectPage())

    def test_depth(self):
        """Test page depth calculation."""
        site = self.get_site()
        page_d0 = pywikibot.Page(site, '/home/test/')
        if site.namespaces[0].subpages:
            self.assertEqual(page_d0.depth, 3)
        else:
            self.assertEqual(page_d0.depth, 0)

        page_user_d0 = pywikibot.Page(site, 'User:Sn1per')
        self.assertEqual(page_user_d0.depth, 0)

        page_d3 = pywikibot.Page(site, 'User:Sn1per/ProtectTest1/test/test')
        self.assertEqual(page_d3.depth, 3)


class TestPageDeprecation(DefaultSiteTestCase, DeprecationTestCase):

    """Test deprecation of Page attributes."""

    def test_creator(self):
        """Test getCreator."""
        mainpage = self.get_mainpage()
        creator = mainpage.getCreator()
        self.assertEqual(creator,
                         (mainpage.oldest_revision.user,
                          mainpage.oldest_revision.timestamp.isoformat()))
        self.assertIsInstance(creator[0], unicode)
        self.assertIsInstance(creator[1], unicode)
        self.assertDeprecation()

        self._reset_messages()
        if MediaWikiVersion(self.site.version()) >= MediaWikiVersion('1.16'):
            self.assertIsInstance(mainpage.previous_revision_id, int)
            self.assertEqual(mainpage.previous_revision_id,
                             mainpage.latest_revision.parent_id)
            self.assertDeprecation()


class TestPageBaseUnicode(DefaultDrySiteTestCase):

    """Base class for tests requring a page using a unicode title."""

    @classmethod
    def setUpClass(cls):
        """Initialize page instance."""
        super(TestPageBaseUnicode, cls).setUpClass()
        cls.page = pywikibot.Page(cls.site, 'Ō')


class TestPageGetFileHistory(DefaultDrySiteTestCase):

    """Test the get_file_history method of the FilePage class."""

    def test_get_file_history_cache(self):
        """Test the cache mechanism of get_file_history."""
        with mock.patch.object(self.site, 'loadimageinfo', autospec=True):
            page = pywikibot.FilePage(self.site, 'File:Foo.jpg')
            _file_revisions = page.get_file_history()
            # On the first call the history is loaded via API
            self.assertEqual(_file_revisions, {})
            # Fill the cache
            _file_revisions['foo'] = 'bar'
            # On the second call page._file_revisions is returned
            self.assertEqual(page.get_file_history(), {'foo': 'bar'})
            self.site.loadimageinfo.assert_called_once_with(page, history=True)


class TestPageRepr(TestPageBaseUnicode):

    """Test for Page's repr implementation."""

    def setUp(self):
        """Force the console encoding to UTF-8."""
        super(TestPageRepr, self).setUp()
        self._old_encoding = config.console_encoding
        config.console_encoding = 'utf8'

    def tearDown(self):
        """Restore the original console encoding."""
        config.console_encoding = self._old_encoding
        super(TestPageRepr, self).tearDown()

    def test_mainpage_type(self):
        u"""Test the return type of repr(Page(<main page>)) is str."""
        mainpage = self.get_mainpage()
        self.assertIsInstance(repr(mainpage), str)

    def test_unicode_type(self):
        """Test the return type of repr(Page(u'<non-ascii>')) is str."""
        page = pywikibot.Page(self.get_site(), u'Ō')
        self.assertIsInstance(repr(page), str)

    @unittest.skipIf(not PY2, 'Python 2 specific test')
    def test_unicode_value(self):
        """Test repr(Page(u'<non-ascii>')) is represented simply as utf8."""
        page = pywikibot.Page(self.get_site(), u'Ō')
        self.assertEqual(repr(page), b'Page(\xc5\x8c)')

    @unittest.skipIf(not PY2, 'Python 2 specific test')
    def test_unicode_percent_r_failure(self):
        """Test u'{x!r}'.format(Page(u'<non-ascii>')) raises exception on Python 2."""
        # This raises an exception on Python 2, but passes on Python 3
        page = pywikibot.Page(self.get_site(), u'Ō')
        self.assertRaisesRegex(UnicodeDecodeError, '', unicode.format, u'{0!r}', page)

    @unittest.skipIf(PY2, 'Python 3+ specific test')
    def test_unicode_value_py3(self):
        """Test to capture actual Python 3 result pre unicode_literals."""
        self.assertEqual(repr(self.page), "Page('Ō')")
        self.assertEqual('%r' % self.page, "Page('Ō')")
        self.assertEqual('{0!r}'.format(self.page), "Page('Ō')")

    @unittest.skipIf(not PY2, 'Python 2 specific test')
    @unittest.expectedFailure
    def test_ASCII_compatible(self):
        """Test that repr returns ASCII compatible bytes in Python 2."""
        page = pywikibot.Page(self.site, 'ä')
        # Bug T95809, the repr in Python 2 should be decodable as ASCII
        repr(page).decode('ascii')


class TestPageReprASCII(TestPageBaseUnicode):

    """Test for Page's repr implementation when using ASCII encoding."""

    def setUp(self):
        """Patch the current console encoding to ASCII."""
        super(TestPageReprASCII, self).setUp()
        self._old_encoding = config.console_encoding
        config.console_encoding = 'ascii'

    def tearDown(self):
        """Restore the original console encoding."""
        config.console_encoding = self._old_encoding
        super(TestPageReprASCII, self).tearDown()

    @unittest.skipIf(not PY2, 'Python 2 specific test')
    def test_incapable_encoding(self):
        """Test that repr still works even if the console encoding does not."""
        self.assertEqual(repr(self.page), b'Page(\\u014c)')


class TestPageBotMayEdit(TestCase):

    """Test Page.botMayEdit() method."""

    family = 'wikipedia'
    code = 'en'

    cached = True
    user = True

    @mock.patch.object(config, 'ignore_bot_templates', False)
    def test_bot_may_edit_general(self):
        """Test that bot is allowed to edit."""
        site = self.get_site()
        user = site.user()

        page = pywikibot.Page(site, 'not_existent_page_for_pywikibot_tests')
        if page.exists():
            raise unittest.SkipTest(
                "Page %s exists! Change page name in tests/page_tests.py"
                % page.title())

        # Ban all compliant bots (shortcut).
        page.text = '{{nobots}}'
        page._templates = [pywikibot.Page(site, 'Template:Nobots')]
        self.assertFalse(page.botMayEdit())

        # Ban all compliant bots not in the list, syntax for de wp.
        page.text = '{{nobots|HagermanBot,Werdnabot}}'
        self.assertTrue(page.botMayEdit(),
                        u'%s: %s but user=%s'
                        % (page.text, page.botMayEdit(), user))

        # Ban all compliant bots not in the list, syntax for de wp.
        page.text = '{{nobots|%s, HagermanBot,Werdnabot}}' % user
        self.assertFalse(page.botMayEdit(),
                         u'%s: %s but user=%s'
                         % (page.text, page.botMayEdit(), user))

        # Ban all bots, syntax for de wp.
        page.text = '{{nobots|all}}'
        self.assertFalse(page.botMayEdit(),
                         u'%s: %s but user=%s'
                         % (page.text, page.botMayEdit(), user))

        # Allow all bots (shortcut).
        page.text = '{{bots}}'
        page._templates = [pywikibot.Page(site, 'Template:Bots')]
        self.assertTrue(page.botMayEdit())

        # Ban all compliant bots not in the list.
        page.text = '{{bots|allow=HagermanBot,Werdnabot}}'
        self.assertFalse(page.botMayEdit(),
                         u'%s: %s but user=%s'
                         % (page.text, page.botMayEdit(), user))

        # Ban all compliant bots in the list.
        page.text = '{{bots|deny=HagermanBot,Werdnabot}}'
        self.assertTrue(page.botMayEdit(),
                        u'%s: %s but user=%s'
                        % (page.text, page.botMayEdit(), user))

        # Ban all compliant bots not in the list.
        page.text = '{{bots|allow=%s, HagermanBot}}' % user
        self.assertTrue(page.botMayEdit(),
                        u'%s: %s but user=%s'
                        % (page.text, page.botMayEdit(), user))

        # Ban all compliant bots in the list.
        page.text = '{{bots|deny=%s, HagermanBot}}' % user
        self.assertFalse(page.botMayEdit(),
                         u'%s: %s but user=%s'
                         % (page.text, page.botMayEdit(), user))

        # Allow all bots.
        page.text = '{{bots|allow=all}}'
        self.assertTrue(page.botMayEdit(),
                        u'%s: %s but user=%s'
                        % (page.text, page.botMayEdit(), user))

        # Ban all compliant bots.
        page.text = '{{bots|allow=none}}'
        self.assertFalse(page.botMayEdit(),
                         u'%s: %s but user=%s'
                         % (page.text, page.botMayEdit(), user))

        # Ban all compliant bots.
        page.text = '{{bots|deny=all}}'
        self.assertFalse(page.botMayEdit(),
                         u'%s: %s but user=%s'
                         % (page.text, page.botMayEdit(), user))

        # Allow all bots.
        page.text = '{{bots|deny=none}}'
        self.assertTrue(page.botMayEdit(),
                        u'%s: %s but user=%s'
                        % (page.text, page.botMayEdit(), user))


class TestPageHistory(DefaultSiteTestCase):

    """Test history related functionality."""

    cached = True

    def test_revisions(self):
        """Test Page.revisions()."""
        mp = self.get_mainpage()
        revs = mp.revisions()
        revs = iter(revs)  # implicit assertion
        revs = list(revs)
        self.assertGreater(len(revs), 1)

    def test_contributors(self):
        """Test Page.contributors()."""
        mp = self.get_mainpage()
        cnt = mp.contributors()
        self.assertIsInstance(cnt, dict)
        self.assertGreater(len(cnt), 1)

    def test_revision_count(self):
        """Test Page.edit_count()."""
        mp = self.get_mainpage()
        rev_count = len(list(mp.revisions()))
        self.assertEqual(rev_count, mp.revision_count())
        cnt = mp.contributors()
        self.assertEqual(rev_count, sum(cnt.values()))

        top_two = cnt.most_common(2)
        self.assertIsInstance(top_two, list)
        self.assertEqual(len(top_two), 2)
        self.assertIsInstance(top_two[0], tuple)
        self.assertIsInstance(top_two[0][0], basestring)
        self.assertIsInstance(top_two[0][1], int)
        top_two_usernames = set([top_two[0][0], top_two[1][0]])
        self.assertEqual(len(top_two_usernames), 2)
        top_two_counts = ([top_two[0][1], top_two[1][1]])
        top_two_edit_count = mp.revision_count(top_two_usernames)
        self.assertIsInstance(top_two_edit_count, int)
        self.assertEqual(top_two_edit_count, sum(top_two_counts))


class TestPageRedirects(TestCase):

    """
    Test redirects.

    This is using the pages 'User:Legoktm/R1', 'User:Legoktm/R2' and
    'User:Legoktm/R3' on the English Wikipedia. 'R1' is redirecting to 'R2',
    'R2' is a normal page and 'R3' does not exist.
    """

    family = 'wikipedia'
    code = 'en'

    cached = True

    def testIsRedirect(self):
        """Test C{Page.isRedirectPage()} and C{Page.getRedirectTarget}."""
        site = self.get_site()
        p1 = pywikibot.Page(site, u'User:Legoktm/R1')
        p2 = pywikibot.Page(site, u'User:Legoktm/R2')
        self.assertTrue(p1.isRedirectPage())
        self.assertEqual(p1.getRedirectTarget(), p2)

    def testPageGet(self):
        """Test C{Page.get()} on different types of pages."""
        site = self.get_site()
        p1 = pywikibot.Page(site, u'User:Legoktm/R2')
        p2 = pywikibot.Page(site, u'User:Legoktm/R1')
        p3 = pywikibot.Page(site, u'User:Legoktm/R3')

        text = u'This page is used in the [[mw:Manual:Pywikipediabot]] testing suite.'
        self.assertEqual(p1.get(), text)
        self.assertRaisesRegex(pywikibot.exceptions.IsRedirectPage,
                               r'{0} is a redirect page\.'
                               .format(re.escape(str(p2))), p2.get)
        self.assertRaisesRegex(pywikibot.exceptions.NoPage, NO_PAGE_RE, p3.get)

    def test_set_redirect_target(self):
        """Test set_redirect_target method."""
        # R1 redirects to R2 and R3 doesn't exist.
        site = self.get_site()
        p1 = pywikibot.Page(site, u'User:Legoktm/R2')
        p2 = pywikibot.Page(site, u'User:Legoktm/R1')
        p3 = pywikibot.Page(site, u'User:Legoktm/R3')

        text = p2.get(get_redirect=True)
        self.assertRaisesRegex(pywikibot.exceptions.IsNotRedirectPage,
                               r'{0} is not a redirect page\.'
                               .format(re.escape(str(p1))),
                               p1.set_redirect_target, p2)
        self.assertRaisesRegex(pywikibot.exceptions.NoPage, NO_PAGE_RE,
                               p3.set_redirect_target, p2)
        p2.set_redirect_target(p1, save=False)
        self.assertEqual(text, p2.get(get_redirect=True))


class TestPageUserAction(DefaultSiteTestCase):

    """Test page user actions."""

    user = True

    def test_purge(self):
        """Test purging the mainpage."""
        mainpage = self.get_mainpage()
        self.assertIsInstance(mainpage.purge(), bool)
        self.assertEqual(mainpage.purge(), mainpage.purge(forcelinkupdate=None))

    def test_watch(self):
        """Test Page.watch, with and without unwatch enabled."""
        # Note: this test uses the userpage, so that it is unwatched and
        # therefore is not listed by script_tests test_watchlist_simulate.
        userpage = self.get_userpage()
        rv = userpage.watch()
        self.assertIsInstance(rv, bool)
        self.assertTrue(rv)
        rv = userpage.watch(unwatch=True)
        self.assertIsInstance(rv, bool)
        self.assertTrue(rv)


class TestPageDelete(TestCase):

    """Test page delete / undelete actions."""

    family = 'test'
    code = 'test'

    write = True
    sysop = True

    def test_delete(self):
        """Test the site.delete and site.undelete method."""
        site = self.get_site()
        p = pywikibot.Page(site, u'User:Unicodesnowman/DeleteTest')
        # Ensure the page exists
        p.text = 'pywikibot unit test page'
        p.save('#redirect[[unit test]]', botflag=True)
        self.assertEqual(p.isRedirectPage(), True)
        # Test deletion
        p.delete(reason='pywikibot unit test', prompt=False, mark=False)
        self.assertEqual(p._pageid, 0)
        self.assertEqual(p.isRedirectPage(), False)
        self.assertRaisesRegex(pywikibot.NoPage, NO_PAGE_RE, p.get, force=True)
        # Test undeleting last two revisions
        del_revs = list(p.loadDeletedRevisions())
        revid = p.getDeletedRevision(del_revs[-1])[u'revid']
        p.markDeletedRevision(del_revs[-1])
        p.markDeletedRevision(del_revs[-2])
        self.assertRaisesRegex(ValueError, 'is not a deleted revision',
                               p.markDeletedRevision, 123)
        p.undelete(reason='pywikibot unit test')
        revs = list(p.revisions())
        self.assertEqual(len(revs), 2)
        self.assertEqual(revs[1].revid, revid)


class TestApplicablePageProtections(TestCase):

    """Test applicable restriction types."""

    family = 'test'
    code = 'test'

    def test_applicable_protections(self):
        """Test Page.applicable_protections."""
        site = self.get_site()
        p1 = pywikibot.Page(site, u'User:Unicodesnowman/NonexistentPage')
        p2 = pywikibot.Page(site, u'User:Unicodesnowman/ProtectTest')
        p3 = pywikibot.Page(site, u'File:Wiki.png')

        # from the API, since 1.25wmf14
        pp1 = p1.applicable_protections()
        pp2 = p2.applicable_protections()
        pp3 = p3.applicable_protections()

        self.assertEqual(pp1, set(['create']))
        self.assertIn('edit', pp2)
        self.assertNotIn('create', pp2)
        self.assertNotIn('upload', pp2)
        self.assertIn('upload', pp3)

        # inferred
        site.version = lambda: '1.24'
        self.assertEqual(pp1, p1.applicable_protections())
        self.assertEqual(pp2, p2.applicable_protections())
        self.assertEqual(pp3, p3.applicable_protections())


class TestPageProtect(TestCase):

    """Test page protect / unprotect actions."""

    family = 'test'
    code = 'test'

    write = True
    sysop = True

    def test_protect(self):
        """Test Page.protect."""
        site = self.get_site()
        p1 = pywikibot.Page(site, u'User:Unicodesnowman/ProtectTest')

        p1.protect(protections={'edit': 'sysop', 'move': 'autoconfirmed'},
                   reason=u'Pywikibot unit test')
        self.assertEqual(p1.protection(),
                         {u'edit': (u'sysop', u'infinity'),
                          u'move': (u'autoconfirmed', u'infinity')})

        p1.protect(protections={'edit': '', 'move': ''},
                   reason=u'Pywikibot unit test')
        self.assertEqual(p1.protection(), {})

    def test_protect_alt(self):
        """Test of Page.protect that works around T78522."""
        site = self.get_site()
        p1 = pywikibot.Page(site, u'User:Unicodesnowman/ProtectTest')

        p1.protect(protections={'edit': 'sysop', 'move': 'autoconfirmed'},
                   reason=u'Pywikibot unit test')
        self.assertEqual(p1.protection(),
                         {u'edit': (u'sysop', u'infinity'),
                          u'move': (u'autoconfirmed', u'infinity')})
        # workaround
        p1 = pywikibot.Page(site, u'User:Unicodesnowman/ProtectTest')
        p1.protect(protections={'edit': '', 'move': ''},
                   reason=u'Pywikibot unit test')
        self.assertEqual(p1.protection(), {})


class HtmlEntity(TestCase):

    """Test that HTML entities are correctly decoded."""

    net = False

    def test_no_entities(self):
        """Test that text is left unchanged."""
        self.assertEqual(pywikibot.page.html2unicode('foobar'), 'foobar')
        self.assertEqual(pywikibot.page.html2unicode(' '), ' ')

    def test_valid_entities(self):
        """Test valid entities."""
        self.assertEqual(pywikibot.page.html2unicode('A&amp;O'), 'A&O')
        self.assertEqual(pywikibot.page.html2unicode('&#x70;&#x79;'), 'py')
        self.assertEqual(pywikibot.page.html2unicode('&#x10000;'), u'\U00010000')
        self.assertEqual(pywikibot.page.html2unicode('&#x70;&amp;&#x79;'), 'p&y')
        self.assertEqual(pywikibot.page.html2unicode('&#128;'), '€')

    def test_ignore_entities(self):
        """Test ignore entities."""
        self.assertEqual(pywikibot.page.html2unicode('A&amp;O', [38]), 'A&amp;O')
        self.assertEqual(pywikibot.page.html2unicode('A&#38;O', [38]), 'A&#38;O')
        self.assertEqual(pywikibot.page.html2unicode('A&#x26;O', [38]), 'A&#x26;O')
        self.assertEqual(pywikibot.page.html2unicode('A&amp;O', [37]), 'A&O')
        self.assertEqual(pywikibot.page.html2unicode('&#128;', [128]), '&#128;')
        self.assertEqual(pywikibot.page.html2unicode('&#128;', [8364]), '&#128;')
        self.assertEqual(pywikibot.page.html2unicode('&#129;&#141;&#157'),
                         '&#129;&#141;&#157')

    def test_recursive_entities(self):
        """Test recursive entities."""
        self.assertEqual(pywikibot.page.html2unicode('A&amp;amp;O'), 'A&amp;O')

    def test_invalid_entities(self):
        """Test texts with invalid entities."""
        self.assertEqual(pywikibot.page.html2unicode('A&notaname;O'), 'A&notaname;O')
        self.assertEqual(pywikibot.page.html2unicode('A&#7f;O'), 'A&#7f;O')
        self.assertEqual(pywikibot.page.html2unicode('&#7f'), '&#7f')
        self.assertEqual(pywikibot.page.html2unicode('&#x70&#x79;'), '&#x70y')


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
