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
    def __init__(self, *args, **kwargs):
        super(TestRequest, self).__init__(0, *args, **kwargs)

    def _get_cache_dir(self):
        path = os.path.join(os.path.split(__file__)[0], 'apicache')
        self._make_dir(path)
        return path

    def _expired(self, dt):
        return False

    def submit(self):
        cached_available = self._load_cache()
        if not cached_available:
            print str(self)
        return super(TestRequest, self).submit()


def patch_request():
    pywikibot.data.api.Request = TestRequest


def unpatch_request():
    pywikibot.data.api.Request = _original_Request
