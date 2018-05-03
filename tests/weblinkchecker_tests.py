# -*- coding: utf-8 -*-
"""weblinkchecker test module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import datetime

from requests import ConnectionError as RequestsConnectionError

from pywikibot.tools import PY2
from scripts import weblinkchecker
from tests.aspects import unittest, require_modules, TestCase
from tests import weblib_tests

if not PY2:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse


@require_modules('memento_client')
class MementoTestCase(TestCase):

    """Test memento client."""

    def _get_archive_url(self, url, date_string=None):
        if date_string is None:
            when = datetime.datetime.now()
        else:
            when = datetime.datetime.strptime(date_string, '%Y%m%d')
        try:
            return weblinkchecker._get_closest_memento_url(
                url, when, self.timegate_uri)
        except RequestsConnectionError as e:
            self.skipTest(e)


class WeblibTestMementoInternetArchive(MementoTestCase, weblib_tests.TestInternetArchive):

    """Test InternetArchive Memento using old weblib tests."""

    timegate_uri = 'http://web.archive.org/web/'
    hostname = timegate_uri


class WeblibTestMementoWebCite(MementoTestCase, weblib_tests.TestWebCite):

    """Test WebCite Memento using old weblib tests."""

    timegate_uri = 'http://timetravel.mementoweb.org/webcite/timegate/'
    hostname = ('http://timetravel.mementoweb.org/webcite/'
                'timemap/json/http://google.com')


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
        archivedversion = self._get_archive_url('https://google.com')
        self.assertIsNotNone(archivedversion)

    def test_invalid(self):
        """Test getting memento for invalid URL."""
        # memento_client raises 'Exception', not a subclass.
        self.assertRaisesRegex(
            Exception, 'Only HTTP URIs are supported',
            self._get_archive_url, 'invalid')


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
