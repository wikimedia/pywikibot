#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the imagetransfer script."""
from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from scripts.imagetransfer import main
from tests.aspects import TestCase


class TestImageTransferMain(TestCase):

    """Test cases for the imagetransfer script."""

    net = False

    def test_chunk_size(self) -> None:
        """Test that the chunk size is passed as an integer."""
        generator = object()
        factory = Mock()
        factory.getCombinedGenerator.return_value = generator

        with patch('scripts.imagetransfer.pywikibot.handle_args',
                   return_value=['-chunk_size:1024']), \
             patch('scripts.imagetransfer.pagegenerators.GeneratorFactory',
                   return_value=factory), \
             patch('scripts.imagetransfer.ImageTransferBot') as bot_class:
            main()

        bot_class.assert_called_once_with(generator=generator,
                                          chunk_size=1024)
        bot_class.return_value.run.assert_called_once_with()


if __name__ == '__main__':
    unittest.main()
