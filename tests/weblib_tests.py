# -*- coding: utf-8  -*-
#
# (C) Pywikipedia bot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

from urlparse import urlparse
import pywikibot.weblib as weblib
from utils import unittest


class TestArchiveSites(unittest.TestCase):
    def testInternetArchiveNewest(self):
        archivedversion = weblib.getInternetArchiveURL('http://google.com')
        parsed = urlparse(archivedversion)
        self.assertIn(parsed.scheme, [u'http', u'https'])
        self.assertEqual(parsed.netloc, u'web.archive.org')
        self.assertTrue(parsed.path.strip('/').endswith('www.google.com'), parsed.path)

    def testInternetArchiveOlder(self):
        archivedversion = weblib.getInternetArchiveURL('http://google.com', '200606')
        parsed = urlparse(archivedversion)
        self.assertIn(parsed.scheme, [u'http', u'https'])
        self.assertEqual(parsed.netloc, u'web.archive.org')
        self.assertTrue(parsed.path.strip('/').endswith('www.google.com'), parsed.path)
        self.assertIn('200606', parsed.path)

    def testWebCiteOlder(self):
        archivedversion = weblib.getWebCitationURL('http://google.com', '20130101')
        self.assertEqual(archivedversion, 'http://www.webcitation.org/6DHSeh2L0')

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
