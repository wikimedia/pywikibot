import datetime
import pywikibot
from pywikibot.data.api import CachedRequest
import unittest


class DryAPITests(unittest.TestCase):

    def setUp(self):
        self.parms = {'site': pywikibot.Site('en'),
                      'action': 'query',
                      'meta': 'userinfo'}
        self.req = CachedRequest(expiry=1, **self.parms)
        self.expreq = CachedRequest(expiry=0, **self.parms)
        self.diffreq = CachedRequest(expiry=1, site=pywikibot.Site('en'), action='query', meta='siteinfo')
        self.diffsite = CachedRequest(expiry=1, site=pywikibot.Site('de'), action='query', meta='userinfo')

    def test_expiry_formats(self):
        self.assertEqual(self.req.expiry, CachedRequest(datetime.timedelta(days=1), **self.parms).expiry)

    def test_get_cache_dir(self):
        retval = self.req._get_cache_dir()
        self.assertIn('apicache', retval)

    def test_create_file_name(self):
        self.assertEqual(self.req._create_file_name(), self.req._create_file_name())
        self.assertEqual(self.req._create_file_name(), self.expreq._create_file_name())
        self.assertNotEqual(self.req._create_file_name(), self.diffreq._create_file_name())

    def test_cachefile_path(self):
        self.assertEqual(self.req._cachefile_path(), self.req._cachefile_path())
        self.assertEqual(self.req._cachefile_path(), self.expreq._cachefile_path())
        self.assertNotEqual(self.req._cachefile_path(), self.diffreq._cachefile_path())
        self.assertNotEqual(self.req._cachefile_path(), self.diffsite._cachefile_path())

    def test_expired(self):
        self.assertFalse(self.req._expired(datetime.datetime.now()))
        self.assertTrue(self.req._expired(datetime.datetime.now() - datetime.timedelta(days=2)))

if __name__ == '__main__':
    unittest.main()
