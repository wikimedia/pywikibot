#!/usr/bin/env python3
"""Memento client test module."""
#
# (C) Pywikibot team, 2015-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest
from contextlib import suppress
from datetime import datetime
from urllib.parse import urlparse

from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import ReadTimeout

from tests.aspects import TestCase, require_modules
from tests.utils import skipping


@require_modules('memento_client')
class MementoTestCase(TestCase):

    """Test memento client."""

    def _get_archive_url(self, url, date_string=None):
        from pywikibot.data.memento import (
            MementoClientException,
            get_closest_memento_url,
        )

        when = (datetime.strptime(date_string, '%Y%m%d')
                if date_string else None)
        with skipping(ReadTimeout, RequestsConnectionError,
                      MementoClientException):
            return get_closest_memento_url(url, when, self.timegate_uri)


class TestMementoArchive(MementoTestCase):

    """Web Archive Memento tests."""

    timegate_uri = 'https://web.archive.org/web/'
    hostname = timegate_uri

    def test_newest(self) -> None:
        """Test Archive for an old https://google.com."""
        dt = '20220715'
        archivedversion = self._get_archive_url('https://google.com',
                                                date_string=dt)
        parsed = urlparse(archivedversion)
        self.assertIn(parsed.scheme, ['http', 'https'])


class TestMementoDefault(MementoTestCase):

    """Test Web Archive is default Memento timegate."""

    timegate_uri = None
    net = True

    def test_newest(self) -> None:
        """Test getting memento for newest https://google.com."""
        archivedversion = self._get_archive_url('https://google.com')
        self.assertIsNotNone(archivedversion)
        from pywikibot.data.memento import DEFAULT_TIMEGATE_BASE_URI
        self.assertStartsWith(archivedversion, DEFAULT_TIMEGATE_BASE_URI)

    def test_invalid(self) -> None:
        """Test getting memento for invalid URL."""
        # memento_client raises 'Exception', not a subclass.
        with self.assertRaisesRegex(
                ValueError, 'Only HTTP URIs are supported'):
            self._get_archive_url('invalid')


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
