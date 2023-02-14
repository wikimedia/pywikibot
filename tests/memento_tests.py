#!/usr/bin/env python3
"""memento client test module."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
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
            result = get_closest_memento_url(url, when, self.timegate_uri)
        return result


class TestMementoArchive(MementoTestCase):

    """New WebCite Memento tests."""

    timegate_uri = 'http://timetravel.mementoweb.org/timegate/'
    hostname = timegate_uri.replace('gate/', 'map/json/http://google.com')

    def test_newest(self):
        """Test Archive for newest https://google.com."""
        dt = '20220715'
        archivedversion = self._get_archive_url('https://google.com',
                                                date_string=dt)
        parsed = urlparse(archivedversion)
        self.assertIn(parsed.scheme, ['http', 'https'])
        self.assertEqual(parsed.netloc, 'arquivo.pt')


class TestMementoDefault(MementoTestCase):

    """Test InternetArchive is default Memento timegate."""

    timegate_uri = None
    net = True

    def test_newest(self):
        """Test getting memento for newest https://google.com."""
        archivedversion = self._get_archive_url('https://google.com')
        self.assertIsNotNone(archivedversion)

    def test_invalid(self):
        """Test getting memento for invalid URL."""
        # memento_client raises 'Exception', not a subclass.
        with self.assertRaisesRegex(
                ValueError, 'Only HTTP URIs are supported'):
            self._get_archive_url('invalid')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
