# -*- coding: utf-8  -*-
#
# (C) Pywikibot team, 2013-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import print_function
__version__ = '$Id$'
#
import pywikibot
from tests import aspects
from tests import unittest  # flake8: noqa

BaseTestCase = aspects.TestCase
NoSiteTestCase = aspects.TestCase
SiteTestCase = aspects.TestCase
CachedTestCase = aspects.TestCase
PywikibotTestCase = aspects.TestCase


def expectedFailureIf(expect):
    """
    Unit test decorator to expect/allow failure under conditions.

    @param expect: Flag to check if failure is allowed
    @type expect: bool
    """
    if expect:
        return unittest.expectedFailure
    else:
        return lambda orig: orig


class DummySiteinfo():

    def __init__(self, cache):
        self._cache = dict((key, (item, False)) for key, item in cache.items())

    def __getitem__(self, key):
        return self.get(key, False)

    def __setitem__(self, key, value):
        self._cache[key] = (value, False)

    def get(self, key, get_default=True, cache=True, expiry=False):
        # Default values are always expired, so only expiry=False doesn't force
        # a reload
        force = expiry is not False
        if not force and key in self._cache:
            loaded = self._cache[key]
            if not loaded[1] and not get_default:
                raise KeyError(key)
            else:
                return loaded[0]
        elif get_default:
            default = pywikibot.site.Siteinfo._get_default(key)
            if cache:
                self._cache[key] = (default, False)
            return default
        else:
            raise KeyError(key)

    def __contains__(self, key):
        return False

    def is_recognised(self, key):
        return None

    def get_requested_time(self, key):
        return False
