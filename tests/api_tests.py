# -*- coding: utf-8  -*-
"""API test module."""
#
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import datetime
import pywikibot
import pywikibot.data.api as api
from tests.aspects import (
    unittest,
    TestCase,
    DefaultSiteTestCase,
    DefaultDrySiteTestCase,
)


class TestApiFunctions(DefaultSiteTestCase):

    """API Request object test class."""

    def testObjectCreation(self):
        """Test api.Request() constructor with implicit site creation."""
        req = api.Request(action="test", foo="", bar="test")
        self.assertTrue(req)
        self.assertEqual(req.site, self.get_site())


class TestDryApiFunctions(DefaultDrySiteTestCase):

    """API Request object test class."""

    def testObjectCreation(self):
        """Test api.Request() constructor."""
        mysite = self.get_site()
        req = api.Request(site=mysite, action="test", foo="", bar="test")
        self.assertTrue(req)
        self.assertEqual(req.site, mysite)
        self.assertIn("foo", req._params)
        self.assertEqual(req["bar"], ["test"])
        # test item assignment
        req["one"] = "1"
        self.assertEqual(req._params['one'], ["1"])
        # test compliance with dict interface
        # req.keys() should contain "action", "foo", "bar", "one"
        self.assertEqual(len(req.keys()), 4)
        self.assertIn("test", req._encoded_items().values())
        for item in req.items():
            self.assertEqual(len(item), 2, item)


class TestPageGenerator(TestCase):

    """API PageGenerator object test class."""

    family = 'wikipedia'
    code = 'en'

    dry = True

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

        # On a dry site, the namespace objects only have canonical names.
        # Add custom_name for this site namespace, to match the live site.
        if 'Wikipedia' not in self.site._namespaces:
            self.site._namespaces[4].custom_name = 'Wikipedia'

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
        self.assertEqual(self.gen.limit, None)  # limit is initally None

    def test_limit_as_number(self):
        for i in range(-2, 4):
            self.gen.set_maximum_items(i)
            self.assertEqual(self.gen.limit, i)

    def test_limit_as_string(self):
        for i in range(-2, 4):
            self.gen.set_maximum_items(str(i))
            self.assertEqual(self.gen.limit, i)

    def test_wrong_limit_setting(self):
        with self.assertRaisesRegex(
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


class TestCachedRequest(DefaultSiteTestCase):

    """Test API Request caching.

    This test class does not use the forced test caching.
    """

    cached = False

    def test_normal_use(self):
        mysite = self.get_site()
        mainpage = self.get_mainpage()
        # Run the cached query three times to ensure the
        # data returned is equal, and the last two have
        # the same cache time.
        params = {'action': 'query',
                  'prop': 'info',
                  'titles': mainpage.title(),
                  }
        req1 = api.CachedRequest(datetime.timedelta(minutes=10),
                                 site=mysite, **params)
        data1 = req1.submit()
        req2 = api.CachedRequest(datetime.timedelta(minutes=10),
                                 site=mysite, **params)
        data2 = req2.submit()
        req3 = api.CachedRequest(datetime.timedelta(minutes=10),
                                 site=mysite, **params)
        data3 = req3.submit()
        self.assertEqual(data1, data2)
        self.assertEqual(data2, data3)
        self.assertIsNotNone(req2._cachetime)
        self.assertIsNotNone(req3._cachetime)
        self.assertEqual(req2._cachetime, req3._cachetime)

    def test_internals(self):
        mysite = self.get_site()
        # Run tests on a missing page unique to this test run so it can
        # not be cached the first request, but will be cached after.
        now = datetime.datetime.now()
        params = {'action': 'query',
                  'prop': 'info',
                  'titles': 'TestCachedRequest_test_internals ' + str(now),
                  }
        req = api.CachedRequest(datetime.timedelta(minutes=10),
                                site=mysite, **params)
        rv = req._load_cache()
        self.assertFalse(rv)
        self.assertIsNone(req._data)
        self.assertIsNone(req._cachetime)

        data = req.submit()

        self.assertIsNotNone(req._data)
        self.assertIsNone(req._cachetime)

        rv = req._load_cache()

        self.assertTrue(rv)
        self.assertIsNotNone(req._data)
        self.assertIsNotNone(req._cachetime)
        self.assertGreater(req._cachetime, now)
        self.assertEqual(req._data, data)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
