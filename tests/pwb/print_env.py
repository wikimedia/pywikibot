#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script that forms part of pwb_tests."""
from __future__ import unicode_literals

import os
import sys

_pwb_dir = os.path.abspath(os.path.join(
    os.path.split(__file__)[0], '..', '..'))
_pwb_dir = _pwb_dir[0].upper() + _pwb_dir[1:]

print('os.environ:')
for k, v in sorted(os.environ.items()):
    # Don't leak the password into logs
    if k == 'USER_PASSWORD':
        continue
    # This only appears in subprocesses
    if k in ['PYWIKIBOT2_DIR_PWB']:
        continue
    print("%r: %r" % (k, v))

print('sys.path:')
for path in sys.path:
    if path == '' or path.startswith('.'):
        continue
    # Normalise DOS drive letter
    path = path[0].upper() + path[1:]
    if path.startswith(_pwb_dir):
        continue
    print(path)
