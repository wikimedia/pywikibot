"""weblinkchecker test module."""
#
# (C) Pywikibot team, 2015-2021
#
# Distributed under the terms of the MIT license.
#
import datetime
import unittest
from contextlib import suppress
from urllib.parse import urlparse

from requests.exceptions import ConnectionError as RequestsConnectionError

from scripts import weblinkchecker
from tests.aspects import TestCase, require_modules


@require_modules('memento_client')
class MementoTestCase(TestCase):

    """Test memento client."""

    def _get_archive_url(self, url, date_string=None):
        from memento_client.memento_client import MementoClientException

        if date_string is None:
            when = datetime.datetime.now()
        else:
            when = datetime.datetime.strptime(date_string, '%Y%m%d')
        try:
            return weblinkchecker._get_closest_memento_url(
                url, when, self.timegate_uri)
        except (RequestsConnectionError, MementoClientException) as e:
            self.skipTest(e)


class TestMementoWebCite(MementoTestCase):

    """New WebCite Memento tests."""

    timegate_uri = 'http://timetravel.mementoweb.org/webcite/timegate/'
    hostname = ('http://timetravel.mementoweb.org/webcite/'
                'timemap/json/http://google.com')

    def test_newest(self):
        """Test WebCite for newest https://google.com."""
        archivedversion = self._get_archive_url('https://google.com')
        parsed = urlparse(archivedversion)
        self.assertIn(parsed.scheme, ['http', 'https'])
        self.assertEqual(parsed.netloc, 'www.webcitation.org')


class TestMementoDefault(MementoTestCase):

    """Test InternetArchive is default Memento timegate."""

    timegate_uri = None
    net = True

    def test_newest(self):
        """Test getting memento for newest https://google.com."""
        # Temporary increase the debug level for T196304
        import logging
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)
        archivedversion = self._get_archive_url('https://google.com')
        self.assertIsNotNone(archivedversion)

    def test_invalid(self):
        """Test getting memento for invalid URL."""
        # memento_client raises 'Exception', not a subclass.
        with self.assertRaisesRegex(
                Exception,
                'Only HTTP URIs are supported'):
            self._get_archive_url('invalid')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
