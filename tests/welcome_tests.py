#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the welcome script."""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from scripts import welcome
from tests.aspects import TestCase


class TestWelcomeBot(TestCase):

    """Test :class:`welcome.WelcomeBot`."""

    net = False

    def test_signature_file_closed_on_read_error(self) -> None:
        """Test that the signature file is closed when reading fails."""
        file_obj = MagicMock()
        file_obj.__enter__.return_value = file_obj
        file_obj.read.side_effect = OSError

        with (
            patch.object(
                welcome.globalvar, 'sign_file_name', 'signatures.txt'),
            patch.object(welcome.pywikibot.config, 'datafilepath',
                         return_value='signatures.txt'),
            patch('builtins.open', return_value=file_obj),
            self.assertRaises(OSError),
        ):
            welcome.WelcomeBot.define_sign(SimpleNamespace())

        file_obj.__exit__.assert_called_once()


if __name__ == '__main__':
    unittest.main()
