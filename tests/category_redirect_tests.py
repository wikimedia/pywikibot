#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the category_redirect script."""
from __future__ import annotations

import unittest
from unittest.mock import patch

from scripts import category_redirect
from tests.aspects import TestCase


class CategoryRedirectMainTestCase(TestCase):

    """Test :func:`category_redirect.main`."""

    net = False

    @patch.object(category_redirect, 'CategoryRedirectBot')
    @patch.object(category_redirect.pywikibot.bot, 'suggest_help',
                  return_value=False)
    @patch.object(category_redirect.pywikibot, 'handle_args',
                  side_effect=lambda args: args)
    def test_delay_option(self, _, __, bot_mock) -> None:
        """Test that the delay option is passed as an integer."""
        category_redirect.main('-delay:14')

        bot_mock.assert_called_once_with(delay=14)


if __name__ == '__main__':
    unittest.main()
