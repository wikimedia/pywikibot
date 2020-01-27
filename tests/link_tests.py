# -*- coding: utf-8 -*-
"""Test Link functionality."""
#
# (C) Pywikibot team, 2014-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import re

import pywikibot

from pywikibot import config2 as config
from pywikibot import Site
from pywikibot.page import Link, Page, SiteLink
from pywikibot.site import Namespace
from pywikibot.exceptions import Error, InvalidTitle

from tests.aspects import (
    unittest,
    AlteredDefaultSiteTestCase as LinkTestCase,
    DefaultDrySiteTestCase,
    WikimediaDefaultSiteTestCase,
    TestCase,
)


class TestCreateSeparated(DefaultDrySiteTestCase):

    """Test C{Link.create_separated}."""

    def _test_link(self, link, page, section, label):
        """Test the separate contents of the link."""
        self.assertIs(link.site, self.site)
        self.assertEqual(link.title, page)
        if section is None:
            self.assertIsNone(link.section)
        else:
            self.assertEqual(link.section, section)
        if label is None:
            self.assertIsNone(link.anchor)
        else:
            self.assertEqual(link.anchor, label)

    def test(self):
        """Test combinations of parameters."""
        self._test_link(Link.create_separated('Foo', self.site),
                        'Foo', None, None)
        self._test_link(Link.create_separated('Foo', self.site, section='Bar'),
                        'Foo', 'Bar', None)
        self._test_link(Link.create_separated('Foo', self.site, label='Baz'),
                        'Foo', None, 'Baz')
        self._test_link(Link.create_separated('Foo', self.site, section='Bar',
                                              label='Baz'),
                        'Foo', 'Bar', 'Baz')


# ---- Tests checking if the parser does (not) accept (in)valid titles


class TestLink(DefaultDrySiteTestCase):

    """
    Test parsing links with DrySite.

    The DrySite is using the builtin namespaces which behaviour is controlled
    in this repository so namespace aware tests do work, even when the actual
    default site is using completely different namespaces.
    """

    def test_valid(self):
        """Test that valid titles are correctly normalized."""
        title_tests = ['Sandbox', 'A "B"', "A 'B'", '.com', '~', '"', "'",
                       'Foo/.../Sandbox', 'Sandbox/...', 'A~~', 'X' * 252]

        extended_title_tests = [
            ('Talk:Sandbox', 'Sandbox'),
            ('Talk:Foo:Sandbox', 'Foo:Sandbox'),
            ('File:Example.svg', 'Example.svg'),
            ('File_talk:Example.svg', 'Example.svg'),
            (':A', 'A'),
            # Length is 256 total, but only title part matters
            ('Category:' + 'X' * 248, 'X' * 248),
            ('A%20B', 'A B'),
            ('A &eacute; B', 'A é B'),
            ('A &#233; B', 'A é B'),
            ('A &#x00E9; B', 'A é B'),
            ('A &nbsp; B', 'A B'),
            ('A &#160; B', 'A B'),
        ]

        site = self.get_site()

        for title in title_tests:
            with self.subTest(title=title):
                self.assertEqual(Link(title, site).title, title)

        for link, title in extended_title_tests:
            with self.subTest(link=link, title=title):
                self.assertEqual(Link(link, site).title, title)

        anchor_link = Link('A | B', site)
        self.assertEqual(anchor_link.title, 'A')
        self.assertEqual(anchor_link.anchor, ' B')

        section_link = Link('A%23B', site)
        self.assertEqual(section_link.title, 'A')
        self.assertEqual(section_link.section, 'B')

    def test_invalid(self):
        """Test that invalid titles raise InvalidTitle exception."""
        exception_message_regex = (
            r'^The link does not contain a page title$'
        )

        texts_to_test = ['', ':', '__  __', '  __  ']

        for text in texts_to_test:
            with self.assertRaisesRegex(
                    InvalidTitle,
                    exception_message_regex):
                Link(text, self.get_site()).parse()

        # Bad characters forbidden regardless of wgLegalTitleChars
        def generate_contains_illegal_chars_exc_regex(text):
            exc_regex = (
                r'^(u|)\'{}\' contains illegal char\(s\) (u|)\'{}\'$'
                .format(re.escape(text), re.escape(text[2])))
            return exc_regex

        texts_to_test = ['A [ B', 'A ] B', 'A { B', 'A } B', 'A < B', 'A > B']

        for text in texts_to_test:
            with self.assertRaisesRegex(
                    InvalidTitle,
                    generate_contains_illegal_chars_exc_regex(text)):
                Link(text, self.get_site()).parse()

        # URL encoding
        # %XX is understood by wikimedia but not %XXXX
        with self.assertRaisesRegex(
                InvalidTitle,
                r'^(u|)\'A%23B\' contains illegal char\(s\) (u|)\'%23\'$'):
            Link('A%2523B', self.get_site()).parse()

        # A link is invalid if their (non-)talk page would be in another
        # namespace than the link's "other" namespace
        with self.assertRaisesRegex(
                InvalidTitle,
                (r'The \(non-\)talk page of (u|)\'Talk:File:Example.svg\''
                 r' is a valid title in another namespace.')):
            Link('Talk:File:Example.svg', self.get_site()).parse()

        # Directory navigation
        def generate_contains_dot_combinations_exc_regex(text):
            exc_regex = (r'^\(contains \. / combinations\): (u|)\'{}\'$'
                         .format(re.escape(text)))
            return exc_regex

        texts_to_test = ['.', '..', './Sandbox', '../Sandbox', 'Foo/./Sandbox',
                         'Foo/../Sandbox', 'Sandbox/.', 'Sandbox/..']

        for text in texts_to_test:
            with self.assertRaisesRegex(
                    InvalidTitle,
                    generate_contains_dot_combinations_exc_regex(text)):
                Link(text, self.get_site()).parse()

        # Tilde
        def generate_contains_tilde_exc_regex(text):
            exc_regex = r'^\(contains ~~~\): (u|)\'%s\'$' % re.escape(text)
            return exc_regex

        texts_to_test = ['A ~~~ Name', 'A ~~~~ Signature', 'A ~~~~~ Timestamp']

        for text in texts_to_test:
            with self.assertRaisesRegex(
                    InvalidTitle,
                    generate_contains_tilde_exc_regex(text)):
                Link(text, self.get_site()).parse()

        # Overlength
        def generate_overlength_exc_regex(text):
            exc_regex = r'^\(over 255 bytes\): (u|)\'%s\'$' % re.escape(text)
            return exc_regex

        texts_to_test = [('x' * 256), ('Invalid:' + 'X' * 248)]

        for text in texts_to_test:
            with self.assertRaisesRegex(
                    InvalidTitle,
                    generate_overlength_exc_regex(text)):
                Link(text, self.get_site()).parse()

        # Namespace prefix without actual title
        def generate_has_no_title_exc_regex(text):
            exc_regex = r'^(u|)\'{}\' has no title\.$'.format(re.escape(text))
            return exc_regex

        texts_to_test = ['Talk:', 'Category: ', 'Category: #bar']

        for text in texts_to_test:
            with self.assertRaisesRegex(
                    InvalidTitle,
                    generate_has_no_title_exc_regex(text.strip())):
                Link(text, self.get_site()).parse()

    def test_relative(self):
        """Test that relative links are handled properly."""
        # Subpage
        page = Page(self.get_site(), 'Foo')
        rel_link = Link('/bar', page)
        self.assertEqual(rel_link.title, 'Foo/bar')
        self.assertEqual(rel_link.site, self.get_site())
        # Subpage of Page with section
        page = Page(self.get_site(), 'Foo#Baz')
        rel_link = Link('/bar', page)
        self.assertEqual(rel_link.title, 'Foo/bar')
        self.assertEqual(rel_link.site, self.get_site())
        # Non-subpage link text beginning with slash
        abs_link = Link('/bar', self.get_site())
        self.assertEqual(abs_link.title, '/bar')


class Issue10254TestCase(DefaultDrySiteTestCase):

    """Test T102461 (Python issue 10254)."""

    def setUp(self):
        """Set up test case."""
        super(Issue10254TestCase, self).setUp()
        self._orig_unicodedata = pywikibot.page.unicodedata

    def tearDown(self):
        """Tear down test case."""
        pywikibot.page.unicodedata = self._orig_unicodedata
        super(Issue10254TestCase, self).tearDown()

    def test_no_change(self):
        """Test T102461 (Python issue 10254) is not encountered."""
        title = 'Li̍t-sṳ́'
        link = Link(title, self.site)
        self.assertEqual(link.title, 'Li̍t-sṳ́')


# ---- The first set of tests are explicit links, starting with a ':'.


class TestPartiallyQualifiedExplicitLinkSameSiteParser(LinkTestCase):

    """Link tests."""

    family = 'wikipedia'
    code = 'en'
    cached = True

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


class TestPartiallyQualifiedExplicitLinkDifferentCodeParser(LinkTestCase):

    """Link tests."""

    family = 'wikipedia'
    code = 'en'
    cached = True

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


class TestPartiallyQualifiedExplicitLinkDifferentFamilyParser(LinkTestCase):

    """Link tests."""

    family = 'wikipedia'
    code = 'en'
    cached = True

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


class TestFullyQualifiedSameNamespaceFamilyParser(LinkTestCase):

    """Link tests."""

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


class TestFullyQualifiedExplicitLinkSameFamilyParser(LinkTestCase):

    """Link tests."""

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


class TestFullyQualifiedExplicitLinkDifferentFamilyParser(LinkTestCase):

    """Test link to a different family."""

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
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_code(self):
        """Test ':en:wikipedia:Main Page' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link(':en:wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)

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


class TestFullyQualifiedExplicitLinkNoLangConfigFamilyParser(LinkTestCase):

    """Test link from family without lang code to a different family."""

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
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 4)

    def test_fully_qualified_NS1_code(self):
        """Test ':en:wikipedia:Talk:Main Page' on wikidata is namespace 4."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link(':en:wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Talk:Main Page')
        self.assertEqual(link.namespace, 4)

    def test_fully_qualified_NS0_family(self):
        """Test ':wikipedia:en:Main Page' on wikidata is namespace 0."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link(':wikipedia:en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_family(self):
        """Test ':wikipedia:en:Talk:Main Page' on wikidata is namespace 1."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link(':wikipedia:en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestFullyQualifiedNoLangFamilyExplicitLinkParser(LinkTestCase):

    """Test wikibase links."""

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
        link.parse()
        self.assertEqual(link.site, self.get_site('wikidata'))
        self.assertEqual(link.title, 'Q6')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_code(self):
        """Test ':testwiki:wikidata:Talk:Q6' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':testwiki:wikidata:Talk:Q6')
        link.parse()
        self.assertEqual(link.site, self.get_site('wikidata'))
        self.assertEqual(link.title, 'Q6')
        self.assertEqual(link.namespace, 1)

    def test_fully_qualified_NS0_family(self):
        """Test ':wikidata:testwiki:Q6' on enwp is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':wikidata:testwiki:Q6')
        link.parse()
        self.assertEqual(link.site, self.get_site('test.wp'))
        self.assertEqual(link.title, 'Q6')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_family(self):
        """Test ':wikidata:testwiki:Talk:Q6' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link(':wikidata:testwiki:Talk:Q6')
        link.parse()
        self.assertEqual(link.site, self.get_site('test.wp'))
        self.assertEqual(link.title, 'Q6')
        self.assertEqual(link.namespace, 1)


class TestFullyQualifiedOneSiteFamilyExplicitLinkParser(LinkTestCase):

    """Test links to one site target family."""

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


# ---- Tests of a Link without colons, which shouldn't be interwikis, follow.


class TestPartiallyQualifiedImplicitLinkSameSiteParser(LinkTestCase):

    """Test partially qualified links to same site."""

    family = 'wikipedia'
    code = 'en'
    cached = True

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


class TestPartiallyQualifiedImplicitLinkDifferentCodeParser(LinkTestCase):

    """Test partially qualified links to different code."""

    family = 'wikipedia'
    code = 'en'
    cached = True

    def test_partially_qualified_NS0_family(self):
        """Test 'en:Main Page' on dewp is namespace 0."""
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


class TestPartiallyQualifiedImplicitLinkDifferentFamilyParser(LinkTestCase):

    """Test partially qualified links to different family."""

    family = 'wikipedia'
    code = 'en'
    cached = True

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


class TestFullyQualifiedImplicitLinkSameFamilyParser(LinkTestCase):

    """Link tests."""

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


class TestFullyQualifiedImplicitLinkDifferentFamilyParser(LinkTestCase):

    """Test link to a different family without preleading colon."""

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
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_code(self):
        """Test 'en:wikipedia:Main Page' on enws is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikisource'
        link = Link('en:wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)

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


class TestFullyQualifiedImplicitLinkNoLangConfigFamilyParser(LinkTestCase):

    """Test implicit link from family without lang code to other family."""

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
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 4)

    def test_fully_qualified_NS1_code(self):
        """Test 'en:wikipedia:Talk:Main Page' on wikidata isn't namespace 1."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link('en:wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Talk:Main Page')
        self.assertEqual(link.namespace, 4)

    def test_fully_qualified_NS0_family(self):
        """Test 'wikipedia:en:Main Page' on wikidata is namespace 0."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link('wikipedia:en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.namespace, 0)
        self.assertEqual(link.title, 'Main Page')

    def test_fully_qualified_NS1_family(self):
        """Test 'wikipedia:en:Talk:Main Page' on wikidata is namespace 1."""
        config.mylang = 'wikidata'
        config.family = 'wikidata'
        link = Link('wikipedia:en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site('enwp'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestFullyQualifiedNoLangFamilyImplicitLinkParser(LinkTestCase):

    """Test wikibase links without preleading colon."""

    family = 'wikidata'
    code = 'test'
    cached = True

    def test_fully_qualified_NS0_code(self):
        """Test 'testwiki:wikidata:Q6' on enwp is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('testwiki:wikidata:Q6')
        link.parse()
        self.assertEqual(link.site, pywikibot.Site('wikidata', 'wikidata'))
        self.assertEqual(link.title, 'Q6')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_code(self):
        """Test 'testwiki:wikidata:Talk:Q6' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('testwiki:wikidata:Talk:Q6')
        link.parse()
        self.assertEqual(link.site, pywikibot.Site('wikidata', 'wikidata'))
        self.assertEqual(link.title, 'Q6')
        self.assertEqual(link.namespace, 1)

    def test_fully_qualified_NS0_family(self):
        """Test 'wikidata:testwiki:Q6' on enwp is namespace 0."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('wikidata:testwiki:Q6')
        link.parse()
        self.assertEqual(link.site, pywikibot.Site('test', 'wikipedia'))
        self.assertEqual(link.title, 'Q6')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_family(self):
        """Test 'wikidata:testwiki:Talk:Q6' on enwp is namespace 1."""
        config.mylang = 'en'
        config.family = 'wikipedia'
        link = Link('wikidata:testwiki:Talk:Q6')
        link.parse()
        self.assertEqual(link.site, pywikibot.Site('test', 'wikipedia'))
        self.assertEqual(link.title, 'Q6')
        self.assertEqual(link.namespace, 1)


class TestFullyQualifiedOneSiteFamilyImplicitLinkParser(LinkTestCase):

    """Test links to one site target family without preleading colon."""

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


class TestEmptyTitle(TestCase):

    """Test links which contain no title."""

    family = 'wikipedia'
    code = 'en'

    def test_interwiki_mainpage(self):
        """Test that Link allow links without a title to the main page."""
        link = Link('en:', self.get_site())
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, '')
        self.assertEqual(link.namespace, 0)

    def test_interwiki_namespace_without_title(self):
        """Test that Link doesn't allow links without a title."""
        link = Link('en:Help:', self.get_site())
        self.assertRaisesRegex(
            InvalidTitle, "'en:Help:' has no title.", link.parse)

    def test_no_text(self):
        """Test that Link doesn't allow empty."""
        link = Link('', self.get_site())
        self.assertRaisesRegex(
            InvalidTitle, 'The link does not contain a page title',
            link.parse)

    def test_namespace_lookalike(self):
        """Test that Link does only detect valid namespaces."""
        link = Link('CAT:', self.get_site())
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'CAT:')
        self.assertEqual(link.namespace, 0)

        link = Link('en:CAT:', self.get_site())
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'CAT:')
        self.assertEqual(link.namespace, 0)


class TestInvalidInterwikiLinks(WikimediaDefaultSiteTestCase):

    """Test links to non-wikis."""

    family = 'wikipedia'
    code = 'en'

    def test_non_wiki_prefix(self):
        """Test that Link fails if the interwiki prefix is not a wiki."""
        link = Link('bugzilla:1337', source=self.site)
        self.assertRaisesRegex(
            Error,
            'bugzilla:1337 is not a local page on wikipedia:en, and the '
            'interwiki prefix bugzilla is not supported by Pywikibot!',
            link.parse)

    def test_other_wiki_prefix(self):
        """Test that Link fails if the interwiki prefix is a unknown family."""
        link = Link('bulba:this-will-never-work', source=self.site)
        self.assertRaisesRegex(
            Error,
            'bulba:this-will-never-work is not a local page on wikipedia:en, '
            'and the interwiki prefix bulba is not supported by Pywikibot!',
            link.parse)


class TestSiteLink(WikimediaDefaultSiteTestCase):

    """Test parsing namespaces when creating SiteLinks."""

    def _test_link(self, link, title, namespace, site_code, site_fam):
        """Test the separate contents of the link."""
        self.assertEqual(link.title, title)
        self.assertEqual(link.namespace, namespace)
        self.assertEqual(link.site, Site(site_code, site_fam))
        self.assertEqual(link.badges, [])

    def test_site_link(self):
        """Test parsing of title."""
        self._test_link(SiteLink('Foobar', 'enwiki'),
                        'Foobar', Namespace.MAIN, 'en', 'wikipedia')
        self._test_link(SiteLink('Mall:!!', 'svwiki'),
                        '!!', Namespace.TEMPLATE, 'sv', 'wikipedia')
        self._test_link(SiteLink('Vorlage:!!', 'dewikibooks'),
                        '!!', Namespace.TEMPLATE, 'de', 'wikibooks')
        self._test_link(SiteLink('Ai Weiwei: Never Sorry', 'enwiki'),
                        'Ai Weiwei: Never Sorry', Namespace.MAIN,
                        'en', 'wikipedia')


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
