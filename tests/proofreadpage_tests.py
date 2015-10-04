# -*- coding: utf-8  -*-
"""Tests for the proofreadpage module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import json

import pywikibot

from pywikibot.data import api
from pywikibot.proofreadpage import IndexPage, ProofreadPage
from tests.aspects import unittest, require_modules, TestCase

from tests.basepage_tests import (
    BasePageMethodsTestBase,
    BasePageLoadRevisionsCachingTestBase,
)


class TestProofreadPageInvalidSite(TestCase):

    """Test ProofreadPage class."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def test_invalid_site_source(self):
        """Test ProofreadPage from invalid Site as source."""
        self.assertRaises(pywikibot.UnknownExtension,
                          ProofreadPage, self.site, 'title')


class TestBasePageMethodsProofreadPage(BasePageMethodsTestBase):

    """Test behavior of ProofreadPage methods inherited from BasePage."""

    family = 'wikisource'
    code = 'en'

    def setUp(self):
        """Set up test case."""
        self._page = ProofreadPage(
            self.site, 'Page:Popular Science Monthly Volume 1.djvu/12')
        super(TestBasePageMethodsProofreadPage, self).setUp()

    def test_basepage_methods(self):
        """Test ProofreadPage methods inherited from superclass BasePage."""
        self._test_invoke()
        self._test_return_datatypes()


class TestLoadRevisionsCachingProofreadPage(BasePageLoadRevisionsCachingTestBase):

    """Test site.loadrevisions() caching."""

    family = 'wikisource'
    code = 'en'

    def setUp(self):
        """Set up test case."""
        self._page = ProofreadPage(
            self.site, 'Page:Popular Science Monthly Volume 1.djvu/12')
        super(TestLoadRevisionsCachingProofreadPage, self).setUp()

    def test_page_text(self):
        """Test site.loadrevisions() with Page.text."""
        self._test_page_text()


class TestProofreadPageValidSite(TestCase):

    """Test ProofreadPage class."""

    family = 'wikisource'
    code = 'en'

    cached = True

    valid = {
        'title': 'Page:Popular Science Monthly Volume 1.djvu/12',
        'ql': 4,
        'user': 'T. Mazzei',
        'header': u"{{rh|2|''THE POPULAR SCIENCE MONTHLY.''}}",
        'footer': u'\n{{smallrefs}}',
    }

    existing_invalid = {
        'title': 'Main Page',
    }

    not_existing_invalid = {
        'title': 'User:cannot_exists',
        'title1': 'User:Popular Science Monthly Volume 1.djvu/12'
    }

    def test_valid_site_source(self):
        """Test ProofreadPage from valid Site as source."""
        page = ProofreadPage(self.site, 'title')
        self.assertEqual(page.namespace(), self.site.proofread_page_ns)

    def test_invalid_existing_page_source(self):
        """Test ProofreadPage from invalid existing Page as source."""
        source = pywikibot.Page(self.site, self.existing_invalid['title'])
        self.assertRaises(ValueError, ProofreadPage, source)

    def test_invalid_not_existing_page_source(self):
        """Test ProofreadPage from invalid not existing Page as source."""
        # namespace is forced
        source = pywikibot.Page(self.site,
                                self.not_existing_invalid['title'])
        fixed_source = pywikibot.Page(self.site,
                                      source.title(withNamespace=False),
                                      ns=self.site.proofread_page_ns)
        page = ProofreadPage(fixed_source)
        self.assertEqual(page.title(), fixed_source.title())

    def test_invalid_not_existing_page_source_wrong_ns(self):
        """Test ProofreadPage from Page not existing in non-Page ns as source."""
        source = pywikibot.Page(self.site,
                                self.not_existing_invalid['title1'])
        self.assertRaises(ValueError, ProofreadPage, source)

    def test_invalid_link_source(self):
        """Test ProofreadPage from invalid Link as source."""
        source = pywikibot.Link(self.not_existing_invalid['title'],
                                source=self.site)
        self.assertRaises(ValueError, ProofreadPage, source)

    def test_valid_link_source(self):
        """Test ProofreadPage from valid Link as source."""
        source = pywikibot.Link(
            self.valid['title'],
            source=self.site,
            defaultNamespace=self.site.proofread_page_ns)
        page = ProofreadPage(source)
        self.assertEqual(page.title(withNamespace=False), source.title)
        self.assertEqual(page.namespace(), source.namespace)

    def test_valid_parsing(self):
        """Test ProofreadPage page parsing functions."""
        page = ProofreadPage(self.site, self.valid['title'])
        self.assertEqual(page.ql, self.valid['ql'])
        self.assertEqual(page.user, self.valid['user'])
        self.assertEqual(page.header, self.valid['header'])
        self.assertEqual(page.footer, self.valid['footer'])

    def test_decompose_recompose_text(self):
        """Test ProofreadPage page decomposing/composing text."""
        page = ProofreadPage(self.site, self.valid['title'])
        plain_text = pywikibot.Page(self.site, self.valid['title']).text
        assert page.text
        self.assertEqual(plain_text, page.text)

    def test_preload_from_not_existing_page(self):
        """Test ProofreadPage page decomposing/composing text."""
        page = ProofreadPage(self.site, 'dummy test page')
        self.assertEqual(page.text,
                         '<noinclude><pagequality level="1" user="%s" />'
                         '<div class="pagetext">\n\n\n</noinclude>'
                         '<noinclude><references/></div></noinclude>'
                         % self.site.username())

    def test_preload_from_empty_text(self):
        """Test ProofreadPage page decomposing/composing text."""
        page = ProofreadPage(self.site, 'dummy test page')
        page.text = ''
        self.assertEqual(page.text,
                         '<noinclude><pagequality level="1" user="%s" />'
                         '<div class="pagetext">\n\n\n</noinclude>'
                         '<noinclude></div></noinclude>'
                         % self.site.username())

    def test_json_format(self):
        """Test conversion to json format."""
        page = ProofreadPage(self.site, self.valid['title'])

        rvargs = {'rvprop': 'ids|flags|timestamp|user|comment|content',
                  'rvcontentformat': 'application/json',
                  'titles': page,
                  }

        rvgen = self.site._generator(api.PropertyGenerator,
                                     type_arg='info|revisions',
                                     total=1, **rvargs)
        rvgen.set_maximum_items(-1)  # suppress use of rvlimit parameter

        try:
            pagedict = next(iter(rvgen))
            loaded_text = pagedict.get('revisions')[0].get('*')
        except (StopIteration, TypeError, KeyError, ValueError, IndexError):
            page_text = ''

        page_text = page._page_to_json()
        self.assertEqual(json.loads(page_text), json.loads(loaded_text))


@require_modules('bs4')
class IndexPageTestCase(TestCase):

    """Run tests related to IndexPage ProofreadPage extension."""

    pass


class TestIndexPageInvalidSite(IndexPageTestCase):

    """Test IndexPage class."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def test_invalid_site_source(self):
        """Test IndexPage from invalid Site as source."""
        self.assertRaises(pywikibot.UnknownExtension,
                          IndexPage, self.site, 'title')


class TestIndexPageValidSite(IndexPageTestCase):

    """Test IndexPage class."""

    family = 'wikisource'
    code = 'en'

    cached = True

    valid_index_title = 'Index:Popular Science Monthly Volume 1.djvu'
    existing_invalid_title = 'Main Page'
    not_existing_invalid_title = 'User:cannot_exists'

    def test_valid_site_as_source(self):
        """Test IndexPage from valid Site as source."""
        page = IndexPage(self.site, 'title')
        self.assertEqual(page.namespace(), self.site.proofread_index_ns)

    def test_invalid_existing_page_as_source(self):
        """Test IndexPage from invalid existing Page as source."""
        source = pywikibot.Page(self.site, self.existing_invalid_title)
        self.assertRaises(ValueError, IndexPage, source)

    def test_invalid_not_existing_page_as_source(self):
        """Test IndexPage from Page not existing in non-Page ns as source."""
        source = pywikibot.Page(self.site,
                                self.not_existing_invalid_title)
        self.assertRaises(ValueError, IndexPage, source)

    def test_invalid_link_as_source(self):
        """Test IndexPage from invalid Link as source."""
        source = pywikibot.Link(self.not_existing_invalid_title,
                                source=self.site)
        self.assertRaises(ValueError, IndexPage, source)

    def test_valid_link_as_source(self):
        """Test IndexPage from valid Link as source."""
        source = pywikibot.Link(self.valid_index_title,
                                source=self.site,
                                defaultNamespace=self.site.proofread_page_ns)
        page = IndexPage(source)
        self.assertEqual(page.title(withNamespace=False), source.title)
        self.assertEqual(page.namespace(), source.namespace)


class TestBasePageMethodsIndexPage(IndexPageTestCase, BasePageMethodsTestBase):

    """Test behavior of ProofreadPage methods inherited from BasePage."""

    family = 'wikisource'
    code = 'en'

    def setUp(self):
        """Set up test case."""
        self._page = IndexPage(
            self.site, 'Index:Popular Science Monthly Volume 1.djvu')
        super(TestBasePageMethodsIndexPage, self).setUp()

    def test_basepage_methods(self):
        """Test IndexPage methods inherited from superclass BasePage."""
        self._test_invoke()
        self._test_return_datatypes()


class TestLoadRevisionsCachingIndexPage(IndexPageTestCase,
                                        BasePageLoadRevisionsCachingTestBase):

    """Test site.loadrevisions() caching."""

    family = 'wikisource'
    code = 'en'

    def setUp(self):
        """Set up test case."""
        self._page = IndexPage(
            self.site, 'Index:Popular Science Monthly Volume 1.djvu')
        super(TestLoadRevisionsCachingIndexPage, self).setUp()

    def test_page_text(self):
        """Test site.loadrevisions() with Page.text."""
        self._test_page_text()


class TestIndexPageMappings(IndexPageTestCase):

    """Test IndexPage class."""

    sites = {
        'enws': {
            'family': 'wikisource',
            'code': 'en',
            'index': 'Popular Science Monthly Volume 1.djvu',
            'num_pages': 804,
            'page': 'Popular Science Monthly Volume 1.djvu/{0}',
            'get_label': [11, 11, '1'],
            'get_number': [[1, set([11])],
                           ['Cvr', set([1, 9, 10, 804])],
                           ],
            # 'get_page' is filled in setUpClass.
        },
        'dews': {  # dews does not use page convention name/number.
            'family': 'wikisource',
            'code': 'de',
            'index': 'Musen-Almanach für das Jahr 1799',
            'num_pages': 272,
            'page': 'Schiller_Musenalmanach_1799_{0:3d}.jpg',
            'get_label': [120, 120, '120'],  # page no, title no, label
            'get_number': [[120, set([120])],
                           ],
            # 'get_page' is filled in setUpClass.
        },
        'frws': {
            'family': 'wikisource',
            'code': 'fr',
            'index': 'Segard - Hymnes profanes, 1894.djvu',
            'num_pages': 107,
            'page': 'Segard - Hymnes profanes, 1894.djvu/{0}',
            'get_label': [11, 11, '8'],
            'get_number': [[8, set([11])],
                           ['-', set(range(1, 4)) | set(range(101, 108))],
                           ],
            # 'get_page' is filled in setUpClass.
        },
    }

    cached = True

    @classmethod
    def setUpClass(cls):
        """Prepare get_page dataset for tests."""
        super(TestIndexPageMappings, cls).setUpClass()
        for key, site_def in cls.sites.items():
            site = cls.get_site(name=key)
            base_title = site_def['page']

            # 'get_page' has same structure as 'get_number'.
            site_def['get_page'] = []
            for label, page_numbers in site_def['get_number']:
                page_set = set(ProofreadPage(site, base_title.format(i))
                               for i in page_numbers)
                site_def['get_page'].append([label, page_set])

    def test_num_pages(self, key):
        """Test num_pages property."""
        index_page = IndexPage(self.site, self.sites[key]['index'])
        self.assertEqual(index_page.num_pages, self.sites[key]['num_pages'])

    def test_get_labels(self, key):
        """Test IndexPage page get_label_from_* functions."""
        data = self.sites[key]
        num, title_num, label = data['get_label']

        index_page = IndexPage(self.site, self.sites[key]['index'])
        page_title = self.sites[key]['page'].format(title_num)
        proofread_page = ProofreadPage(self.site, page_title)

        # Get label from number.
        self.assertEqual(index_page.get_label_from_page_number(num), label)
        # Error if number does not exists.
        self.assertRaises(KeyError, index_page.get_label_from_page_number, -1)

        # Get label from page.
        self.assertEqual(index_page.get_label_from_page(proofread_page), label)
        # Error if page does not exists.
        self.assertRaises(KeyError, index_page.get_label_from_page, None)

    def test_get_page_and_number(self, key):
        """Test IndexPage page get_page_number functions."""
        data = self.sites[key]
        index_page = IndexPage(self.site, self.sites[key]['index'])

        # Test get_page_numbers_from_label.
        for label, num_set in data['get_number']:
            # Get set of numbers from label with label as int or str.
            self.assertEqual(index_page.get_page_number_from_label(label),
                             num_set)
            self.assertEqual(index_page.get_page_number_from_label(str(label)),
                             num_set)

        # Error if label does not exists.
        label, num_set = 'dummy label', []
        self.assertRaises(KeyError, index_page.get_page_number_from_label,
                          'dummy label')

        # Test get_page_from_label.
        for label, page_set in data['get_page']:
            # Get set of pages from label with label as int or str.
            self.assertEqual(index_page.get_page_from_label(label),
                             page_set)
            self.assertEqual(index_page.get_page_from_label(str(label)),
                             page_set)

        # Error if label does not exists.
        self.assertRaises(KeyError, index_page.get_page_from_label, 'dummy label')

        # Test consistency of page <-> numbers mapping on last page_set and
        # num_set used.
        for p in page_set:
            n = index_page._numbers_from_page[p]
            self.assertEqual(index_page._page_from_numbers[n], p)
        for n in num_set:
            p = index_page._page_from_numbers[n]
            self.assertEqual(index_page._numbers_from_page[p], n)

        # Test get_page_from_number.
        for n in num_set:
            p = index_page.get_page_from_number(n)
            self.assertEqual(index_page._numbers_from_page[p], n)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
