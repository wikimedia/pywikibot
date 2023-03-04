#!/usr/bin/env python3
"""Test template bot module."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import unittest

import pywikibot
from pywikibot.pagegenerators import XMLDumpPageGenerator
from pywikibot.textlib import MultiTemplateMatchBuilder
from tests import join_xml_data_path
from tests.aspects import TestCase


class TestXMLPageGenerator(TestCase):

    """Test XML Page generator."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def generator(self, title, xml='article-pear-0.10.xml'):
        """Return XMLDumpPageGenerator list for a given template title."""
        template = pywikibot.Page(self.site, title, ns=10)
        builder = MultiTemplateMatchBuilder(self.site)
        predicate = builder.search_any_predicate([template])
        gen = XMLDumpPageGenerator(
            filename=join_xml_data_path(xml),
            site=self.site,
            text_predicate=predicate)
        return list(gen)

    def test_no_match(self):
        """Test pages without any desired templates."""
        self.assertIsEmpty(self.generator('foobar'))

    def test_match(self):
        """Test pages with one match without parameters."""
        pages = self.generator('stack begin')
        self.assertLength(pages, 1)
        self.assertPageTitlesEqual(pages, ['Pear'], site=self.site)

    def test_match_with_params(self):
        """Test pages with one match with parameters."""
        pages = self.generator('Taxobox')
        self.assertLength(pages, 1)
        self.assertPageTitlesEqual(pages, ['Pear'], site=self.site)

    def test_match_any(self):
        """Test pages with one of many matches."""
        template1 = pywikibot.Page(self.site, 'Template:stack begin')
        template2 = pywikibot.Page(self.site, 'Template:foobar')
        builder = MultiTemplateMatchBuilder(self.site)

        predicate = builder.search_any_predicate([template1, template2])
        gen = XMLDumpPageGenerator(
            filename=join_xml_data_path('article-pear-0.10.xml'),
            site=self.site,
            text_predicate=predicate)
        pages = list(gen)
        self.assertLength(pages, 1)
        self.assertPageTitlesEqual(pages, ['Pear'], site=self.site)

        # reorder templates
        predicate = builder.search_any_predicate([template2, template1])
        gen = XMLDumpPageGenerator(
            filename=join_xml_data_path('article-pear-0.10.xml'),
            site=self.site,
            text_predicate=predicate)
        pages = list(gen)
        self.assertLength(pages, 1)
        self.assertPageTitlesEqual(pages, ['Pear'], site=self.site)

    def test_match_msg(self):
        """Test pages with {{msg:..}}."""
        pages = self.generator('Foo', 'dummy-template.xml')
        self.assertLength(pages, 1)
        self.assertPageTitlesEqual(pages, ['Fake page with msg'],
                                   site=self.site)

    def test_match_unnecessary_template_prefix(self):
        """Test pages with {{template:..}}."""
        pages = self.generator('Bar', 'dummy-template.xml')
        self.assertLength(pages, 1)
        self.assertPageTitlesEqual(
            pages, ['Fake page with unnecessary template prefix'],
            site=self.site)

    def test_nested_match(self):
        """Test pages with one match inside another template."""
        pages = self.generator('boo', 'dummy-template.xml')
        self.assertLength(pages, 1)
        self.assertPageTitlesEqual(
            pages, ['Fake page with nested template'],
            site=self.site)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
