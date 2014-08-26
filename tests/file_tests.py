# -*- coding: utf-8  -*-
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import pywikibot

from tests.utils import unittest, SiteTestCase

commons = pywikibot.Site('commons', 'commons')


class TestShareFiles(SiteTestCase):

    def testSharedOnly(self):
        title = 'File:Sepp Maier 1.JPG'

        itwp = pywikibot.Site('it', 'wikipedia')
        itwp_file = pywikibot.ImagePage(itwp, title)
        for using in itwp_file.usingPages():
            self.assertIsInstance(using, pywikibot.Page)

        commons_file = pywikibot.ImagePage(commons, title)

        self.assertFalse(itwp_file.exists())
        self.assertTrue(commons_file.exists())

        self.assertRaises(pywikibot.NoPage, itwp_file.fileIsShared)
        self.assertTrue(commons_file.fileIsShared())
        self.assertTrue(commons_file.fileUrl())

        self.assertRaises(pywikibot.NoPage, itwp_file.fileUrl)
        self.assertRaises(pywikibot.NoPage, itwp_file.get)

    def testLocalOnly(self):
        title = 'File:April Fools Day Adminship discussion (2005).png'

        enwp = pywikibot.Site('en', 'wikipedia')
        enwp_file = pywikibot.ImagePage(enwp, title)
        for using in enwp_file.usingPages():
            self.assertIsInstance(using, pywikibot.Page)

        commons_file = pywikibot.ImagePage(commons, title)

        self.assertTrue(enwp_file.fileUrl())
        self.assertTrue(enwp_file.exists())
        self.assertFalse(commons_file.exists())

        self.assertFalse(enwp_file.fileIsShared())
        self.assertRaises(pywikibot.NoPage, commons_file.fileIsShared)

        self.assertRaises(pywikibot.NoPage, commons_file.fileUrl)
        self.assertRaises(pywikibot.NoPage, commons_file.get)

    def testOnBoth(self):
        title = 'File:Pulsante spam.png'

        itwp = pywikibot.Site('it', 'wikipedia')
        itwp_file = pywikibot.ImagePage(itwp, title)
        for using in itwp_file.usingPages():
            self.assertIsInstance(using, pywikibot.Page)

        commons_file = pywikibot.ImagePage(commons, title)

        self.assertTrue(itwp_file.fileUrl())
        self.assertTrue(itwp_file.exists())
        self.assertTrue(commons_file.exists())

        self.assertFalse(itwp_file.fileIsShared())
        self.assertTrue(commons_file.fileIsShared())

    def testNonFileLocal(self):
        """Test file page, without local file, existing on the local wiki."""
        title = 'File:Sepp Maier 1.JPG'

        testwp = pywikibot.Site('test', 'wikipedia')
        testwp_file = pywikibot.ImagePage(testwp, title)

        self.assertTrue(testwp_file.fileUrl())
        self.assertTrue(testwp_file.exists())
        self.assertTrue(testwp_file.fileIsShared())

        commons_file = pywikibot.ImagePage(commons, title)
        self.assertEqual(testwp_file.fileUrl(),
                         commons_file.fileUrl())


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
