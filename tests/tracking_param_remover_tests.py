#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Unit tests for scripts.tracking_param_remover."""
from __future__ import annotations

import unittest
import urllib.parse
from contextlib import suppress

from scripts.tracking_param_remover import (
    TrackingParamRemoverBot,
    is_archive_url,
)
from tests.aspects import TestCase


class TestIsArchiveUrl(TestCase):

    """Test archive URL detection."""

    net = False

    def _parse(self, url: str) -> urllib.parse.ParseResult:
        return urllib.parse.urlparse(url)

    def test_archive_hosts(self) -> None:
        """Known archive hosts are detected."""
        urls = (
            'https://web.archive.org/web/20200101000000/'
            'https://example.com/?utm_source=x',
            'https://www.web.archive.org/web/2020/'
            'https://example.com/?fbclid=1',
            'https://archive.is/abc?utm_source=x',
            'https://archive.ph/abc?gclid=1',
            'https://archive.today/abc?si=1',
            'https://www.archive.today/abc?si=1',
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertTrue(is_archive_url(self._parse(url)))

    def test_wayback_path_on_archive_org(self) -> None:
        """archive.org Wayback paths are treated as archives."""
        url = (
            'https://archive.org/web/20200101000000/'
            'https://example.com/?utm_source=x'
        )
        self.assertTrue(is_archive_url(self._parse(url)))

    def test_non_archive(self) -> None:
        """Ordinary hosts are not treated as archives."""
        for url in (
            'https://example.com/?utm_source=x',
            'https://archive.org/details/foo?utm_source=x',
            'https://not-archive.is.example.com/?utm_source=x',
        ):
            with self.subTest(url=url):
                self.assertFalse(is_archive_url(self._parse(url)))


class TestRemoveTrackingParams(TestCase):

    """Test TrackingParamRemoverBot.remove_tracking_params."""

    net = False

    def _remove(self, url: str) -> str:
        return TrackingParamRemoverBot.remove_tracking_params(
            urllib.parse.urlparse(url))

    def test_removes_trackers(self) -> None:
        """Tracking parameters are stripped from normal URLs."""
        result = self._remove(
            'https://example.com/page?id=1&utm_source=x&ok=2')
        parsed = urllib.parse.urlparse(result)
        params = dict(urllib.parse.parse_qsl(parsed.query))
        self.assertEqual(params, {'id': '1', 'ok': '2'})

    def test_preserves_archive_trackers(self) -> None:
        """Tracking parameters on archive URLs are preserved."""
        urls = (
            'https://web.archive.org/web/2020/'
            'https://example.com/?utm_source=x',
            'https://archive.is/foo?fbclid=abc',
            'https://archive.ph/foo?gclid=1',
            'https://archive.today/foo?si=1',
            'https://archive.org/web/2020/'
            'https://example.com/?utm_source=x',
        )
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self._remove(url), url)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
