# -*- coding: utf-8  -*-
#
# (C) Pywikibot team, 2013-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import print_function
__version__ = '$Id$'
#
import time
import sys

if sys.version_info < (2, 7):
    # Unittest2 is a backport of python 2.7s unittest module to python 2.6
    import unittest2 as unittest
else:
    import unittest

import pywikibot

# Number of seconds each test may consume before a note is added after the test.
test_duration_warning_interval = 10


def collector():
    # This test collector loads tests from the `tests` directory in files
    # matching the pattern `*tests.py`. This gets used by `setup.py test` when
    # running on Python 2.6 to use the unittest2 test runner instead of the
    # unittest one.
    return unittest.loader.defaultTestLoader.discover("tests", "*tests.py")

from tests import patch_request, unpatch_request


class BaseTestCase(unittest.TestCase):

    """Base class for all test cases.

    Adds timing info to stdout.
    """

    def assertType(self, obj, cls):
        """Assert that obj is an instance of type cls"""
        return self.assertTrue(isinstance(obj, cls))

    def setUp(self):
        self.test_start = time.time()

    def tearDown(self):
        self.test_completed = time.time()
        duration = self.test_completed - self.test_start

        if duration > test_duration_warning_interval:
            print(' %0.3fs' % duration, end=' ')
            sys.stdout.flush()


class NoSiteTestCase(BaseTestCase):

    """Test cases not connected to a Site object.

    Do not use this for mock Site objects.

    Never set a class or instance variable called 'site'
    As it will prevent tests from executing when invoked as:
    $ nosetests -a '!site' -v
    """

    def setUp(self):
        self.old_Site_lookup_method = pywikibot.Site
        pywikibot.Site = lambda *args: self.fail('%s: Site() not permitted'
                                                 % self.__class__.__name__)

        super(NoSiteTestCase, self).setUp()

    def tearDown(self):
        super(NoSiteTestCase, self).tearDown()

        pywikibot.Site = self.old_Site_lookup_method


class SiteTestCase(BaseTestCase):

    """Test cases connected to a Site object.

    Do not use this for mock Site objects.
    """

    site = True


class CachedTestCase(SiteTestCase):

    """Aggressively cached API test cases.

    Patches pywikibot.data.api to aggressively cache
    API responses.
    """

    def setUp(self):
        patch_request()

        super(CachedTestCase, self).setUp()

    def tearDown(self):
        super(CachedTestCase, self).tearDown()

        unpatch_request()

PywikibotTestCase = CachedTestCase


class DummySiteinfo():

    def __init__(self, cache):
        self._cache = dict((key, (item, False)) for key, item in cache.items())

    def __getitem__(self, key):
        return self.get(key, False)

    def get(self, key, get_default=True, cache=True, force=False):
        if not force and key in self._cache:
            loaded = self._cache[key]
            if not loaded[1] and not get_default:
                raise KeyError(key)
            else:
                return loaded[0]
        elif get_default:
            default = pywikibot.site.Siteinfo._get_default(key)
            if cache:
                self._cache[key] = (default, True)
            return default
        else:
            raise KeyError(key)

    def __contains__(self, key):
        return False

    def is_recognised(self, key):
        return None
