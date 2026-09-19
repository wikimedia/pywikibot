#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the PageViewInfo extension."""
from __future__ import annotations

from unittest.mock import Mock, patch

import pywikibot
from pywikibot.data import api
from tests.aspects import DefaultSiteTestCase


class TestPageViewInfo(DefaultSiteTestCase):

    """Test PageViewInfo methods against mocked API responses."""

    dry = True

    def test_pageviews(self) -> None:
        """Test retrieving views for a page."""
        page = pywikibot.Page(self.site, 'Special:Search')
        response = {
            'title': 'Special:Search',
            'pageviews': {'2026-09-17': 42, '2026-09-18': None},
        }

        with (
            patch.object(self.site, 'has_extension', return_value=True),
            patch.object(page, 'exists') as exists,
            patch.object(self.site, '_generator') as generator,
        ):
            generator.return_value.__iter__.return_value = iter((response,))
            result = page.pageviews()

        self.assertEqual(result, response['pageviews'])
        exists.assert_not_called()
        generator.assert_called_once_with(
            api.PropertyGenerator,
            type_arg='pageviews',
            titles='Special:Search',
            pvipmetric='pageviews',
        )

    def test_siteviews(self) -> None:
        """Test retrieving site-wide views."""
        request = Mock()
        response = {'2026-09-17': 42, '2026-09-18': 43}
        request.submit.return_value = {'query': {'siteviews': response}}

        with (
            patch.object(self.site, 'has_extension', return_value=True),
            patch.object(self.site, 'simple_request', return_value=request)
            as simple_request,
        ):
            result = self.site.siteviews(days=2, metric='uniques')

        self.assertEqual(result, response)
        simple_request.assert_called_once_with(
            action='query',
            meta='siteviews',
            pvisdays=2,
            pvismetric='uniques',
            formatversion=2,
        )

    def test_mostviewed(self) -> None:
        """Test retrieving the most viewed pages."""
        response = (
            {'title': 'Main Page', 'count': 42},
            {'title': 'Earth', 'count': 23},
        )

        with (
            patch.object(self.site, 'has_extension', return_value=True),
            patch.object(self.site, '_generator') as generator,
        ):
            generator.return_value.__iter__.return_value = iter(response)
            result = list(self.site.mostviewed(total=2))

        self.assertEqual(
            [(page.title(), count) for page, count in result],
            [('Main Page', 42), ('Earth', 23)],
        )
        generator.assert_called_once_with(
            api.ListGenerator,
            type_arg='mostviewed',
            total=2,
            pvimmetric='pageviews',
        )


if __name__ == '__main__':
    import unittest

    unittest.main()
