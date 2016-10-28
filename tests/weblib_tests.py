# -*- coding: utf-8 -*-
"""Weblib test module."""
#
# (C) Pywikibot team, 2014-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot.tools import PY2

if not PY2:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse

import pywikibot.weblib as weblib

from tests.aspects import unittest, DeprecationTestCase
from tests.utils import PatchedHttp


class TestInternetArchive(DeprecationTestCase):

    """Test weblib methods to access Internet Archive."""

    sites = {
        'archive.org': {
            'hostname': 'https://archive.org/wayback/available?url=invalid',
        },
    }

    def _test_response(self, response, *args, **kwargs):
        # for later tests this is must be present, and it'll tell us the
        # original content if that does not match
        self.assertIn('closest', response.content)

    def _get_archive_url(self, url, date_string=None):
        with PatchedHttp(weblib, False) as p:
            p.after_fetch = self._test_response
            archivedversion = weblib.getInternetArchiveURL(url, date_string)
            self.assertOneDeprecation()
            return archivedversion

    def testInternetArchiveNewest(self):
        """Test Internet Archive for newest https://google.com."""
        archivedversion = self._get_archive_url('https://google.com')
        parsed = urlparse(archivedversion)
        self.assertIn(parsed.scheme, [u'http', u'https'])
        self.assertEqual(parsed.netloc, u'web.archive.org')
        self.assertTrue(parsed.path.strip('/').endswith('google.com'), parsed.path)

    def testInternetArchiveOlder(self):
        """Test Internet Archive for https://google.com as of June 2006."""
        archivedversion = self._get_archive_url('https://google.com', '20060601')
        parsed = urlparse(archivedversion)
        self.assertIn(parsed.scheme, [u'http', u'https'])
        self.assertEqual(parsed.netloc, u'web.archive.org')
        self.assertTrue(parsed.path.strip('/').endswith('google.com'), parsed.path)
        self.assertIn('200606', parsed.path)


class TestWebCite(DeprecationTestCase):

    """Test weblib methods to access WebCite."""

    sites = {
        'webcite': {
            'hostname': 'www.webcitation.org',
        }
    }

    def _get_archive_url(self, url, date_string=None):
        archivedversion = weblib.getWebCitationURL(url, date_string)
        self.assertOneDeprecation()
        return archivedversion

    @unittest.expectedFailure  # See T110640
    def testWebCiteOlder(self):
        """Test WebCite for https://google.com as of January 2013."""
        archivedversion = self._get_archive_url('https://google.com', '20130101')
        self.assertEqual(archivedversion, 'http://www.webcitation.org/6DHSeh2L0')


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
