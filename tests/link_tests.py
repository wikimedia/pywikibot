# -*- coding: utf-8  -*-
#
# (C) Pywikipedia bot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import os
import pywikibot
from pywikibot import config2 as config
from pywikibot.page import Link
from tests.aspects import unittest, TestCase

show_failures = os.environ.get('PYWIKIBOT2_TEST_SHOW_FAILURE', '0') == '1'

# ---- The first set of tests are explicit links, starting with a ':'.


class TestPartiallyQualifiedExplicitLinkSameSiteParser(TestCase):

    family = 'wikipedia'
    code = 'en'
    cached = True

    def setUp(self):
        self.old_lang = config.mylang
        self.old_family = config.family

    def tearDown(self):
        config.mylang = self.old_lang
        config.family = self.old_family

    def test_partially_qualified_NS0_code(self):
        """Test ':wikipedia:Main Page' on enwp is namespace 4."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 4)

    def test_partially_qualified_NS1_code(self):
        """Test ':wikipedia:Talk:Main Page' on enwp is namespace 4."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Talk:Main Page')
        self.assertEqual(link.namespace, 4)

    def test_partially_qualified_NS0_family(self):
        """Test ':en:Main Page' on enwp is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_family(self):
        """Test ':en:Talk:Main Page' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestPartiallyQualifiedExplicitLinkDifferentCodeParser(TestCase):

    family = 'wikipedia'
    code = 'en'
    cached = True

    def setUp(self):
        self.old_lang = config.mylang
        self.old_family = config.family

    def tearDown(self):
        config.mylang = self.old_lang
        config.family = self.old_family

    def test_partially_qualified_NS0_family(self):
        """Test ':en:Main Page' on dewp is namespace 0."""
        config.mylang = 'de'
        config.family = 'wikipedia'
        link = Link(':en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_family(self):
        """Test ':en:Talk:Main Page' on dewp is namespace 1."""
        config.mylang = 'de'
        config.family = 'wikipedia'
        link = Link(':en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestPartiallyQualifiedExplicitLinkDifferentFamilyParser(TestCase):

    family = 'wikipedia'
    code = 'en'
    cached = True

    def setUp(self):
        self.old_lang = config.mylang
        self.old_family = config.family

    def tearDown(self):
        config.mylang = self.old_lang
        config.family = self.old_family

    def test_partially_qualified_NS0_code(self):
        """Test ':wikipedia:Main Page' on enws is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link(':wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_code(self):
        """Test ':wikipedia:Talk:Main Page' on enws is ns 1."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link(':wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestFullyQualifiedSameNamespaceFamilyParser(TestCase):

    family = 'wikipedia'
    code = 'en'
    cached = True

    def test_namespace_vs_family(self):
        """Test namespace is selected before family."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':wikipedia:en:Main Page')
        link.parse()
        self.assertEqual(link.title, 'En:Main Page')
        self.assertEqual(link.namespace, 4)

        link = Link(':wikipedia:en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'En:Talk:Main Page')
        self.assertEqual(link.namespace, 4)


class TestFullyQualifiedExplicitLinkSameFamilyParser(TestCase):

    family = 'wikipedia'
    code = 'en'
    cached = True

    def test_fully_qualified_NS0_code(self):
        """Test ':en:wikipedia:Main Page' on enwp is namespace 4."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':en:wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 4)

    def test_fully_qualified_NS1_code(self):
        """Test ':en:wikipedia:Talk:Main Page' on enwp is namespace 4."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':en:wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Talk:Main Page')
        self.assertEqual(link.namespace, 4)


class TestFullyQualifiedExplicitLinkDifferentFamilyParser(TestCase):

    sites = {
        'enws': {
            'family': 'wikisource',
            'code': 'en'
        },
        'enwp': {
            'family': 'wikipedia',
            'code': 'en'
        }
    }
    cached = True

    def test_fully_qualified_NS0_code(self):
        """Test ':en:wikipedia:Main Page' on enws is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link(':en:wikipedia:Main Page')
        if show_failures:
            link.parse()
        else:
            self.assertRaisesRegex(
                pywikibot.Error,
                "Improperly formatted interwiki link ':en:wikipedia:Main Page'",
                link.parse)
        if show_failures:
            self.assertEqual(link.site, self.get_site('enwp'))
        else:
            self.assertEqual(link.site, self.get_site('enws'))
        if show_failures:
            self.assertEqual(link.title, 'Main Page')
            self.assertEqual(link.namespace, 0)
        else:
            try:
                link.title
            except pywikibot.Error as e:
                self.assertEqual(str(e), "Improperly formatted interwiki link ':en:wikipedia:Main Page'")

    def test_fully_qualified_NS1_code(self):
        """Test ':en:wikipedia:Main Page' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link(':en:wikipedia:Talk:Main Page')
        if show_failures:
            link.parse()
        else:
            self.assertRaisesRegex(
                pywikibot.Error,
                "Improperly formatted interwiki link ':en:wikipedia:Talk:Main Page'",
                link.parse)
        if show_failures:
            self.assertEqual(link.site, self.get_site('enwp'))
        else:
            self.assertEqual(link.site, self.get_site('enws'))
        if show_failures:
            self.assertEqual(link.title, 'Main Page')
            self.assertEqual(link.namespace, 1)
        else:
            try:
                link.title
            except pywikibot.Error as e:
                self.assertEqual(str(e), "Improperly formatted interwiki link ':en:wikipedia:Talk:Main Page'")

    def test_fully_qualified_NS0_family(self):
        """Test ':wikipedia:en:Main Page' on enws is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link(':wikipedia:en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_family(self):
        """Test ':wikipedia:en:Talk:Main Page' on enws is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link(':wikipedia:en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestFullyQualifiedExplicitLinkNoLangConfigFamilyParser(TestCase):

    sites = {
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata'
        },
        'enwp': {
            'family': 'wikipedia',
            'code': 'en'
        }
    }
    cached = True

    def test_fully_qualified_NS0_code(self):
        """Test ':en:wikipedia:Main Page' on wikidata is namespace 4."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link(':en:wikipedia:Main Page')
        link.parse()
        if show_failures:
            self.assertEqual(link.site, self.get_site('enwp'))
        else:
            self.assertEqual(link.site, self.get_site('wikidata'))
        if show_failures:
            self.assertEqual(link.title, 'Main Page')
            self.assertEqual(link.namespace, 4)
        else:
            self.assertEqual(link.title, 'En:wikipedia:Main Page')
            self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_code(self):
        """Test ':en:wikipedia:Talk:Main Page' on wikidata is namespace 4."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link(':en:wikipedia:Talk:Main Page')
        link.parse()
        if show_failures:
            self.assertEqual(link.site, self.get_site('enwp'))
        else:
            self.assertEqual(link.site, self.get_site('wikidata'))
        if show_failures:
            self.assertEqual(link.title, 'Talk:Main Page')
            self.assertEqual(link.namespace, 4)
        else:
            self.assertEqual(link.title, 'En:wikipedia:Talk:Main Page')
            self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS0_family(self):
        """Test ':wikipedia:en:Main Page' on wikidata is namespace 0."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link(':wikipedia:en:Main Page')
        if show_failures:
            link.parse()
            self.assertEqual(link.site, self.get_site('enwp'))
            self.assertEqual(link.title, 'Main Page')
            self.assertEqual(link.namespace, 0)
        else:
            self.assertRaisesRegex(
                pywikibot.NoSuchSite,
                'Language wikidata does not exist in family wikipedia',
                link.parse)  # very bad

    def test_fully_qualified_NS1_family(self):
        """Test ':wikipedia:en:Talk:Main Page' on wikidata is namespace 1."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link(':wikipedia:en:Talk:Main Page')
        if show_failures:
            link.parse()
        else:
            self.assertRaisesRegex(
                pywikibot.NoSuchSite,
                'Language wikidata does not exist in family wikipedia',
                link.parse)  # very bad
        if show_failures:
            self.assertEqual(link.site, self.get_site('enwp'))
        else:
            self.assertEqual(link.site, self.get_site('wikidata'))
        if show_failures:
            self.assertEqual(link.title, 'Main Page')
            self.assertEqual(link.namespace, 1)


class TestFullyQualifiedNoLangFamilyExplicitLinkParser(TestCase):

    sites = {
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata'
        },
        'enwp': {
            'family': 'wikipedia',
            'code': 'en'
        },
        'test.wp': {
            'family': 'wikipedia',
            'code': 'test'
        },
    }
    cached = True

    def test_fully_qualified_NS0_code(self):
        """Test ':testwiki:wikidata:Q6' on enwp is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':testwiki:wikidata:Q6')
        if show_failures:
            link.parse()
            self.assertEqual(link.site, self.get_site('wikidata'))
            self.assertEqual(link.title, 'Q6')
            self.assertEqual(link.namespace, 0)
        else:
            self.assertRaisesRegex(
                pywikibot.Error,
                'Family testwiki does not exist',
                link.parse)  # very bad

    def test_fully_qualified_NS1_code(self):
        """Test ':testwiki:wikidata:Talk:Q6' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':testwiki:wikidata:Talk:Q6')
        if show_failures:
            link.parse()
            self.assertEqual(link.site, self.get_site('wikidata'))
            self.assertEqual(link.title, 'Q6')
            self.assertEqual(link.namespace, 1)
        else:
            self.assertRaisesRegex(
                pywikibot.Error,
                'Family testwiki does not exist',
                link.parse)  # very bad

    def test_fully_qualified_NS0_family(self):
        """Test ':wikidata:testwiki:Q6' on enwp is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':wikidata:testwiki:Q6')
        link.parse()
        if show_failures:
            self.assertEqual(link.site, self.get_site('test.wp'))
            self.assertEqual(link.title, 'Q6')
            self.assertEqual(link.namespace, 0)
        else:
            self.assertEqual(link.site, self.get_site('enwp'))
            self.assertEqual(link.title, 'Wikidata:testwiki:Q6')
            self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_family(self):
        """Test ':wikidata:testwiki:Talk:Q6' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':wikidata:testwiki:Talk:Q6')
        link.parse()
        if show_failures:
            self.assertEqual(link.site, self.get_site('test.wp'))
            self.assertEqual(link.title, 'Q6')
            self.assertEqual(link.namespace, 1)
        else:
            self.assertEqual(link.site, self.get_site('enwp'))
            self.assertEqual(link.title, 'Wikidata:testwiki:Talk:Q6')
            self.assertEqual(link.namespace, 0)


class TestFullyQualifiedOneSiteFamilyExplicitLinkParser(TestCase):

    family = 'species'
    code = 'species'
    cached = True

    def test_fully_qualified_NS0_code(self):
        """Test ':species:species:Main Page' on species is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':species:species:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_code(self):
        """Test ':species:species:Talk:Main Page' on species is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':species:species:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


# ---- Tests of a Link without colons, which shouldnt be interwikis, follow.


class TestPartiallyQualifiedImplicitLinkSameSiteParser(TestCase):

    family = 'wikipedia'
    code = 'en'
    cached = True

    def setUp(self):
        self.old_lang = config.mylang
        self.old_family = config.family

    def tearDown(self):
        config.mylang = self.old_lang
        config.family = self.old_family

    def test_partially_qualified_NS0_code(self):
        """Test 'wikipedia:Main Page' on enwp is namespace 4."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 4)

    def test_partially_qualified_NS1_code(self):
        """Test 'wikipedia:Talk:Main Page' on enwp is namespace 4."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Talk:Main Page')
        self.assertEqual(link.namespace, 4)

    def test_partially_qualified_NS0_family(self):
        """Test 'en:Main Page' on enwp is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_family(self):
        """Test 'en:Talk:Main Page' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestPartiallyQualifiedImplicitLinkDifferentCodeParser(TestCase):

    family = 'wikipedia'
    code = 'en'
    cached = True

    def setUp(self):
        self.old_lang = config.mylang
        self.old_family = config.family

    def tearDown(self):
        config.mylang = self.old_lang
        config.family = self.old_family

    def test_partially_qualified_NS0_family(self):
        """Test 'en:Main Page' on dewp  is namespace 0."""
        config.mylang = 'de'
        config.family = 'wikipedia'
        link = Link('en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_family(self):
        """Test 'en:Talk:Main Page' on dewp is namespace 1."""
        config.mylang = 'de'
        config.family = 'wikipedia'
        link = Link('en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestPartiallyQualifiedImplicitLinkDifferentFamilyParser(TestCase):

    family = 'wikipedia'
    code = 'en'
    cached = True

    def setUp(self):
        self.old_lang = config.mylang
        self.old_family = config.family

    def tearDown(self):
        config.mylang = self.old_lang
        config.family = self.old_family

    def test_partially_qualified_NS0_code(self):
        """Test 'wikipedia:Main Page' on enws is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link('wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_code(self):
        """Test 'wikipedia:Talk:Main Page' on enws is ns 1."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link('wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestFullyQualifiedImplicitLinkSameFamilyParser(TestCase):

    family = 'wikipedia'
    code = 'en'
    cached = True

    def test_fully_qualified_NS0_code(self):
        """Test 'en:wikipedia:Main Page' on enwp is namespace 4."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('en:wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 4)

    def test_fully_qualified_NS1_code(self):
        """Test 'en:wikipedia:Talk:Main Page' on enwp is namespace 4."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('en:wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Talk:Main Page')
        self.assertEqual(link.namespace, 4)


class TestFullyQualifiedImplicitLinkDifferentFamilyParser(TestCase):

    sites = {
        'enws': {
            'family': 'wikisource',
            'code': 'en'
        },
        'enwp': {
            'family': 'wikipedia',
            'code': 'en'
        }
    }
    cached = True

    def test_fully_qualified_NS0_code(self):
        """Test 'en:wikipedia:Main Page' on enws is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link('en:wikipedia:Main Page')
        if show_failures:
            link.parse()
        else:
            self.assertRaisesRegex(
                pywikibot.Error,
                "Improperly formatted interwiki link 'en:wikipedia:Main Page'",
                link.parse)
        if show_failures:
            self.assertEqual(link.site, self.get_site('enwp'))
        else:
            self.assertEqual(link.site, self.get_site('enws'))
        if show_failures:
            self.assertEqual(link.title, 'Main Page')
            self.assertEqual(link.namespace, 0)
        else:
            try:
                link.title
            except pywikibot.Error as e:
                self.assertEqual(str(e), "Improperly formatted interwiki link 'en:wikipedia:Main Page'")

    def test_fully_qualified_NS1_code(self):
        """Test 'en:wikipedia:Main Page' on enws is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link('en:wikipedia:Talk:Main Page')
        if show_failures:
            link.parse()
        else:
            self.assertRaisesRegex(
                pywikibot.Error,
                "Improperly formatted interwiki link 'en:wikipedia:Talk:Main Page'",
                link.parse)
        if show_failures:
            self.assertEqual(link.site, self.get_site('enwp'))
        else:
            self.assertEqual(link.site, self.get_site('enws'))
        if show_failures:
            self.assertEqual(link.title, 'Main Page')
            self.assertEqual(link.namespace, 1)
        else:
            try:
                link.title
            except pywikibot.Error as e:
                self.assertEqual(str(e), "Improperly formatted interwiki link 'en:wikipedia:Talk:Main Page'")

    def test_fully_qualified_NS0_family(self):
        """Test 'wikipedia:en:Main Page' on enws is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link('wikipedia:en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_family(self):
        """Test 'wikipedia:en:Talk:Main Page' on enws is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link('wikipedia:en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestFullyQualifiedImplicitLinkNoLangConfigFamilyParser(TestCase):

    sites = {
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata'
        },
        'enwp': {
            'family': 'wikipedia',
            'code': 'en'
        }
    }
    cached = True

    def test_fully_qualified_NS0_code(self):
        """Test 'en:wikipedia:Main Page' on wikidata is namespace 4."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link('en:wikipedia:Main Page')
        link.parse()
        if show_failures:
            self.assertEqual(link.site, self.get_site('enwp'))
        else:
            self.assertEqual(link.site, self.get_site('wikidata'))
        if show_failures:
            self.assertEqual(link.title, 'Main Page')
            self.assertEqual(link.namespace, 4)
        else:
            self.assertEqual(link.title, 'En:wikipedia:Main Page')
            self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_code(self):
        """Test 'en:wikipedia:Talk:Main Page' on wikidata is not namespace 1."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link('en:wikipedia:Talk:Main Page')
        link.parse()
        if show_failures:
            self.assertEqual(link.site, self.get_site('enwp'))
        else:
            self.assertEqual(link.site, self.get_site('wikidata'))
        if show_failures:
            self.assertEqual(link.title, 'Talk:Main Page')
            self.assertEqual(link.namespace, 4)
        else:
            self.assertEqual(link.title, 'En:wikipedia:Talk:Main Page')
            self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS0_family(self):
        """Test 'wikipedia:en:Main Page' on wikidata is namespace 0."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link('wikipedia:en:Main Page')
        if show_failures:
            link.parse()
            self.assertEqual(link.site, self.get_site('enwp'))
            self.assertEqual(link.namespace, 0)
            self.assertEqual(link.title, 'Main Page')
        else:
            self.assertRaisesRegex(
                pywikibot.NoSuchSite,
                'Language wikidata does not exist in family wikipedia',
                link.parse)  # very bad

    def test_fully_qualified_NS1_family(self):
        """Test 'wikipedia:en:Talk:Main Page' on wikidata is namespace 1."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link('wikipedia:en:Talk:Main Page')
        if show_failures:
            link.parse()
        else:
            self.assertRaisesRegex(
                pywikibot.NoSuchSite,
                'Language wikidata does not exist in family wikipedia',
                link.parse)  # very bad
        if show_failures:
            self.assertEqual(link.site, self.get_site('enwp'))
        else:
            self.assertEqual(link.site, self.get_site('wikidata'))
        if show_failures:
            self.assertEqual(link.title, 'Main Page')
            self.assertEqual(link.namespace, 1)


class TestFullyQualifiedNoLangFamilyImplicitLinkParser(TestCase):

    family = 'wikidata'
    code = 'test'
    cached = True

    def test_fully_qualified_NS0_code(self):
        """Test 'testwiki:wikidata:Q6' on enwp is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('testwiki:wikidata:Q6')
        if show_failures:
            link.parse()
            self.assertEqual(link.site, pywikibot.Site('wikidata', 'wikidata'))
            self.assertEqual(link.title, 'Q6')
            self.assertEqual(link.namespace, 0)
        else:
            self.assertRaisesRegex(
                pywikibot.Error,
                'Family testwiki does not exist',
                link.parse)  # very bad

    def test_fully_qualified_NS1_code(self):
        """Test 'testwiki:wikidata:Talk:Q6' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('testwiki:wikidata:Talk:Q6')
        if show_failures:
            link.parse()
            self.assertEqual(link.site, pywikibot.Site('wikidata', 'wikidata'))
            self.assertEqual(link.title, 'Q6')
            self.assertEqual(link.namespace, 1)
        else:
            self.assertRaisesRegex(
                pywikibot.Error,
                'Family testwiki does not exist',
                link.parse)  # very bad

    def test_fully_qualified_NS0_family(self):
        """Test 'wikidata:testwiki:Q6' on enwp is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('wikidata:testwiki:Q6')
        link.parse()
        if show_failures:
            self.assertEqual(link.site, pywikibot.Site('test', 'wikipedia'))
            self.assertEqual(link.title, 'Q6')
            self.assertEqual(link.namespace, 0)
        else:
            self.assertEqual(link.site, pywikibot.Site('en', 'wikipedia'))
            self.assertEqual(link.title, 'Wikidata:testwiki:Q6')
            self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_family(self):
        """Test 'wikidata:testwiki:Talk:Q6' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('wikidata:testwiki:Talk:Q6')
        link.parse()
        if show_failures:
            self.assertEqual(link.site, pywikibot.Site('test', 'wikipedia'))
            self.assertEqual(link.title, 'Q6')
            self.assertEqual(link.namespace, 1)
        else:
            self.assertEqual(link.site, pywikibot.Site('en', 'wikipedia'))
            self.assertEqual(link.title, 'Wikidata:testwiki:Talk:Q6')
            self.assertEqual(link.namespace, 0)


class TestFullyQualifiedOneSiteFamilyImplicitLinkParser(TestCase):

    family = 'species'
    code = 'species'
    cached = True

    def test_fully_qualified_NS0_family_code(self):
        """Test 'species:species:Main Page' on enwp is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('species:species:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_family_code(self):
        """Test 'species:species:Talk:Main Page' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('species:species:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)

    def test_fully_qualified_NS0_code(self):
        """Test 'species:Main Page' on enwp is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('species:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_code(self):
        """Test 'species:Talk:Main Page' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('species:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
