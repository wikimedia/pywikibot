# -*- coding: utf-8  -*-
#
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import os
import sys

__all__ = ['httplib2', 'OrderedDict', '_cache_dir', 'TestRequest',
           'patch_request', 'unpatch_request']

# Verify that the unit tests have a base working environment:
# - httplib2 is mandatory
# - ordereddict is only needed as a fallback for python 2.6
# - mwparserfromhell is optional, so is only imported in textlib_tests
try:
    import httplib2
except ImportError as e:
    print("ImportError: %s" % e)
    sys.exit(1)

try:
    from collections import OrderedDict
except ImportError:
    try:
        from ordereddict import OrderedDict
    except ImportError as e:
        print("ImportError: %s" % e)
        if sys.version_info[0] == 2 and sys.version_info[1] == 6:
            print(
                "pywikibot depends on module ordereddict in Python 2.6.\n"
                "Run 'pip install ordereddict' to run these tests under "
                "Python 2.6")
        sys.exit(1)

import pywikibot.data.api
from pywikibot.data.api import Request as _original_Request
from pywikibot.data.api import CachedRequest

_cache_dir = os.path.join(os.path.split(__file__)[0], 'apicache')

CachedRequest._get_cache_dir = staticmethod(
    lambda *args: CachedRequest._make_dir(_cache_dir))


class TestRequest(CachedRequest):

    """Add caching to every Request except logins."""

    def __init__(self, *args, **kwargs):
        super(TestRequest, self).__init__(0, *args, **kwargs)

    def _expired(self, dt):
        """Never invalidate cached data."""
        return False

    def _load_cache(self):
        """Return whether the cache can be used."""
        if not super(TestRequest, self)._load_cache():
            return False

        # tokens need careful management in the cache
        # and cant be aggressively cached.
        # FIXME: remove once 'badtoken' is reliably handled in api.py
        if 'intoken' in self._uniquedescriptionstr():
            self._data = None
            return False

        if 'lgpassword' in self._uniquedescriptionstr():
            self._data = None
            return False

        return True

    def _write_cache(self, data):
        """Write data except login details."""
        if 'intoken' in self._uniquedescriptionstr():
            return

        if 'lgpassword' in self._uniquedescriptionstr():
            return

        return super(TestRequest, self)._write_cache(data)


original_expired = None


def patch_request():
    global original_expired
    pywikibot.data.api.Request = TestRequest
    original_expired = pywikibot.data.api.CachedRequest._expired
    pywikibot.data.api.CachedRequest._expired = lambda *args, **kwargs: False


def unpatch_request():
    pywikibot.data.api.Request = _original_Request
    pywikibot.data.api.CachedRequest._expired = original_expired
