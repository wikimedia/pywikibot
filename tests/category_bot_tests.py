#!/usr/bin/env python3
#
# (C) Pywikibot team, 2015-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the category bot script."""
from __future__ import annotations

import unittest
from contextlib import suppress
from unittest.mock import Mock, patch

import pywikibot
from pywikibot.site import BaseSite
from scripts import category
from scripts.category import CategoryMoveRobot, CategoryPreprocess
from tests.aspects import DefaultSiteTestCase, TestCase


MOCKED_USERNAME = Mock(return_value='FakeUsername')


# Temporarily set a username to circumvent NoUsernameError; T161692
@patch.object(BaseSite, 'username', new=MOCKED_USERNAME)
class CfdActions(DefaultSiteTestCase):

    """Test CFD (Categories for deletion) actions."""

    def test_strip_cfd_templates_does_nothing_when_no_templates(self) -> None:
        """Test when the're no CFD templates, the page text is not changed."""
        bot = CategoryMoveRobot(oldcat='Old', newcat='New')
        bot.newcat.text = 'Nothing should change.\n\nAnother line.'
        bot._strip_cfd_templates(commit=False)
        self.assertEqual(bot.newcat.text,
                         'Nothing should change.\n\nAnother line.')

    def test_strip_cfd_templates_with_spaces_in_comments(self) -> None:
        """Test CFD templates with spaces in the syntax are removed."""
        self._runtest_strip_cfd_templates('<!-- BEGIN CFD TEMPLATE -->',
                                          '<!-- END CFD TEMPLATE -->')

    def test_strip_cfd_templates_without_spaces_in_comments(self) -> None:
        """Test CFD templates without spaces in the syntax are removed."""
        self._runtest_strip_cfd_templates('<!--BEGIN CFD TEMPLATE-->',
                                          '<!--END CFD TEMPLATE-->')

    def _runtest_strip_cfd_templates(self,
                                     template_start,
                                     template_end) -> None:
        """Run a CFD template stripping test, given CFD start/end templates."""
        bot = CategoryMoveRobot(oldcat='Old', newcat='New')
        bot.newcat.text = (
            f'Preamble\n{template_start}\nRandom text inside template\n'
            f'Even another template: {{{{cfr-speedy}}}}\n{template_end}\n'
            f'Footer stuff afterwards\n\n[[Category:Should remain]]'
        )
        expected = ('Preamble\nFooter stuff afterwards\n\n'
                    '[[Category:Should remain]]')
        bot._strip_cfd_templates(commit=False)
        self.assertEqual(bot.newcat.text, expected)


class TestPreprocessingCategory(TestCase):

    """Test determining template or type categorization target."""

    family = 'wikipedia'
    code = 'en'

    def test_determine_type_target(self) -> None:
        """Test determining type target."""
        page = pywikibot.Page(self.site, 'Template:Doc')
        bot = CategoryPreprocess(follow_redirects=True)
        bot.site = self.site
        new_page = bot.determine_type_target(page)
        expected = pywikibot.Page(self.site, 'Template:Documentation')
        self.assertEqual(new_page, expected)

        page = pywikibot.Page(self.site, 'Template:Doc')
        bot = CategoryPreprocess()
        bot.site = self.site
        new_page = bot.determine_type_target(page)
        self.assertIsNone(new_page)

        page = pywikibot.Page(self.site, 'Template:Baz')
        bot = CategoryPreprocess()
        bot.site = self.site
        new_page = bot.determine_type_target(page)
        self.assertIsNone(new_page)

    def test_determine_template_target(self) -> None:
        """Test determining template target."""
        page = pywikibot.Page(self.site, 'Template:Documentation')
        bot = CategoryPreprocess()
        bot.site = self.site
        new_page = bot.determine_template_target(page)
        expected = pywikibot.Page(self.site, 'Template:Documentation/doc')
        self.assertEqual(new_page, expected)
        self.assertEqual(bot.includeonly, ['includeonly'])

        page = pywikibot.Page(self.site, 'Template:Branches of chemistry')
        bot = CategoryPreprocess()
        bot.site = self.site
        new_page = bot.determine_template_target(page)
        expected = pywikibot.Page(self.site, 'Template:Branches of chemistry')
        self.assertEqual(new_page, expected)
        self.assertEqual(bot.includeonly, [])


class TestCategoryArguments(TestCase):

    """Test category script argument handling."""

    net = False

    @patch.object(category.pywikibot, 'handle_args', side_effect=lambda x: x)
    def test_parse_args(self, handle_args) -> None:
        """Test parsing category and generator options."""
        args = (
            'move', '-nodelete', '-person', '-rebuild', '-from:Old_cat',
            '-to:New_cat', '-batch', '-inplace', '-nodelsum', '-append',
            '-overwrite', '-showimages', '-summary:summary', '-match:title',
            '-talkpages', '-recurse:2', '-pagesonly', '-nowb', '-allowsplit',
            '-mvtogether', '-create', '-redirect', '-hist', '-depth:7',
            '-keepsortkey', '-prefix:#', '-always', '-page:Example',
            'unknown',
        )

        settings = category._parse_args(args)

        handle_args.assert_called_once_with(args)
        self.assertEqual(settings.action, 'move')
        self.assertEqual(settings.options, {
            'always': True,
            'from': 'Old cat',
            'prefix': '#',
            'recurse': 2,
            'to': 'New cat',
        })
        expected = {
            'allow_split': True,
            'append': True,
            'batch': True,
            'create_pages': True,
            'delete_empty_cat': False,
            'depth': 7,
            'follow_redirects': True,
            'history': True,
            'inplace': True,
            'keep_sortkey': True,
            'move_together': True,
            'overwrite': True,
            'pagesonly': True,
            'rebuild': True,
            'showimages': True,
            'sort_by_last_name': True,
            'summary': 'summary',
            'talkpages': True,
            'title_regex': 'title',
            'use_deletion_summary': False,
            'wikibase': False,
        }
        for name, value in expected.items():
            with self.subTest(option=name):
                self.assertEqual(getattr(settings, name), value)
        self.assertEqual(settings.generator_args, ['-page:Example'])
        self.assertEqual(settings.unknown, ['unknown'])

        with patch.object(category.pywikibot, 'input', return_value='title'):
            settings = category._parse_args(('listify', '-match', '-recurse'))
        self.assertEqual(settings.title_regex, 'title')
        self.assertIs(settings.options['recurse'], True)

    def test_configure_generator_factory(self) -> None:
        """Test generator option support for category actions."""
        for action, enabled in (
            ('listify', ['namespace']),
            ('move', None),
        ):
            with (
                self.subTest(action=action),
                patch.object(category.pagegenerators,
                             'GeneratorFactory') as factory_class,
            ):
                factory = factory_class.return_value
                factory.handle_args.return_value = ['-unknown']
                settings = category._CategorySettings(
                    action=action, generator_args=['-page:Example'])

                result = category._configure_generator_factory(settings)

                self.assertIs(result, factory)
                factory_class.assert_called_once_with(
                    enabled_options=enabled)
                factory.handle_args.assert_called_once_with(
                    ['-page:Example'])
                self.assertEqual(settings.unknown, ['-unknown'])

        settings = category._CategorySettings(
            action='tree', generator_args=['-page:Example'])
        with patch.object(category.pagegenerators,
                          'GeneratorFactory') as factory_class:
            result = category._configure_generator_factory(settings)
        self.assertIsNone(result)
        factory_class.assert_not_called()
        self.assertEqual(settings.unknown, ['-page:Example'])


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
