# -*- coding: utf-8 -*-
"""Test template bot module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import pywikibot

from pywikibot.pagegenerators import XMLDumpPageGenerator
from pywikibot.textlib import _MultiTemplateMatchBuilder

from tests import join_xml_data_path
from tests.aspects import unittest, TestCase


class TestXMLPageGenerator(TestCase):

    """Test XML Page generator."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def test_no_match(self):
        """Test pages without any desired templates."""
        template = pywikibot.Page(self.site, 'Template:foobar')
        builder = _MultiTemplateMatchBuilder(self.site)
        predicate = builder.search_any_predicate([template])
        gen = XMLDumpPageGenerator(
            filename=join_xml_data_path('article-pear-0.10.xml'),
            site=self.site,
            text_predicate=predicate)
        pages = list(gen)
        self.assertEqual(len(pages), 0)

    def test_match(self):
        """Test pages with one match without parameters."""
        template = pywikibot.Page(self.site, 'Template:stack begin')
        builder = _MultiTemplateMatchBuilder(self.site)
        predicate = builder.search_any_predicate([template])
        gen = XMLDumpPageGenerator(
            filename=join_xml_data_path('article-pear-0.10.xml'),
            site=self.site,
            text_predicate=predicate)
        pages = list(gen)
        self.assertEqual(len(pages), 1)
        self.assertPagelistTitles(pages, ['Pear'],
                                  site=self.site)

    def test_match_with_params(self):
        """Test pages with one match with parameters."""
        template = pywikibot.Page(self.site, 'Template:Taxobox')
        builder = _MultiTemplateMatchBuilder(self.site)
        predicate = builder.search_any_predicate([template])
        gen = XMLDumpPageGenerator(
            filename=join_xml_data_path('article-pear-0.10.xml'),
            site=self.site,
            text_predicate=predicate)
        pages = list(gen)
        self.assertEqual(len(pages), 1)
        self.assertPagelistTitles(pages, ['Pear'],
                                  site=self.site)

    def test_match_any(self):
        """Test pages with one of many matches."""
        template1 = pywikibot.Page(self.site, 'Template:stack begin')
        template2 = pywikibot.Page(self.site, 'Template:foobar')
        builder = _MultiTemplateMatchBuilder(self.site)

        predicate = builder.search_any_predicate([template1, template2])
        gen = XMLDumpPageGenerator(
            filename=join_xml_data_path('article-pear-0.10.xml'),
            site=self.site,
            text_predicate=predicate)
        pages = list(gen)
        self.assertEqual(len(pages), 1)
        self.assertPagelistTitles(pages, ['Pear'],
                                  site=self.site)

        # reorder templates
        predicate = builder.search_any_predicate([template2, template1])
        gen = XMLDumpPageGenerator(
            filename=join_xml_data_path('article-pear-0.10.xml'),
            site=self.site,
            text_predicate=predicate)
        pages = list(gen)
        self.assertEqual(len(pages), 1)
        self.assertPagelistTitles(pages, ['Pear'],
                                  site=self.site)

    def test_match_msg(self):
        """Test pages with {{msg:..}}."""
        template = pywikibot.Page(self.site, 'Template:Foo')
        builder = _MultiTemplateMatchBuilder(self.site)

        predicate = builder.search_any_predicate([template])
        gen = XMLDumpPageGenerator(
            filename=join_xml_data_path('dummy-template.xml'),
            site=self.site,
            text_predicate=predicate)
        pages = list(gen)
        self.assertEqual(len(pages), 1)
        self.assertPagelistTitles(pages, ['Fake page with msg'],
                                  site=self.site)

    def test_match_unnecessary_template_prefix(self):
        """Test pages with {{template:..}}."""
        template = pywikibot.Page(self.site, 'Template:Bar')
        builder = _MultiTemplateMatchBuilder(self.site)

        predicate = builder.search_any_predicate([template])
        gen = XMLDumpPageGenerator(
            filename=join_xml_data_path('dummy-template.xml'),
            site=self.site,
            text_predicate=predicate)
        pages = list(gen)
        self.assertEqual(len(pages), 1)
        self.assertPagelistTitles(
            pages, ['Fake page with unnecessary template prefix'],
            site=self.site)

    def test_nested_match(self):
        """Test pages with one match inside another template."""
        template = pywikibot.Page(self.site, 'Template:boo')
        builder = _MultiTemplateMatchBuilder(self.site)
        predicate = builder.search_any_predicate([template])
        gen = XMLDumpPageGenerator(
            filename=join_xml_data_path('dummy-template.xml'),
            site=self.site,
            text_predicate=predicate)
        pages = list(gen)
        self.assertEqual(len(pages), 1)
        self.assertPagelistTitles(
            pages, ['Fake page with nested template'],
            site=self.site)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
