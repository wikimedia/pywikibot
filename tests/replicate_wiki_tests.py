#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the replicate_wiki script."""
from __future__ import annotations

import unittest
from collections import defaultdict
from types import SimpleNamespace
from unittest.mock import Mock, patch

from scripts import replicate_wiki
from tests.aspects import TestCase


class TestSyncSites(TestCase):

    """Test replication to multiple destination wikis."""

    net = False
    site = False

    def test_replacements_are_per_destination(self) -> None:
        """Apply each destination's replacements to the original text."""
        bot = object.__new__(replicate_wiki.SyncSites)
        bot.original = 'source'
        bot.sites = ('first', 'second', 'unchanged')
        bot.options = SimpleNamespace(dest_namespace=None, replace=True)
        bot.differences = defaultdict(list)
        bot.put_message = Mock(return_value='Sync summary')
        pages = {
            'source': Mock(text='original'),
            'first': Mock(text='original'),
            'second': Mock(text='second text'),
            'unchanged': Mock(text='original'),
        }
        replacements = {
            'first': {'original': 'first text'},
            'second': {'original': 'second text'},
        }

        with patch.object(replicate_wiki, 'Page',
                          side_effect=lambda site, title: pages[site]), \
             patch.object(replicate_wiki.config, 'replicate_replace',
                          replacements):
            bot.check_page('Example')

        self.assertEqual([pages[site].text for site in bot.sites],
                         ['first text', 'second text', 'original'])
        self.assertEqual(bot.differences, {'first': ['Example']})


if __name__ == '__main__':
    unittest.main()
