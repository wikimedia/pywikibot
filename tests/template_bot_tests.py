#!/usr/bin/env python3
#
# (C) Pywikibot team, 2015-2026
#
# Distributed under the terms of the MIT license.
#
"""Test template bot module."""
from __future__ import annotations

import unittest
from unittest.mock import call, patch

import pywikibot
from pywikibot import pagegenerators
from pywikibot.pagegenerators import XMLDumpPageGenerator
from pywikibot.textlib import MultiTemplateMatchBuilder
from scripts import template
from tests import join_xml_data_path
from tests.aspects import TestCase


class TestTemplateMain(TestCase):

    """Test :func:`template.main`."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def test_filter_uses_fallback_generator(self) -> None:
        """Test that filters do not suppress the fallback generator."""
        factory = pagegenerators.GeneratorFactory(site=self.site)
        fallback = [pywikibot.Page(self.site, 'Fallback')]
        with (
            patch.object(template.pywikibot, 'handle_args',
                         side_effect=lambda args: args),
            patch.object(template.pywikibot, 'Site', return_value=self.site),
            patch.object(template.pagegenerators, 'GeneratorFactory',
                         return_value=factory),
            patch.object(template.pywikibot.Page, 'getReferences',
                         return_value=fallback) as references,
            patch.object(factory, 'getCombinedGenerator',
                         wraps=factory.getCombinedGenerator) as combined,
            patch.object(template, 'TemplateRobot') as bot,
        ):
            template.main('-remove', '-namespace:0', 'Foo')

        self.assertFalse(factory.generator_specified)
        references.assert_called_once_with(
            only_template_inclusion=True, follow_redirects=False)
        self.assertEqual(combined.call_args_list[0], call())
        self.assertLength(combined.call_args_list, 2)
        bot.return_value.run.assert_called_once_with()

    def test_explicit_generator_suppresses_fallback(self) -> None:
        """Test that an explicit source suppresses the fallback."""
        factory = pagegenerators.GeneratorFactory(site=self.site)
        with (
            patch.object(template.pywikibot, 'handle_args',
                         side_effect=lambda args: args),
            patch.object(template.pywikibot, 'Site', return_value=self.site),
            patch.object(template.pagegenerators, 'GeneratorFactory',
                         return_value=factory),
            patch.object(template.pywikibot.Page, 'getReferences')
            as references,
            patch.object(factory, 'getCombinedGenerator',
                         wraps=factory.getCombinedGenerator) as combined,
            patch.object(template, 'TemplateRobot') as bot,
        ):
            template.main('-remove', '-page:Bar', 'Foo')

        self.assertTrue(factory.generator_specified)
        references.assert_not_called()
        combined.assert_called_once_with()
        bot.return_value.run.assert_called_once_with()


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

    def test_no_match(self) -> None:
        """Test pages without any desired templates."""
        self.assertIsEmpty(self.generator('foobar'))

    def test_match(self) -> None:
        """Test pages with one match without parameters."""
        pages = self.generator('stack begin')
        self.assertLength(pages, 1)
        self.assertPageTitlesEqual(pages, ['Pear'], site=self.site)

    def test_match_with_params(self) -> None:
        """Test pages with one match with parameters."""
        pages = self.generator('Taxobox')
        self.assertLength(pages, 1)
        self.assertPageTitlesEqual(pages, ['Pear'], site=self.site)

    def test_match_any(self) -> None:
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

    def test_match_msg(self) -> None:
        """Test pages with {{msg:..}}."""
        pages = self.generator('Foo', 'dummy-template.xml')
        self.assertLength(pages, 1)
        self.assertPageTitlesEqual(pages, ['Fake page with msg'],
                                   site=self.site)

    def test_match_unnecessary_template_prefix(self) -> None:
        """Test pages with {{template:..}}."""
        pages = self.generator('Bar', 'dummy-template.xml')
        self.assertLength(pages, 1)
        self.assertPageTitlesEqual(
            pages, ['Fake page with unnecessary template prefix'],
            site=self.site)

    def test_nested_match(self) -> None:
        """Test pages with one match inside another template."""
        pages = self.generator('boo', 'dummy-template.xml')
        self.assertLength(pages, 1)
        self.assertPageTitlesEqual(
            pages, ['Fake page with nested template'],
            site=self.site)


if __name__ == '__main__':
    unittest.main()
