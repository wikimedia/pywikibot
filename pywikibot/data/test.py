# -*- coding: utf-8  -*-
"""
Set of test suites for the data module.
"""
#
# (C) Pywikipedia bot team, 2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'


import unittest
import http, api


class HTTPTest(unittest.TestCase):

    def setUp(self):
        self.HTTP = http.HTTP(None) #TODO: Replace None with an actual Site object once implemented

    def testGETMainPage(self):
        """GETting the Main Page should give a HTTP 200 response."""
        status, data = self.HTTP.GET('/w/index.php?title=Main_Page')
        self.assertEqual(status, 200)


class APITest(unittest.TestCase):

    def setUp(self):
        self.API = api.API(None) #TODO: Replace None with an actual Site object once implemented

    def testGETMainPage(self):
        """Querying for nothing should return an empty <api /> tag."""
        status, data = self.API.query()
        self.assertEqual(status, 200)
        self.assertEqual(data, '<?xml version="1.0" encoding="utf-8"?><api />')


if __name__ == '__main__':
    unittest.main()
