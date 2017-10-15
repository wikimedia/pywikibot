#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script that forms part of pwb_tests."""
#
# (C) Pywikibot team, 2013-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import os.path

for k, v in sorted(locals().copy().items()):
    # Skip a few items that Python 3 adds and are not emulated in pwb.
    if k in ['__cached__', '__loader__', '__spec__', '__annotations__']:
        continue
    if k == '__file__':
        print("__file__: %r" % os.path.join('.', os.path.relpath(__file__)))
    else:
        print("%r: %r" % (k, v))
