# -*- coding: utf-8 -*-
"""Tests for the category bot script."""
#
# (C) Pywikibot team, 2015-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import pywikibot
from pywikibot import BaseSite

from scripts.category import CategoryPreprocess, CategoryMoveRobot

from tests import patch, Mock
from tests.aspects import unittest, DefaultSiteTestCase, TestCase


MOCKED_USERNAME = Mock(return_value='FakeUsername')


# Temporarily set a username to circumvent NoUsername error; T161692
@patch.object(BaseSite, 'username', new=MOCKED_USERNAME)
class CfdActions(DefaultSiteTestCase):

    """Test CFD (Categories for deletion) actions."""

    def test_strip_cfd_templates_does_nothing_when_no_templates(self):
        """Test that when there are no CFD templates, the page text is not changed."""
        bot = CategoryMoveRobot(oldcat='Old', newcat='New')
        bot.newcat.text = "Nothing should change.\n\nAnother line."
        bot._strip_cfd_templates(commit=False)
        self.assertEqual(bot.newcat.text,
                         "Nothing should change.\n\nAnother line.")

    def test_strip_cfd_templates_with_spaces_in_comments(self):
        """Test that CFD templates with spaces in the syntax are removed properly."""
        self._runtest_strip_cfd_templates('<!-- BEGIN CFD TEMPLATE -->',
                                          '<!-- END CFD TEMPLATE -->')

    def test_strip_cfd_templates_without_spaces_in_comments(self):
        """Test that CFD templates without spaces in the syntax are removed properly."""
        self._runtest_strip_cfd_templates('<!--BEGIN CFD TEMPLATE-->',
                                          '<!--END CFD TEMPLATE-->')

    def _runtest_strip_cfd_templates(self, template_start, template_end):
        """Run a CFD template stripping test with the given CFD start/end templates."""
        bot = CategoryMoveRobot(oldcat='Old', newcat='New')
        bot.newcat.text = '\n'.join((
            'Preamble',
            template_start,
            'Random text inside template',
            'Even another template: {{cfr-speedy}}',
            template_end,
            'Footer stuff afterwards',
            '',
            '[[Category:Should remain]]'
        ))
        expected = '\n'.join((
            'Preamble',
            'Footer stuff afterwards',
            '',
            '[[Category:Should remain]]'
        ))
        bot._strip_cfd_templates(commit=False)
        self.assertEqual(bot.newcat.text, expected)


class TestPreprocessingCategory(TestCase):
    """Test determining template or type categorization target."""

    family = 'wikipedia'
    code = 'en'

    def test_determine_type_target(self):
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
        self.assertEqual(new_page, None)

        page = pywikibot.Page(self.site, 'Template:Baz')
        bot = CategoryPreprocess()
        bot.site = self.site
        new_page = bot.determine_type_target(page)
        self.assertEqual(new_page, None)

    def test_determine_template_target(self):
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


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
