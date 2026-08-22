#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the touch script."""
from __future__ import annotations

import unittest
from contextlib import suppress
from unittest.mock import patch

from pywikibot import pagegenerators
from scripts import touch
from tests.aspects import TestCase


class TestTouchMain(TestCase):

    """Test :func:`touch.main`."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def _suggest_help(self, *args: str):
        """Run touch and return the suggest_help mock."""
        factory = pagegenerators.GeneratorFactory(site=self.site)
        with (
            patch.object(touch.pywikibot, 'handle_args', return_value=args),
            patch.object(touch.pagegenerators, 'GeneratorFactory',
                         return_value=factory),
            patch.object(touch.pywikibot.bot, 'suggest_help',
                         return_value=True) as suggest_help,
        ):
            touch.main(*args)

        return suggest_help

    def test_start_is_generator(self) -> None:
        """Test that -start is treated as a generator source."""
        suggest_help = self._suggest_help('-start:!')
        suggest_help.assert_called_once_with(
            missing_generator=False, unknown_parameters=[])

    def test_namespace_is_not_generator(self) -> None:
        """Test that -namespace alone is not a generator source."""
        suggest_help = self._suggest_help('-namespace:0')
        suggest_help.assert_called_once_with(
            missing_generator=True, unknown_parameters=[])


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
