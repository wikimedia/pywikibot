# -*- coding: utf-8  -*-
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import os
import sys
if sys.version_info[0] == 2:
    from urlparse import urlparse
else:
    from urllib.parse import urlparse

import pywikibot.weblib as weblib
from tests.utils import unittest, NoSiteTestCase


class TestArchiveSites(NoSiteTestCase):

    net = True

    @classmethod
    def setUpClass(cls):
        if os.environ.get('TRAVIS', 'false') == 'true':
            raise unittest.SkipTest('Weblib tests are disabled on Travis-CI')

    def testInternetArchiveNewest(self):
        archivedversion = weblib.getInternetArchiveURL('https://google.com')
        parsed = urlparse(archivedversion)
        self.assertIn(parsed.scheme, [u'http', u'https'])
        self.assertEqual(parsed.netloc, u'web.archive.org')
        self.assertTrue(parsed.path.strip('/').endswith('www.google.com'), parsed.path)

    def testInternetArchiveOlder(self):
        archivedversion = weblib.getInternetArchiveURL('https://google.com', '200606')
        parsed = urlparse(archivedversion)
        self.assertIn(parsed.scheme, [u'http', u'https'])
        self.assertEqual(parsed.netloc, u'web.archive.org')
        self.assertTrue(parsed.path.strip('/').endswith('www.google.com'), parsed.path)
        self.assertIn('200606', parsed.path)

    def testWebCiteOlder(self):
        archivedversion = weblib.getWebCitationURL('https://google.com', '20130101')
        self.assertEqual(archivedversion, 'http://www.webcitation.org/6DHSeh2L0')

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
