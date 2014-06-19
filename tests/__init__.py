# -*- coding: utf-8  -*-
#
# (C) Pywikipedia bot team, 2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import os
import pywikibot.data.api
from pywikibot.data.api import Request as _original_Request
from pywikibot.data.api import CachedRequest


class TestRequest(CachedRequest):

    """Add caching to every Request except logins."""

    def __init__(self, *args, **kwargs):
        super(TestRequest, self).__init__(0, *args, **kwargs)

    def _get_cache_dir(self):
        path = os.path.join(os.path.split(__file__)[0], 'apicache')
        self._make_dir(path)
        return path

    def _expired(self, dt):
        """Never invalidate cached data."""
        return False

    def _load_cache(self):
        """Return whether the cache can be used."""
        if not super(TestRequest, self)._load_cache():
            return False

        if 'lgpassword' in self._uniquedescriptionstr():
            self._delete_cache()
            self._data = None
            return False

        return True

    def _delete_cache(self):
        """Delete cached response if it exists."""
        self._load_cache()
        if self._cachetime:
            os.remove(self._cachefile_path())

    def _write_cache(self, data):
        """Write data except login details."""
        if 'lgpassword' in self._uniquedescriptionstr():
            return

        return super(TestRequest, self)._write_cache(data)


def patch_request():
    global original_expired
    pywikibot.data.api.Request = TestRequest
    original_expired = pywikibot.data.api.CachedRequest._expired
    pywikibot.data.api.CachedRequest._expired = lambda *args, **kwargs: False


def unpatch_request():
    pywikibot.data.api.Request = _original_Request
    pywikibot.data.api.CachedRequest._expired = original_expired
