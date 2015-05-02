# -*- coding: utf-8  -*-
"""Tests for the proofreadpage module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import pywikibot
from pywikibot.proofreadpage import ProofreadPage

from tests.aspects import unittest, TestCase


class TestProofreadPageInvalidSite(TestCase):

    """Test ProofreadPage class."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def test_invalid_site_source(self):
        """Test ProofreadPage from invalid Site as source."""
        self.assertRaises(pywikibot.UnknownExtension,
                          ProofreadPage, self.site, 'title')


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

    def test_invalid_existing_page_source_in_valid_site(self):
        """Test ProofreadPage from invalid existing Page as source."""
        source = pywikibot.Page(self.site, self.existing_invalid['title'])
        self.assertRaises(ValueError, ProofreadPage, source)

    def test_invalid_not_existing_page_source_in_valid_site(self):
        """Test ProofreadPage from invalid not existing Page as source."""
        # namespace is forced
        source = pywikibot.Page(self.site,
                                self.not_existing_invalid['title'])
        fixed_source = pywikibot.Page(self.site,
                                      source.title(withNamespace=False),
                                      ns=self.site.proofread_page_ns)
        page = ProofreadPage(fixed_source)
        self.assertEqual(page.title(), fixed_source.title())

    def test_invalid_not_existing_page_source_in_valid_site_wrong_ns(self):
        """Test ProofreadPage from Page not existing in non-Page ns as source."""
        source = pywikibot.Page(self.site,
                                self.not_existing_invalid['title1'])
        self.assertRaises(ValueError, ProofreadPage, source)

    def test_invalid_link_source_in_valid_site(self):
        """Test ProofreadPage from invalid Link as source."""
        source = pywikibot.Link(self.not_existing_invalid['title'],
                                source=self.site)
        self.assertRaises(ValueError, ProofreadPage, source)

    def test_valid_link_source_in_valid_site(self):
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
        assert(page.text)
        self.assertEqual(plain_text, page.text)

    def test_preload_from_not_existing_page(self):
        """Test ProofreadPage page decomposing/composing text."""
        page = ProofreadPage(self.site, 'dummy test page')
        self.assertEqual(page.text,
                         '<noinclude><pagequality level="1" user="" />'
                         '<div class="pagetext">\n\n\n</noinclude>'
                         '<noinclude><references/></div></noinclude>')

    def test_preload_from_empty_text(self):
        """Test ProofreadPage page decomposing/composing text."""
        page = ProofreadPage(self.site, 'dummy test page')
        page.text = ''
        self.assertEqual(page.text,
                         '<noinclude><pagequality level="1" user="" />'
                         '<div class="pagetext">\n\n\n</noinclude>'
                         '<noinclude></div></noinclude>')

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
