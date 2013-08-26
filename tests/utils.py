import unittest

class PywikibotTestCase(unittest.TestCase):
    def assertType(self, obj, cls):
        """Assert that obj is an instance of type cls"""
        return self.assertTrue(isinstance(obj, cls))