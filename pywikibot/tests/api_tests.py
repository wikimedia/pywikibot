import unittest
import pywikibot
import pywikibot.data.api as api

mysite = pywikibot.Site('en', 'wikipedia')


class TestApiFunctions(unittest.TestCase):

    def testObjectCreation(self):
        """Test that api.Request() creates an object with desired attributes"""
        req = api.Request(site=mysite, foo="", bar="test")
        self.assert_(req)
        self.assertEqual(req.site, mysite)
        self.assert_("foo" in req.params)
        self.assertEqual(req["format"], "json")
        self.assertEqual(req["bar"], "test")
        # test item assignment
        req["one"] = "1"
        self.assertEqual(req.params['one'], "1")
        # test compliance with dict interface
        # req.keys() should contain "foo", "bar", "format", "maxlag", "one"
        self.assertEqual(len(req.keys()), 5)
        self.assert_("test" in req.values())
        self.assert_(all(len(item) == 2 for item in req.items()))


class TestPageGenerator(unittest.TestCase):
    def setUp(self):
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
        results = [p for p in self.gen]
        self.assertEqual(len(results), 4)
        for page in results:
            self.assertEqual(type(page), pywikibot.Page)
            self.assertEqual(page.site(), mysite)
            self.assert_(page.title() in titles)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
