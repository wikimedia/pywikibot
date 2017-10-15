# -*- coding: utf-8 -*-
"""Test Interwiki Link functionality."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import config2 as config

from pywikibot.exceptions import InvalidTitle
from pywikibot.page import Link

from tests.aspects import (
    unittest,
    AlteredDefaultSiteTestCase as LinkTestCase,
    TestCase,
)


class TestPartiallyQualifiedLinkDifferentCodeParser(LinkTestCase):

    """Tests for interwiki links to local sites."""

    family = 'wikipedia'
    code = 'en'
    cached = True

    def test_partially_qualified_NS0_family(self):
        """Test that Link uses config.family for namespace 0."""
        config.mylang = 'de'
        config.family = 'wikipedia'
        link = Link('en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_family(self):
        """Test that Link uses config.family for namespace 1."""
        config.mylang = 'de'
        config.family = 'wikipedia'
        link = Link('en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


class TestInterwikiLinksToNonLocalSites(TestCase):

    """Tests for interwiki links to non local sites."""

    sites = {
        'wp': {
            'family': 'wikipedia',
            'code': 'en'
        },
        'tw': {
            'family': 'i18n',
            'code': 'i18n'
        }
    }

    def test_direct_non_local(self):
        """Test translatewiki:Main Page on English Wikipedia."""
        link = Link('translatewiki:Main Page', self.get_site('wp'))
        link.parse()
        self.assertEqual(link.site, self.get_site('tw'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_indirect_non_local(self):
        """Test en:translatewiki:Main Page on English Wikipedia."""
        link = Link('en:translatewiki:Main Page', self.get_site('wp'))
        link.parse()
        self.assertEqual(link.site, self.get_site('tw'))
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_via_local_non_local(self):
        """Test de:translatewiki:Main Page on English Wikipedia."""
        link = Link('de:translatewiki:Main Page', self.get_site('wp'))
        self.assertRaisesRegex(
            InvalidTitle,
            "de:translatewiki:Main Page links to a non local site i18n:i18n "
            "via an interwiki link to wikipedia:de",
            link.parse)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
