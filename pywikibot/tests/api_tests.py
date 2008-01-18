import unittest
import pywikibot.data.api as api

from pywikibot.tests.dummy import TestSite as Site
mysite = Site('en.wikipedia.org')


class TestApiFunctions(unittest.TestCase):

    def testObjectCreation(self):
        """Test that api.Request() creates an object with desired attributes"""
        req = api.Request(mysite, "foo", bar="test")
        self.assert_(req)
        self.assertEqual(req.site, mysite)
        self.assert_("foo" in req.params)
        self.assertEqual(req["format"], "json")
        self.assertEqual(req["bar"], "test")
        # test item assignment
        req["one"] = "1"
        self.assertEqual(req.params['one'], "1")

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
