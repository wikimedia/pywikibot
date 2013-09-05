import unittest
from tests import patch_request, unpatch_request


class PywikibotTestCase(unittest.TestCase):
    def assertType(self, obj, cls):
        """Assert that obj is an instance of type cls"""
        return self.assertTrue(isinstance(obj, cls))

    def setUp(self):
        patch_request()

    def tearDown(self):
        unpatch_request()
