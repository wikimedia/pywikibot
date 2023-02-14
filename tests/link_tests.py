#!/usr/bin/env python3
"""Test Link functionality."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import re
from contextlib import suppress

import pywikibot
from pywikibot import Site, config
from pywikibot.exceptions import InvalidTitleError, SiteDefinitionError
from pywikibot.page import Link, Page, SiteLink
from pywikibot.site import Namespace
from tests.aspects import (
    AlteredDefaultSiteTestCase,
    DefaultDrySiteTestCase,
    TestCase,
    WikimediaDefaultSiteTestCase,
    unittest,
)


class TestCreateSeparated(DefaultDrySiteTestCase):

    """Test ``Link.create_separated``."""

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

    def replaced(self, iterable):
        """Replace family specific title delimiter."""
        for items in iterable:
            if isinstance(items, str):
                items = [items]
            items = [re.sub(' ',
                            self.site.family.title_delimiter_and_aliases[0],
                            item)
                     for item in items]
            if len(items) == 1:
                items = items[0]
            yield items

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

        site = self.site

        for title in self.replaced(title_tests):
            with self.subTest(title=title):
                self.assertEqual(Link(title, site).title, title)

        for link, title in self.replaced(extended_title_tests):
            with self.subTest(link=link, title=title):
                self.assertEqual(Link(link, site).title, title)

        anchor_link = Link('A | B', site)
        self.assertEqual(anchor_link.title, 'A')
        self.assertEqual(anchor_link.anchor, ' B')

        section_link = Link('A%23B', site)
        self.assertEqual(section_link.title, 'A')
        self.assertEqual(section_link.section, 'B')

    def test_invalid(self):
        """Test that invalid titles raise InvalidTitleError."""
        # Bad characters forbidden regardless of wgLegalTitleChars
        def generate_contains_illegal_chars_exc_regex(text):
            exc_regex = (
                r'^(u|)\'{}\' contains illegal char\(s\) (u|)\'{}\'$'
                .format(re.escape(text), re.escape(text[2])))
            return exc_regex

        # Directory navigation
        def generate_contains_dot_combinations_exc_regex(text):
            exc_regex = (r'^\(contains \. / combinations\): (u|)\'{}\'$'
                         .format(re.escape(text)))
            return exc_regex

        # Tilde
        def generate_contains_tilde_exc_regex(text):
            exc_regex = r'^\(contains ~~~\): (u|)\'{}\'$' \
                        .format(re.escape(text))
            return exc_regex

        # Overlength
        def generate_overlength_exc_regex(text):
            exc_regex = r'^\(over 255 bytes\): (u|)\'{}\'$' \
                        .format(re.escape(text))
            return exc_regex

        # Namespace prefix without actual title
        def generate_has_no_title_exc_regex(text):
            exc_regex = r'^(u|)\'{}\' has no title\.$'.format(
                re.escape(text.strip()))
            return exc_regex

        title_tests = [
            # Empty title
            (['', ':'],
             r'^The link \[\[.*\]\] does not contain a page title$'),

            (['A [ B', 'A ] B', 'A { B', 'A } B', 'A < B', 'A > B'],
             generate_contains_illegal_chars_exc_regex),

            # URL encoding
            # %XX is understood by wikimedia but not %XXXX
            (['A%2523B'],
             r'^(u|)\'A%23B\' contains illegal char\(s\) (u|)\'%23\'$'),

            # A link is invalid if their (non-)talk page would be in another
            # namespace than the link's "other" namespace
            (['Talk:File:Example.svg'],
             r'The \(non-\)talk page of (u|)\'Talk:File:Example.svg\''
             r' is a valid title in another namespace.'),

            (['.', '..', './Sandbox', '../Sandbox', 'Foo/./Sandbox',
              'Foo/../Sandbox', 'Sandbox/.', 'Sandbox/..'],
             generate_contains_dot_combinations_exc_regex),

            (['A ~~~ Name', 'A ~~~~ Signature', 'A ~~~~~ Timestamp'],
             generate_contains_tilde_exc_regex),

            ([('x' * 256), ('Invalid:' + 'X' * 248)],
             generate_overlength_exc_regex),

            (['Talk:'],
             generate_has_no_title_exc_regex),
        ]

        # Known issues with wikihow.
        if self.site.family.name != 'wikihow':
            title_tests.extend([
                (['Category: ', 'Category: #bar'],
                 generate_has_no_title_exc_regex),
                (['__  __', '  __  '],
                 r'^The link \[\[\]\] does not contain a page title$'),
            ])

        for texts_to_test, exception_regex in title_tests:
            for text in self.replaced(texts_to_test):
                with self.subTest(title=text):
                    if callable(exception_regex):
                        regex = exception_regex(text)
                    else:
                        regex = exception_regex
                    with self.assertRaisesRegex(InvalidTitleError, regex):
                        Link(text, self.site).parse()

    def test_relative(self):
        """Test that relative links are handled properly."""
        # Subpage
        page = Page(self.site, 'Foo')
        rel_link = Link('/bar', page)
        self.assertEqual(rel_link.title, 'Foo/bar')
        self.assertEqual(rel_link.site, self.site)
        # Subpage of Page with section
        page = Page(self.site, 'Foo#Baz')
        rel_link = Link('/bar', page)
        self.assertEqual(rel_link.title, 'Foo/bar')
        self.assertEqual(rel_link.site, self.site)
        # Non-subpage link text beginning with slash
        abs_link = Link('/bar', self.site)
        self.assertEqual(abs_link.title, '/bar')


class Issue10254TestCase(DefaultDrySiteTestCase):

    """Test T102461 (Python issue 10254)."""

    def test_no_change(self):
        """Test T102461 (Python issue 10254) is not encountered."""
        title = 'Li̍t-sṳ́'
        link = Link(title, self.site)
        self.assertEqual(link.title, 'Li̍t-sṳ́')


# ---- The first set of tests are explicit links, starting with a ':'.

class LinkTestCase(AlteredDefaultSiteTestCase):

    """Cached API test for link tests."""

    cache = True


class LinkTestWikiEn(LinkTestCase):

    """Link tests on wikipedia:en."""

    family = 'wikipedia'
    code = 'en'

    def setUp(self):
        """Setup tests."""
        super().setUp()
        config.mylang = 'en'
        config.family = 'wikipedia'


class TestPartiallyQualifiedExplicitLinkSameSiteParser(LinkTestWikiEn):

    """Link tests."""

    def test_partially_qualified_NS0_code(self):
        """Test ':wikipedia:Main Page' on enwp is namespace 4."""
        link = Link(':wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 4)

    def test_partially_qualified_NS1_code(self):
        """Test ':wikipedia:Talk:Main Page' on enwp is namespace 4."""
        link = Link(':wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Talk:Main Page')
        self.assertEqual(link.namespace, 4)

    def test_partially_qualified_NS0_family(self):
        """Test ':en:Main Page' on enwp is namespace 0."""
        link = Link(':en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_family(self):
        """Test ':en:Talk:Main Page' on enwp is namespace 1."""
        link = Link(':en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestPartiallyQualifiedExplicitLinkDifferentCodeParser(LinkTestWikiEn):

    """Link tests."""

    def test_partially_qualified_NS0_family(self):
        """Test ':en:Main Page' on dewp is namespace 0."""
        link = Link(':en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_family(self):
        """Test ':en:Talk:Main Page' on dewp is namespace 1."""
        link = Link(':en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestPartiallyQualifiedExplicitLinkDifferentFamilyParser(LinkTestCase):

    """Link tests."""

    family = 'wikipedia'
    code = 'en'

    def setUp(self):
        """Setup tests."""
        super().setUp()
        config.mylang = 'en'
        config.family = 'wikisource'

    def test_partially_qualified_NS0_code(self):
        """Test ':wikipedia:Main Page' on enws is namespace 0."""
        link = Link(':wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_code(self):
        """Test ':wikipedia:Talk:Main Page' on enws is ns 1."""
        link = Link(':wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestFullyQualifiedSameNamespaceFamilyParser(LinkTestCase):

    """Link tests."""

    family = 'wikipedia'
    code = 'en'

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
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'En:Talk:Main Page')
        self.assertEqual(link.namespace, 4)


class TestFullyQualifiedExplicitLinkSameFamilyParser(LinkTestWikiEn):

    """Link tests."""

    def test_fully_qualified_NS0_code(self):
        """Test ':en:wikipedia:Main Page' on enwp is namespace 4."""
        link = Link(':en:wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 4)

    def test_fully_qualified_NS1_code(self):
        """Test ':en:wikipedia:Talk:Main Page' on enwp is namespace 4."""
        link = Link(':en:wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Talk:Main Page')
        self.assertEqual(link.namespace, 4)


class TestFullyQualifiedLinkDifferentFamilyParser(LinkTestCase):

    """Test link to a different family with and without preleading colon."""

    family = 'wikipedia'
    code = 'en'

    PATTERN = '{colon}{first}:{second}:{title}'

    def setUp(self):
        """Setup tests."""
        super().setUp()
        config.mylang = 'en'
        config.family = 'wikisource'

    def test_fully_qualified_NS0(self):
        """Test that fully qualified link is in namespace 0."""
        family, code = 'wikipedia', 'en'
        for colon in ('', ':'):  # with or without preleading colon
            # switch code:family sequence en:wikipedia or wikipedia:en
            for first, second in [(family, code), (code, family)]:
                with self.subTest(colon=colon,
                                  site=f'{first}:{second}'):
                    link_title = self.PATTERN.format(colon=colon,
                                                     first=first,
                                                     second=second,
                                                     title='Main Page')
                    link = Link(link_title)
                    link.parse()
                    self.assertEqual(link.site, self.site)
                    self.assertEqual(link.title, 'Main Page')
                    self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1(self):
        """Test that fully qualified link is in namespace 1."""
        family, code = 'wikipedia', 'en'
        for colon in ('', ':'):  # with or without preleading colon
            # switch code:family sequence en:wikipedia or wikipedia:en
            for first, second in [(family, code), (code, family)]:
                with self.subTest(colon=colon,
                                  site=f'{first}:{second}'):
                    link_title = self.PATTERN.format(colon=colon,
                                                     first=first,
                                                     second=second,
                                                     title='Talk:Main Page')
                    link = Link(link_title)
                    link.parse()
                    self.assertEqual(link.site, self.site)
                    self.assertEqual(link.title, 'Main Page')
                    self.assertEqual(link.namespace, 1)


class TestFullyQualifiedExplicitLinkNoLangConfigFamilyParser(LinkTestCase):

    """Test link from family without lang code to a different family."""

    family = 'wikipedia'
    code = 'en'

    def setUp(self):
        """Setup tests."""
        super().setUp()
        config.mylang = 'wikidata'
        config.family = 'wikidata'

    def test_fully_qualified_NS0_code(self):
        """Test ':en:wikipedia:Main Page' on wikidata is namespace 4."""
        link = Link(':en:wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 4)

    def test_fully_qualified_NS1_code(self):
        """Test ':en:wikipedia:Talk:Main Page' on wikidata is namespace 4."""
        link = Link(':en:wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Talk:Main Page')
        self.assertEqual(link.namespace, 4)

    def test_fully_qualified_NS0_family(self):
        """Test ':wikipedia:en:Main Page' on wikidata is namespace 0."""
        link = Link(':wikipedia:en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_family(self):
        """Test ':wikipedia:en:Talk:Main Page' on wikidata is namespace 1."""
        link = Link(':wikipedia:en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestFullyQualifiedNoLangFamilyExplicitLinkParser(LinkTestCase):

    """Test wikibase links."""

    sites = {
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata'
        },
        'test': {
            'family': 'wikipedia',
            'code': 'test'
        },
    }

    def setUp(self):
        """Setup tests."""
        super().setUp()
        config.mylang = 'en'
        config.family = 'wikipedia'

    def test_fully_qualified_NS0_code(self):
        """Test ':testwiki:wikidata:Q6' on enwp is namespace 0."""
        link = Link(':testwiki:wikidata:Q6')
        link.parse()
        self.assertEqual(link.site, self.get_site('wikidata'))
        self.assertEqual(link.title, 'Q6')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_code(self):
        """Test ':testwiki:wikidata:Talk:Q6' on enwp is namespace 1."""
        link = Link(':testwiki:wikidata:Talk:Q6')
        link.parse()
        self.assertEqual(link.site, self.get_site('wikidata'))
        self.assertEqual(link.title, 'Q6')
        self.assertEqual(link.namespace, 1)

    def test_fully_qualified_NS0_family(self):
        """Test ':wikidata:testwiki:Q6' on enwp is namespace 0."""
        config.family = 'wikipedia'
        link = Link(':wikidata:testwiki:Q6')
        link.parse()
        self.assertEqual(link.site, self.get_site('test'))
        self.assertEqual(link.title, 'Q6')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_family(self):
        """Test ':wikidata:testwiki:Talk:Q6' on enwp is namespace 1."""
        link = Link(':wikidata:testwiki:Talk:Q6')
        link.parse()
        self.assertEqual(link.site, self.get_site('test'))
        self.assertEqual(link.title, 'Q6')
        self.assertEqual(link.namespace, 1)


class TestFullyQualifiedOneSiteFamilyExplicitLinkParser(LinkTestCase):

    """Test links to one site target family."""

    family = 'species'
    code = 'species'

    def setUp(self):
        """Setup tests."""
        super().setUp()
        config.mylang = 'en'
        config.family = 'wikipedia'

    def test_fully_qualified_NS0_code(self):
        """Test ':species:species:Main Page' on species is namespace 0."""
        link = Link(':species:species:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_code(self):
        """Test ':species:species:Talk:Main Page' on species is namespace 1."""
        link = Link(':species:species:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


# ---- Tests of a Link without colons, which shouldn't be interwikis, follow.


class TestPartiallyQualifiedImplicitLinkSameSiteParser(LinkTestWikiEn):

    """Test partially qualified links to same site."""

    def test_partially_qualified_NS0_code(self):
        """Test 'wikipedia:Main Page' on enwp is namespace 4."""
        link = Link('wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 4)

    def test_partially_qualified_NS1_code(self):
        """Test 'wikipedia:Talk:Main Page' on enwp is namespace 4."""
        link = Link('wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Talk:Main Page')
        self.assertEqual(link.namespace, 4)

    def test_partially_qualified_NS0_family(self):
        """Test 'en:Main Page' on enwp is namespace 0."""
        link = Link('en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_family(self):
        """Test 'en:Talk:Main Page' on enwp is namespace 1."""
        link = Link('en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestPartiallyQualifiedImplicitLinkDifferentCodeParser(LinkTestWikiEn):

    """Test partially qualified links to different code."""

    def test_partially_qualified_NS0_family(self):
        """Test 'en:Main Page' on dewp is namespace 0."""
        link = Link('en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_family(self):
        """Test 'en:Talk:Main Page' on dewp is namespace 1."""
        link = Link('en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestPartiallyQualifiedImplicitLinkDifferentFamilyParser(LinkTestCase):

    """Test partially qualified links to different family."""

    family = 'wikipedia'
    code = 'en'

    def setUp(self):
        """Setup tests."""
        super().setUp()
        config.mylang = 'en'
        config.family = 'wikisource'

    def test_partially_qualified_NS0_code(self):
        """Test 'wikipedia:Main Page' on enws is namespace 0."""
        link = Link('wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_code(self):
        """Test 'wikipedia:Talk:Main Page' on enws is ns 1."""
        link = Link('wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestFullyQualifiedImplicitLinkSameFamilyParser(LinkTestWikiEn):

    """Link tests."""

    def test_fully_qualified_NS0_code(self):
        """Test 'en:wikipedia:Main Page' on enwp is namespace 4."""
        link = Link('en:wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 4)

    def test_fully_qualified_NS1_code(self):
        """Test 'en:wikipedia:Talk:Main Page' on enwp is namespace 4."""
        link = Link('en:wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Talk:Main Page')
        self.assertEqual(link.namespace, 4)


class TestFullyQualifiedImplicitLinkNoLangConfigFamilyParser(LinkTestCase):

    """Test implicit link from family without lang code to other family."""

    family = 'wikipedia'
    code = 'en'

    def setUp(self):
        """Setup tests."""
        super().setUp()
        config.mylang = 'wikidata'
        config.family = 'wikidata'

    def test_fully_qualified_NS0_code(self):
        """Test 'en:wikipedia:Main Page' on wikidata is namespace 4."""
        link = Link('en:wikipedia:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 4)

    def test_fully_qualified_NS1_code(self):
        """Test 'en:wikipedia:Talk:Main Page' on wikidata isn't namespace 1."""
        link = Link('en:wikipedia:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Talk:Main Page')
        self.assertEqual(link.namespace, 4)

    def test_fully_qualified_NS0_family(self):
        """Test 'wikipedia:en:Main Page' on wikidata is namespace 0."""
        link = Link('wikipedia:en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.namespace, 0)
        self.assertEqual(link.title, 'Main Page')

    def test_fully_qualified_NS1_family(self):
        """Test 'wikipedia:en:Talk:Main Page' on wikidata is namespace 1."""
        link = Link('wikipedia:en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestFullyQualifiedNoLangFamilyImplicitLinkParser(LinkTestCase):

    """Test wikibase links without preleading colon."""

    family = 'wikidata'
    code = 'test'

    def setUp(self):
        """Setup tests."""
        super().setUp()
        config.mylang = 'en'
        config.family = 'wikipedia'

    def test_fully_qualified_NS0(self):
        """Test prefixed links with 'Q6' on enwp is namespace 0."""
        test = [('testwiki:wikidata', 'wikidata:wikidata'),
                ('wikidata:testwiki', 'wikipedia:test')]
        for linkprefix, sitetitle in test:
            with self.subTest(pattern=linkprefix):
                link = Link(linkprefix + ':Q6')
                link.parse()
                self.assertEqual(link.site, pywikibot.Site(sitetitle))
                self.assertEqual(link.title, 'Q6')
                self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1(self):
        """Test prefixed links with 'Talk:Q6' on enwp is namespace 1."""
        test = [('testwiki:wikidata', 'wikidata:wikidata'),
                ('wikidata:testwiki', 'wikipedia:test')]
        for linkprefix, sitetitle in test:
            with self.subTest(pattern=linkprefix):
                link = Link(linkprefix + ':Talk:Q6')
                link.parse()
                self.assertEqual(link.site, pywikibot.Site(sitetitle))
                self.assertEqual(link.title, 'Q6')
                self.assertEqual(link.namespace, 1)


class TestFullyQualifiedOneSiteFamilyImplicitLinkParser(LinkTestCase):

    """Test links to one site target family without preleading colon."""

    family = 'species'
    code = 'species'

    def setUp(self):
        """Setup tests."""
        super().setUp()
        config.mylang = 'en'
        config.family = 'wikipedia'

    def test_fully_qualified_NS0_family_code(self):
        """Test 'species:species:Main Page' on enwp is namespace 0."""
        link = Link('species:species:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_family_code(self):
        """Test 'species:species:Talk:Main Page' on enwp is namespace 1."""
        link = Link('species:species:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)

    def test_fully_qualified_NS0_code(self):
        """Test 'species:Main Page' on enwp is namespace 0."""
        link = Link('species:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_fully_qualified_NS1_code(self):
        """Test 'species:Talk:Main Page' on enwp is namespace 1."""
        link = Link('species:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestEmptyTitle(TestCase):

    """Test links which contain no title."""

    family = 'wikipedia'
    code = 'en'

    def test_interwiki_mainpage(self):
        """Test that Link allow links without a title to the main page."""
        link = Link('en:', self.site)
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, '')
        self.assertEqual(link.namespace, 0)

    def test_interwiki_namespace_without_title(self):
        """Test that Link doesn't allow links without a title."""
        link = Link('en:Help:', self.site)
        with self.assertRaisesRegex(
                InvalidTitleError,
                "'en:Help:' has no title."):
            link.parse()

    def test_no_text(self):
        """Test that Link doesn't allow empty."""
        link = Link('', self.site)
        with self.assertRaisesRegex(
                InvalidTitleError,
                r'The link \[\[.*\]\] does not contain a page title'):
            link.parse()

    def test_namespace_lookalike(self):
        """Test that Link does only detect valid namespaces."""
        link = Link('CAT:', self.site)
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'CAT:')
        self.assertEqual(link.namespace, 0)

        link = Link('en:CAT:', self.site)
        link.parse()
        self.assertEqual(link.site, self.site)
        self.assertEqual(link.title, 'CAT:')
        self.assertEqual(link.namespace, 0)


class TestForeignInterwikiLinks(WikimediaDefaultSiteTestCase):

    """Test links to non-wikis."""

    family = 'wikipedia'
    code = 'en'

    def test_non_wiki_prefix(self):
        """Test that Link fails if the interwiki prefix is not a wiki."""
        link = Link('bugzilla:1337', source=self.site)
        # bugzilla does not return a json content but redirects to phab.
        # api.Request._json_loads cannot detect this problem and raises
        # a SiteDefinitionError. The site is created anyway but the title
        # cannot be parsed
        with self.assertRaises(SiteDefinitionError):
            link.site
        self.assertEqual(link.site.sitename, 'wikimedia:wikimedia')
        self.assertTrue(link._is_interwiki)

    def test_other_wiki_prefix(self):
        """Test that Link fails if the interwiki prefix is a unknown family."""
        link = Link('bulba:title on auto-generated Site', source=self.site)
        self.assertEqual(link.title, 'Title on auto-generated Site')
        self.assertEqual(link.site.sitename, 'bulba:bulba')
        self.assertTrue(link._is_interwiki)

    def test_invalid_wiki_prefix(self):
        """Test that Link with prefix not listed in InterwikiMap."""
        title = 'Unknownprefix:This title'
        link = Link(title, source=self.site)
        self.assertEqual(link.title, title)
        self.assertEqual(link.site, self.site)
        self.assertFalse(link._is_interwiki)


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
    with suppress(SystemExit):
        unittest.main()
