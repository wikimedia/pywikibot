# -*- coding: utf-8  -*-
#
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import datetime
import pywikibot
import pywikibot.data.api as api
from tests.aspects import unittest, TestCase


class TestApiFunctions(TestCase):

    family = 'wikipedia'
    code = 'en'
    cached = True

    def testObjectCreation(self):
        """Test that api.Request() creates an object with desired attributes"""
        mysite = self.get_site()
        req = api.Request(site=mysite, action="test", foo="", bar="test")
        self.assertTrue(req)
        self.assertEqual(req.site, mysite)
        self.assertIn("foo", req.params)
        self.assertEqual(req["bar"], "test")
        # test item assignment
        req["one"] = "1"
        self.assertEqual(req.params['one'], "1")
        # test compliance with dict interface
        # req.keys() should contain "action", "foo", "bar", "one"
        self.assertEqual(len(req.keys()), 4)
        self.assertIn("test", req.values())
        for item in req.items():
            self.assertEqual(len(item), 2, item)


class TestPageGenerator(TestCase):

    family = 'wikipedia'
    code = 'en'

    cached = True

    def setUp(self):
        super(TestPageGenerator, self).setUp()
        mysite = self.get_site()
        self.gen = api.PageGenerator(site=mysite,
                                     generator="links",
                                     titles="User:R'n'B")
        # following test data is copied from an actual api.php response
        self.gen.data = {
            "query": {"pages": {"296589": {"pageid": 296589,
                                           "ns": 0,
                                           "title": "Broadcaster.com"
                                           },
                                "13918157": {"pageid": 13918157,
                                             "ns": 0,
                                             "title": "Broadcaster (definition)"
                                             },
                                "156658": {"pageid": 156658,
                                           "ns": 0,
                                           "title": "Wiktionary"
                                           },
                                "47757": {"pageid": 47757,
                                          "ns": 4,
                                          "title": "Wikipedia:Disambiguation"
                                          }
                                }
                      }
        }

    def testGeneratorResults(self):
        """Test that PageGenerator yields pages with expected attributes."""
        titles = ["Broadcaster.com", "Broadcaster (definition)",
                  "Wiktionary", "Wikipedia:Disambiguation"]
        mysite = self.get_site()
        results = [p for p in self.gen]
        self.assertEqual(len(results), 4)
        for page in results:
            self.assertEqual(type(page), pywikibot.Page)
            self.assertEqual(page.site, mysite)
            self.assertIn(page.title(), titles)

    def test_initial_limit(self):
        self.assertEqual(self.gen.limit, None)  # limit is initaly None

    def test_limit_as_number(self):
        for i in range(-2, 4):
            self.gen.set_maximum_items(i)
            self.assertEqual(self.gen.limit, i)

    def test_limit_as_string(self):
        for i in range(-2, 4):
            self.gen.set_maximum_items(str(i))
            self.assertEqual(self.gen.limit, i)

    def test_wrong_limit_setting(self):
        with self.assertRaisesRegexp(
                ValueError,
                "invalid literal for int\(\) with base 10: 'test'"):
            self.gen.set_maximum_items('test')

    def test_limits(self):
        """Test that PageGenerator yields the requested amount of pages."""
        for i in range(4, 0, -1):
            self.gen.set_maximum_items(i)  # set total amount of pages
            results = [p for p in self.gen]
            self.assertEqual(len(results), i)

        self.gen.set_maximum_items(0)
        results = [p for p in self.gen]
        self.assertEqual(len(results), 4)  # total=0 but 4 expected (really?)

        self.gen.set_maximum_items(-1)
        results = [p for p in self.gen]
        self.assertEqual(len(results), 4)  # total=-1 but 4 expected


class TestCachedRequest(TestCase):

    """Test API Request caching.

    This test class does not use the forced test caching.
    """

    family = 'wikipedia'
    code = 'en'

    cached = False

    def testResults(self):
        mysite = self.get_site()
        # Run the cached query twice to ensure the
        # data returned is equal
        params = {'action': 'query',
                  'prop': 'info',
                  'titles': 'Main Page',
                  }
        req = api.CachedRequest(datetime.timedelta(minutes=10),
                                site=mysite, **params)
        data = req.submit()
        req2 = api.CachedRequest(datetime.timedelta(minutes=10),
                                 site=mysite, **params)
        data2 = req2.submit()
        self.assertEqual(data, data2)

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
