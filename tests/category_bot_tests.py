# -*- coding: utf-8 -*-
"""Tests for the category bot script."""
#
# (C) Pywikibot team, 2015-2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

try:
    from unittest.mock import patch, Mock
except ImportError:
    from mock import patch, Mock

from pywikibot import BaseSite

from scripts.category import CategoryMoveRobot

from tests.aspects import unittest, DefaultSiteTestCase


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


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
