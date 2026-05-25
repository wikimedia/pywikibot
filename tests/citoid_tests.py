#!/usr/bin/env python3
#
# (C) Pywikibot team, 2025-2026
#
# Distributed under the terms of the MIT license.
#
"""Unit tests for citoid script."""
from __future__ import annotations

import datetime
import unittest

import pywikibot
from pywikibot.data import citoid
from pywikibot.exceptions import ApiNotAvailableError
from tests.aspects import TestCase


class TestCitoid(TestCase):

    """Test the Citoid client."""

    family = 'wikipedia'
    code = 'test'
    login = False

    def test_citoid_positive(self):
        """Test citoid script."""
        client = citoid.CitoidClient(self.site)
        resp = client.get_citation(
            'mediawiki',
            'https://ro.wikipedia.org/wiki/România'
        )
        self.assertLength(resp, 1)
        self.assertEqual(resp[0]['title'], 'România')
        self.assertEqual(
            resp[0]['rights'],
            'Creative Commons Attribution-ShareAlike License'
        )
        self.assertIsNotEmpty(resp[0]['url'])
        self.assertEqual(
            resp[0]['accessDate'],
            datetime.datetime.now().strftime('%Y-%m-%d')
        )

    def test_citoid_no_config(self):
        """Test citoid script with no citoid endpoint configured."""
        client = citoid.CitoidClient(pywikibot.Site('wikiquote:pl'))
        with self.assertRaisesRegex(
            ApiNotAvailableError,
            'Citoid endpoint not configured for wikiquote'
        ):
            client.get_citation(
                'mediawiki',
                'https://ro.wikipedia.org/wiki/România'
            )

    def test_citoid_no_valid_format(self):
        """Test citoid script with invalid format provided."""
        client = citoid.CitoidClient(self.site)
        with self.assertRaisesRegex(ValueError, 'Invalid format mediawiki2'):
            client.get_citation(
                'mediawiki2',
                'https://ro.wikipedia.org/wiki/România'
            )


if __name__ == '__main__':
    unittest.main()
