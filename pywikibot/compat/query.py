# -*- coding: utf-8 -*-
"""
WARNING: THIS MODULE EXISTS SOLELY TO PROVIDE COMPAT BACKWARDS-COMPATIBILITY.

IT IS DEPRECATED. DO NOT USE IT.

Do not use this module anymore; use pywikibot.data.api.Request
or Page/APISite highlevel methods instead.
"""
#
# (C) Pywikibot team, 2008-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot.data import api
from pywikibot.tools import deprecated, deprecated_args, remove_last_args


@deprecated('pywikibot.data.api.Request', since='20120603',
            future_warning=True)
@deprecated_args(useAPI=None, retryCount=None, encodeTitle=None)
@remove_last_args(['back_response'])
def GetData(request, site=None):
    """
    Query the server with the given request dict.

    DEPRECATED: Use pywikibot.data.api.Request instead.
    """
    if site:
        request['site'] = site

    req = api.Request(**request)
    return req.submit()


__all__ = (GetData, )
