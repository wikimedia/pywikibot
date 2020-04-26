# -*- coding: utf-8 -*-
"""Miscellaneous helper functions (not wiki-dependent)."""
#
# (C) Pywikibot team, 2008-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import collections
from distutils.version import LooseVersion
import gzip
import hashlib
from importlib import import_module
import inspect
import itertools
import os
import re
import stat
import subprocess
import sys
import threading
import time
import types

try:
    from collections.abc import Iterator, Mapping
except ImportError:  # Python 2.7
    from collections import Iterator, Mapping
from datetime import datetime
from distutils.version import Version
from functools import wraps
from warnings import catch_warnings, showwarning, warn

from pywikibot.logging import debug

PYTHON_VERSION = sys.version_info[:3]
PY2 = (PYTHON_VERSION[0] == 2)

if not PY2:
    from itertools import zip_longest
    import queue
    StringTypes = (str, bytes)
    UnicodeType = str
    from ipaddress import ip_address
else:
    from itertools import izip_longest as zip_longest
    import Queue as queue  # noqa: N813
    StringTypes = types.StringTypes
    UnicodeType = types.UnicodeType
    try:
        from ipaddress import ip_address
    except ImportError:
        ip_address = None

try:
    import bz2
except ImportError as bz2_import_error:
    try:
        import bz2file as bz2
        warn('package bz2 was not found; using bz2file', ImportWarning)
    except ImportError:
        warn('package bz2 and bz2file were not found', ImportWarning)
        bz2 = bz2_import_error

try:
    import lzma
except ImportError as lzma_import_error:
    lzma = lzma_import_error


if PYTHON_VERSION < (3, 5):
    # although deprecated in 3 completely no message was emitted until 3.5
    ArgSpec = inspect.ArgSpec
    getargspec = inspect.getargspec
else:
    ArgSpec = collections.namedtuple('ArgSpec', ['args', 'varargs', 'keywords',
                                                 'defaults'])

    def getargspec(func):
        """Python 3 implementation using inspect.signature."""
        sig = inspect.signature(func)
        args = []
        defaults = []
        varargs = None
        kwargs = None
        for p in sig.parameters.values():
            if p.kind == inspect.Parameter.VAR_POSITIONAL:
                varargs = p.name
            elif p.kind == inspect.Parameter.VAR_KEYWORD:
                kwargs = p.name
            else:
                args += [p.name]
                if p.default != inspect.Parameter.empty:
                    defaults += [p.default]
        if defaults:
            defaults = tuple(defaults)
        else:
            defaults = None
        return ArgSpec(args, varargs, kwargs, defaults)


_logger = 'tools'

# A mapping of characters to their MediaWiki title-cased forms. Python,
# depending on version, handles these characters differently, which causes
# errors in normalizing titles. (T200357) This dict was created using
# Python 3.7 (Unicode version 11.0.0) and should be updated at least with every
# new release of Python with an updated unicodedata.unidata_version.
_first_upper_exception = {
    '\xdf': '\xdf', '\u0149': '\u0149', '\u0180': '\u0180', '\u019a': '\u019a',
    '\u01c5': '\u01c5', '\u01c6': '\u01c5', '\u01c8': '\u01c8', '\u01c9':
    '\u01c8', '\u01cb': '\u01cb', '\u01cc': '\u01cb', '\u01f0': '\u01f0',
    '\u01f2': '\u01f2', '\u01f3': '\u01f2', '\u023c': '\u023c', '\u023f':
    '\u023f', '\u0240': '\u0240', '\u0242': '\u0242', '\u0247': '\u0247',
    '\u0249': '\u0249', '\u024b': '\u024b', '\u024d': '\u024d', '\u024f':
    '\u024f', '\u0250': '\u0250', '\u0251': '\u0251', '\u0252': '\u0252',
    '\u025c': '\u025c', '\u0261': '\u0261', '\u0265': '\u0265', '\u0266':
    '\u0266', '\u026a': '\u026a', '\u026b': '\u026b', '\u026c': '\u026c',
    '\u0271': '\u0271', '\u027d': '\u027d', '\u0287': '\u0287', '\u0289':
    '\u0289', '\u028c': '\u028c', '\u029d': '\u029d', '\u029e': '\u029e',
    '\u0345': '\u0345', '\u0371': '\u0371', '\u0373': '\u0373', '\u0377':
    '\u0377', '\u037b': '\u037b', '\u037c': '\u037c', '\u037d': '\u037d',
    '\u0390': '\u0390', '\u03b0': '\u03b0', '\u03d7': '\u03d7', '\u03f2':
    '\u03a3', '\u03f3': '\u03f3', '\u03f8': '\u03f8', '\u03fb': '\u03fb',
    '\u04cf': '\u04cf', '\u04f7': '\u04f7', '\u04fb': '\u04fb', '\u04fd':
    '\u04fd', '\u04ff': '\u04ff', '\u0511': '\u0511', '\u0513': '\u0513',
    '\u0515': '\u0515', '\u0517': '\u0517', '\u0519': '\u0519', '\u051b':
    '\u051b', '\u051d': '\u051d', '\u051f': '\u051f', '\u0521': '\u0521',
    '\u0523': '\u0523', '\u0525': '\u0525', '\u0527': '\u0527', '\u0529':
    '\u0529', '\u052b': '\u052b', '\u052d': '\u052d', '\u052f': '\u052f',
    '\u0587': '\u0587', '\u10d0': '\u10d0', '\u10d1': '\u10d1', '\u10d2':
    '\u10d2', '\u10d3': '\u10d3', '\u10d4': '\u10d4', '\u10d5': '\u10d5',
    '\u10d6': '\u10d6', '\u10d7': '\u10d7', '\u10d8': '\u10d8', '\u10d9':
    '\u10d9', '\u10da': '\u10da', '\u10db': '\u10db', '\u10dc': '\u10dc',
    '\u10dd': '\u10dd', '\u10de': '\u10de', '\u10df': '\u10df', '\u10e0':
    '\u10e0', '\u10e1': '\u10e1', '\u10e2': '\u10e2', '\u10e3': '\u10e3',
    '\u10e4': '\u10e4', '\u10e5': '\u10e5', '\u10e6': '\u10e6', '\u10e7':
    '\u10e7', '\u10e8': '\u10e8', '\u10e9': '\u10e9', '\u10ea': '\u10ea',
    '\u10eb': '\u10eb', '\u10ec': '\u10ec', '\u10ed': '\u10ed', '\u10ee':
    '\u10ee', '\u10ef': '\u10ef', '\u10f0': '\u10f0', '\u10f1': '\u10f1',
    '\u10f2': '\u10f2', '\u10f3': '\u10f3', '\u10f4': '\u10f4', '\u10f5':
    '\u10f5', '\u10f6': '\u10f6', '\u10f7': '\u10f7', '\u10f8': '\u10f8',
    '\u10f9': '\u10f9', '\u10fa': '\u10fa', '\u10fd': '\u10fd', '\u10fe':
    '\u10fe', '\u10ff': '\u10ff', '\u13f8': '\u13f8', '\u13f9': '\u13f9',
    '\u13fa': '\u13fa', '\u13fb': '\u13fb', '\u13fc': '\u13fc', '\u13fd':
    '\u13fd', '\u1c80': '\u1c80', '\u1c81': '\u1c81', '\u1c82': '\u1c82',
    '\u1c83': '\u1c83', '\u1c84': '\u1c84', '\u1c85': '\u1c85', '\u1c86':
    '\u1c86', '\u1c87': '\u1c87', '\u1c88': '\u1c88', '\u1d79': '\u1d79',
    '\u1d7d': '\u1d7d', '\u1e96': '\u1e96', '\u1e97': '\u1e97', '\u1e98':
    '\u1e98', '\u1e99': '\u1e99', '\u1e9a': '\u1e9a', '\u1efb': '\u1efb',
    '\u1efd': '\u1efd', '\u1eff': '\u1eff', '\u1f50': '\u1f50', '\u1f52':
    '\u1f52', '\u1f54': '\u1f54', '\u1f56': '\u1f56', '\u1f71': '\u0386',
    '\u1f73': '\u0388', '\u1f75': '\u0389', '\u1f77': '\u038a', '\u1f79':
    '\u038c', '\u1f7b': '\u038e', '\u1f7d': '\u038f', '\u1f80': '\u1f88',
    '\u1f81': '\u1f89', '\u1f82': '\u1f8a', '\u1f83': '\u1f8b', '\u1f84':
    '\u1f8c', '\u1f85': '\u1f8d', '\u1f86': '\u1f8e', '\u1f87': '\u1f8f',
    '\u1f88': '\u1f88', '\u1f89': '\u1f89', '\u1f8a': '\u1f8a', '\u1f8b':
    '\u1f8b', '\u1f8c': '\u1f8c', '\u1f8d': '\u1f8d', '\u1f8e': '\u1f8e',
    '\u1f8f': '\u1f8f', '\u1f90': '\u1f98', '\u1f91': '\u1f99', '\u1f92':
    '\u1f9a', '\u1f93': '\u1f9b', '\u1f94': '\u1f9c', '\u1f95': '\u1f9d',
    '\u1f96': '\u1f9e', '\u1f97': '\u1f9f', '\u1f98': '\u1f98', '\u1f99':
    '\u1f99', '\u1f9a': '\u1f9a', '\u1f9b': '\u1f9b', '\u1f9c': '\u1f9c',
    '\u1f9d': '\u1f9d', '\u1f9e': '\u1f9e', '\u1f9f': '\u1f9f', '\u1fa0':
    '\u1fa8', '\u1fa1': '\u1fa9', '\u1fa2': '\u1faa', '\u1fa3': '\u1fab',
    '\u1fa4': '\u1fac', '\u1fa5': '\u1fad', '\u1fa6': '\u1fae', '\u1fa7':
    '\u1faf', '\u1fa8': '\u1fa8', '\u1fa9': '\u1fa9', '\u1faa': '\u1faa',
    '\u1fab': '\u1fab', '\u1fac': '\u1fac', '\u1fad': '\u1fad', '\u1fae':
    '\u1fae', '\u1faf': '\u1faf', '\u1fb2': '\u1fb2', '\u1fb3': '\u1fbc',
    '\u1fb4': '\u1fb4', '\u1fb6': '\u1fb6', '\u1fb7': '\u1fb7', '\u1fbc':
    '\u1fbc', '\u1fc2': '\u1fc2', '\u1fc3': '\u1fcc', '\u1fc4': '\u1fc4',
    '\u1fc6': '\u1fc6', '\u1fc7': '\u1fc7', '\u1fcc': '\u1fcc', '\u1fd2':
    '\u1fd2', '\u1fd3': '\u0390', '\u1fd6': '\u1fd6', '\u1fd7': '\u1fd7',
    '\u1fe2': '\u1fe2', '\u1fe3': '\u03b0', '\u1fe4': '\u1fe4', '\u1fe6':
    '\u1fe6', '\u1fe7': '\u1fe7', '\u1ff2': '\u1ff2', '\u1ff3': '\u1ffc',
    '\u1ff4': '\u1ff4', '\u1ff6': '\u1ff6', '\u1ff7': '\u1ff7', '\u1ffc':
    '\u1ffc', '\u214e': '\u214e', '\u2170': '\u2170', '\u2171': '\u2171',
    '\u2172': '\u2172', '\u2173': '\u2173', '\u2174': '\u2174', '\u2175':
    '\u2175', '\u2176': '\u2176', '\u2177': '\u2177', '\u2178': '\u2178',
    '\u2179': '\u2179', '\u217a': '\u217a', '\u217b': '\u217b', '\u217c':
    '\u217c', '\u217d': '\u217d', '\u217e': '\u217e', '\u217f': '\u217f',
    '\u2184': '\u2184', '\u24d0': '\u24d0', '\u24d1': '\u24d1', '\u24d2':
    '\u24d2', '\u24d3': '\u24d3', '\u24d4': '\u24d4', '\u24d5': '\u24d5',
    '\u24d6': '\u24d6', '\u24d7': '\u24d7', '\u24d8': '\u24d8', '\u24d9':
    '\u24d9', '\u24da': '\u24da', '\u24db': '\u24db', '\u24dc': '\u24dc',
    '\u24dd': '\u24dd', '\u24de': '\u24de', '\u24df': '\u24df', '\u24e0':
    '\u24e0', '\u24e1': '\u24e1', '\u24e2': '\u24e2', '\u24e3': '\u24e3',
    '\u24e4': '\u24e4', '\u24e5': '\u24e5', '\u24e6': '\u24e6', '\u24e7':
    '\u24e7', '\u24e8': '\u24e8', '\u24e9': '\u24e9', '\u2c30': '\u2c30',
    '\u2c31': '\u2c31', '\u2c32': '\u2c32', '\u2c33': '\u2c33', '\u2c34':
    '\u2c34', '\u2c35': '\u2c35', '\u2c36': '\u2c36', '\u2c37': '\u2c37',
    '\u2c38': '\u2c38', '\u2c39': '\u2c39', '\u2c3a': '\u2c3a', '\u2c3b':
    '\u2c3b', '\u2c3c': '\u2c3c', '\u2c3d': '\u2c3d', '\u2c3e': '\u2c3e',
    '\u2c3f': '\u2c3f', '\u2c40': '\u2c40', '\u2c41': '\u2c41', '\u2c42':
    '\u2c42', '\u2c43': '\u2c43', '\u2c44': '\u2c44', '\u2c45': '\u2c45',
    '\u2c46': '\u2c46', '\u2c47': '\u2c47', '\u2c48': '\u2c48', '\u2c49':
    '\u2c49', '\u2c4a': '\u2c4a', '\u2c4b': '\u2c4b', '\u2c4c': '\u2c4c',
    '\u2c4d': '\u2c4d', '\u2c4e': '\u2c4e', '\u2c4f': '\u2c4f', '\u2c50':
    '\u2c50', '\u2c51': '\u2c51', '\u2c52': '\u2c52', '\u2c53': '\u2c53',
    '\u2c54': '\u2c54', '\u2c55': '\u2c55', '\u2c56': '\u2c56', '\u2c57':
    '\u2c57', '\u2c58': '\u2c58', '\u2c59': '\u2c59', '\u2c5a': '\u2c5a',
    '\u2c5b': '\u2c5b', '\u2c5c': '\u2c5c', '\u2c5d': '\u2c5d', '\u2c5e':
    '\u2c5e', '\u2c61': '\u2c61', '\u2c65': '\u2c65', '\u2c66': '\u2c66',
    '\u2c68': '\u2c68', '\u2c6a': '\u2c6a', '\u2c6c': '\u2c6c', '\u2c73':
    '\u2c73', '\u2c76': '\u2c76', '\u2c81': '\u2c81', '\u2c83': '\u2c83',
    '\u2c85': '\u2c85', '\u2c87': '\u2c87', '\u2c89': '\u2c89', '\u2c8b':
    '\u2c8b', '\u2c8d': '\u2c8d', '\u2c8f': '\u2c8f', '\u2c91': '\u2c91',
    '\u2c93': '\u2c93', '\u2c95': '\u2c95', '\u2c97': '\u2c97', '\u2c99':
    '\u2c99', '\u2c9b': '\u2c9b', '\u2c9d': '\u2c9d', '\u2c9f': '\u2c9f',
    '\u2ca1': '\u2ca1', '\u2ca3': '\u2ca3', '\u2ca5': '\u2ca5', '\u2ca7':
    '\u2ca7', '\u2ca9': '\u2ca9', '\u2cab': '\u2cab', '\u2cad': '\u2cad',
    '\u2caf': '\u2caf', '\u2cb1': '\u2cb1', '\u2cb3': '\u2cb3', '\u2cb5':
    '\u2cb5', '\u2cb7': '\u2cb7', '\u2cb9': '\u2cb9', '\u2cbb': '\u2cbb',
    '\u2cbd': '\u2cbd', '\u2cbf': '\u2cbf', '\u2cc1': '\u2cc1', '\u2cc3':
    '\u2cc3', '\u2cc5': '\u2cc5', '\u2cc7': '\u2cc7', '\u2cc9': '\u2cc9',
    '\u2ccb': '\u2ccb', '\u2ccd': '\u2ccd', '\u2ccf': '\u2ccf', '\u2cd1':
    '\u2cd1', '\u2cd3': '\u2cd3', '\u2cd5': '\u2cd5', '\u2cd7': '\u2cd7',
    '\u2cd9': '\u2cd9', '\u2cdb': '\u2cdb', '\u2cdd': '\u2cdd', '\u2cdf':
    '\u2cdf', '\u2ce1': '\u2ce1', '\u2ce3': '\u2ce3', '\u2cec': '\u2cec',
    '\u2cee': '\u2cee', '\u2cf3': '\u2cf3', '\u2d00': '\u2d00', '\u2d01':
    '\u2d01', '\u2d02': '\u2d02', '\u2d03': '\u2d03', '\u2d04': '\u2d04',
    '\u2d05': '\u2d05', '\u2d06': '\u2d06', '\u2d07': '\u2d07', '\u2d08':
    '\u2d08', '\u2d09': '\u2d09', '\u2d0a': '\u2d0a', '\u2d0b': '\u2d0b',
    '\u2d0c': '\u2d0c', '\u2d0d': '\u2d0d', '\u2d0e': '\u2d0e', '\u2d0f':
    '\u2d0f', '\u2d10': '\u2d10', '\u2d11': '\u2d11', '\u2d12': '\u2d12',
    '\u2d13': '\u2d13', '\u2d14': '\u2d14', '\u2d15': '\u2d15', '\u2d16':
    '\u2d16', '\u2d17': '\u2d17', '\u2d18': '\u2d18', '\u2d19': '\u2d19',
    '\u2d1a': '\u2d1a', '\u2d1b': '\u2d1b', '\u2d1c': '\u2d1c', '\u2d1d':
    '\u2d1d', '\u2d1e': '\u2d1e', '\u2d1f': '\u2d1f', '\u2d20': '\u2d20',
    '\u2d21': '\u2d21', '\u2d22': '\u2d22', '\u2d23': '\u2d23', '\u2d24':
    '\u2d24', '\u2d25': '\u2d25', '\u2d27': '\u2d27', '\u2d2d': '\u2d2d',
    '\ua641': '\ua641', '\ua643': '\ua643', '\ua645': '\ua645', '\ua647':
    '\ua647', '\ua649': '\ua649', '\ua64b': '\ua64b', '\ua64d': '\ua64d',
    '\ua64f': '\ua64f', '\ua651': '\ua651', '\ua653': '\ua653', '\ua655':
    '\ua655', '\ua657': '\ua657', '\ua659': '\ua659', '\ua65b': '\ua65b',
    '\ua65d': '\ua65d', '\ua65f': '\ua65f', '\ua661': '\ua661', '\ua663':
    '\ua663', '\ua665': '\ua665', '\ua667': '\ua667', '\ua669': '\ua669',
    '\ua66b': '\ua66b', '\ua66d': '\ua66d', '\ua681': '\ua681', '\ua683':
    '\ua683', '\ua685': '\ua685', '\ua687': '\ua687', '\ua689': '\ua689',
    '\ua68b': '\ua68b', '\ua68d': '\ua68d', '\ua68f': '\ua68f', '\ua691':
    '\ua691', '\ua693': '\ua693', '\ua695': '\ua695', '\ua697': '\ua697',
    '\ua699': '\ua699', '\ua69b': '\ua69b', '\ua723': '\ua723', '\ua725':
    '\ua725', '\ua727': '\ua727', '\ua729': '\ua729', '\ua72b': '\ua72b',
    '\ua72d': '\ua72d', '\ua72f': '\ua72f', '\ua733': '\ua733', '\ua735':
    '\ua735', '\ua737': '\ua737', '\ua739': '\ua739', '\ua73b': '\ua73b',
    '\ua73d': '\ua73d', '\ua73f': '\ua73f', '\ua741': '\ua741', '\ua743':
    '\ua743', '\ua745': '\ua745', '\ua747': '\ua747', '\ua749': '\ua749',
    '\ua74b': '\ua74b', '\ua74d': '\ua74d', '\ua74f': '\ua74f', '\ua751':
    '\ua751', '\ua753': '\ua753', '\ua755': '\ua755', '\ua757': '\ua757',
    '\ua759': '\ua759', '\ua75b': '\ua75b', '\ua75d': '\ua75d', '\ua75f':
    '\ua75f', '\ua761': '\ua761', '\ua763': '\ua763', '\ua765': '\ua765',
    '\ua767': '\ua767', '\ua769': '\ua769', '\ua76b': '\ua76b', '\ua76d':
    '\ua76d', '\ua76f': '\ua76f', '\ua77a': '\ua77a', '\ua77c': '\ua77c',
    '\ua77f': '\ua77f', '\ua781': '\ua781', '\ua783': '\ua783', '\ua785':
    '\ua785', '\ua787': '\ua787', '\ua78c': '\ua78c', '\ua791': '\ua791',
    '\ua793': '\ua793', '\ua797': '\ua797', '\ua799': '\ua799', '\ua79b':
    '\ua79b', '\ua79d': '\ua79d', '\ua79f': '\ua79f', '\ua7a1': '\ua7a1',
    '\ua7a3': '\ua7a3', '\ua7a5': '\ua7a5', '\ua7a7': '\ua7a7', '\ua7a9':
    '\ua7a9', '\ua7b5': '\ua7b5', '\ua7b7': '\ua7b7', '\ua7b9': '\ua7b9',
    '\uab53': '\uab53', '\uab70': '\uab70', '\uab71': '\uab71', '\uab72':
    '\uab72', '\uab73': '\uab73', '\uab74': '\uab74', '\uab75': '\uab75',
    '\uab76': '\uab76', '\uab77': '\uab77', '\uab78': '\uab78', '\uab79':
    '\uab79', '\uab7a': '\uab7a', '\uab7b': '\uab7b', '\uab7c': '\uab7c',
    '\uab7d': '\uab7d', '\uab7e': '\uab7e', '\uab7f': '\uab7f', '\uab80':
    '\uab80', '\uab81': '\uab81', '\uab82': '\uab82', '\uab83': '\uab83',
    '\uab84': '\uab84', '\uab85': '\uab85', '\uab86': '\uab86', '\uab87':
    '\uab87', '\uab88': '\uab88', '\uab89': '\uab89', '\uab8a': '\uab8a',
    '\uab8b': '\uab8b', '\uab8c': '\uab8c', '\uab8d': '\uab8d', '\uab8e':
    '\uab8e', '\uab8f': '\uab8f', '\uab90': '\uab90', '\uab91': '\uab91',
    '\uab92': '\uab92', '\uab93': '\uab93', '\uab94': '\uab94', '\uab95':
    '\uab95', '\uab96': '\uab96', '\uab97': '\uab97', '\uab98': '\uab98',
    '\uab99': '\uab99', '\uab9a': '\uab9a', '\uab9b': '\uab9b', '\uab9c':
    '\uab9c', '\uab9d': '\uab9d', '\uab9e': '\uab9e', '\uab9f': '\uab9f',
    '\uaba0': '\uaba0', '\uaba1': '\uaba1', '\uaba2': '\uaba2', '\uaba3':
    '\uaba3', '\uaba4': '\uaba4', '\uaba5': '\uaba5', '\uaba6': '\uaba6',
    '\uaba7': '\uaba7', '\uaba8': '\uaba8', '\uaba9': '\uaba9', '\uabaa':
    '\uabaa', '\uabab': '\uabab', '\uabac': '\uabac', '\uabad': '\uabad',
    '\uabae': '\uabae', '\uabaf': '\uabaf', '\uabb0': '\uabb0', '\uabb1':
    '\uabb1', '\uabb2': '\uabb2', '\uabb3': '\uabb3', '\uabb4': '\uabb4',
    '\uabb5': '\uabb5', '\uabb6': '\uabb6', '\uabb7': '\uabb7', '\uabb8':
    '\uabb8', '\uabb9': '\uabb9', '\uabba': '\uabba', '\uabbb': '\uabbb',
    '\uabbc': '\uabbc', '\uabbd': '\uabbd', '\uabbe': '\uabbe', '\uabbf':
    '\uabbf', '\ufb00': '\ufb00', '\ufb01': '\ufb01', '\ufb02': '\ufb02',
    '\ufb03': '\ufb03', '\ufb04': '\ufb04', '\ufb05': '\ufb05', '\ufb06':
    '\ufb06', '\ufb13': '\ufb13', '\ufb14': '\ufb14', '\ufb15': '\ufb15',
    '\ufb16': '\ufb16', '\ufb17': '\ufb17', '\U0001044e': '\U0001044e',
    '\U0001044f': '\U0001044f', '\U000104d8': '\U000104d8', '\U000104d9':
    '\U000104d9', '\U000104da': '\U000104da', '\U000104db': '\U000104db',
    '\U000104dc': '\U000104dc', '\U000104dd': '\U000104dd', '\U000104de':
    '\U000104de', '\U000104df': '\U000104df', '\U000104e0': '\U000104e0',
    '\U000104e1': '\U000104e1', '\U000104e2': '\U000104e2', '\U000104e3':
    '\U000104e3', '\U000104e4': '\U000104e4', '\U000104e5': '\U000104e5',
    '\U000104e6': '\U000104e6', '\U000104e7': '\U000104e7', '\U000104e8':
    '\U000104e8', '\U000104e9': '\U000104e9', '\U000104ea': '\U000104ea',
    '\U000104eb': '\U000104eb', '\U000104ec': '\U000104ec', '\U000104ed':
    '\U000104ed', '\U000104ee': '\U000104ee', '\U000104ef': '\U000104ef',
    '\U000104f0': '\U000104f0', '\U000104f1': '\U000104f1', '\U000104f2':
    '\U000104f2', '\U000104f3': '\U000104f3', '\U000104f4': '\U000104f4',
    '\U000104f5': '\U000104f5', '\U000104f6': '\U000104f6', '\U000104f7':
    '\U000104f7', '\U000104f8': '\U000104f8', '\U000104f9': '\U000104f9',
    '\U000104fa': '\U000104fa', '\U000104fb': '\U000104fb', '\U00010cc0':
    '\U00010cc0', '\U00010cc1': '\U00010cc1', '\U00010cc2': '\U00010cc2',
    '\U00010cc3': '\U00010cc3', '\U00010cc4': '\U00010cc4', '\U00010cc5':
    '\U00010cc5', '\U00010cc6': '\U00010cc6', '\U00010cc7': '\U00010cc7',
    '\U00010cc8': '\U00010cc8', '\U00010cc9': '\U00010cc9', '\U00010cca':
    '\U00010cca', '\U00010ccb': '\U00010ccb', '\U00010ccc': '\U00010ccc',
    '\U00010ccd': '\U00010ccd', '\U00010cce': '\U00010cce', '\U00010ccf':
    '\U00010ccf', '\U00010cd0': '\U00010cd0', '\U00010cd1': '\U00010cd1',
    '\U00010cd2': '\U00010cd2', '\U00010cd3': '\U00010cd3', '\U00010cd4':
    '\U00010cd4', '\U00010cd5': '\U00010cd5', '\U00010cd6': '\U00010cd6',
    '\U00010cd7': '\U00010cd7', '\U00010cd8': '\U00010cd8', '\U00010cd9':
    '\U00010cd9', '\U00010cda': '\U00010cda', '\U00010cdb': '\U00010cdb',
    '\U00010cdc': '\U00010cdc', '\U00010cdd': '\U00010cdd', '\U00010cde':
    '\U00010cde', '\U00010cdf': '\U00010cdf', '\U00010ce0': '\U00010ce0',
    '\U00010ce1': '\U00010ce1', '\U00010ce2': '\U00010ce2', '\U00010ce3':
    '\U00010ce3', '\U00010ce4': '\U00010ce4', '\U00010ce5': '\U00010ce5',
    '\U00010ce6': '\U00010ce6', '\U00010ce7': '\U00010ce7', '\U00010ce8':
    '\U00010ce8', '\U00010ce9': '\U00010ce9', '\U00010cea': '\U00010cea',
    '\U00010ceb': '\U00010ceb', '\U00010cec': '\U00010cec', '\U00010ced':
    '\U00010ced', '\U00010cee': '\U00010cee', '\U00010cef': '\U00010cef',
    '\U00010cf0': '\U00010cf0', '\U00010cf1': '\U00010cf1', '\U00010cf2':
    '\U00010cf2', '\U000118c0': '\U000118c0', '\U000118c1': '\U000118c1',
    '\U000118c2': '\U000118c2', '\U000118c3': '\U000118c3', '\U000118c4':
    '\U000118c4', '\U000118c5': '\U000118c5', '\U000118c6': '\U000118c6',
    '\U000118c7': '\U000118c7', '\U000118c8': '\U000118c8', '\U000118c9':
    '\U000118c9', '\U000118ca': '\U000118ca', '\U000118cb': '\U000118cb',
    '\U000118cc': '\U000118cc', '\U000118cd': '\U000118cd', '\U000118ce':
    '\U000118ce', '\U000118cf': '\U000118cf', '\U000118d0': '\U000118d0',
    '\U000118d1': '\U000118d1', '\U000118d2': '\U000118d2', '\U000118d3':
    '\U000118d3', '\U000118d4': '\U000118d4', '\U000118d5': '\U000118d5',
    '\U000118d6': '\U000118d6', '\U000118d7': '\U000118d7', '\U000118d8':
    '\U000118d8', '\U000118d9': '\U000118d9', '\U000118da': '\U000118da',
    '\U000118db': '\U000118db', '\U000118dc': '\U000118dc', '\U000118dd':
    '\U000118dd', '\U000118de': '\U000118de', '\U000118df': '\U000118df',
    '\U00016e60': '\U00016e60', '\U00016e61': '\U00016e61', '\U00016e62':
    '\U00016e62', '\U00016e63': '\U00016e63', '\U00016e64': '\U00016e64',
    '\U00016e65': '\U00016e65', '\U00016e66': '\U00016e66', '\U00016e67':
    '\U00016e67', '\U00016e68': '\U00016e68', '\U00016e69': '\U00016e69',
    '\U00016e6a': '\U00016e6a', '\U00016e6b': '\U00016e6b', '\U00016e6c':
    '\U00016e6c', '\U00016e6d': '\U00016e6d', '\U00016e6e': '\U00016e6e',
    '\U00016e6f': '\U00016e6f', '\U00016e70': '\U00016e70', '\U00016e71':
    '\U00016e71', '\U00016e72': '\U00016e72', '\U00016e73': '\U00016e73',
    '\U00016e74': '\U00016e74', '\U00016e75': '\U00016e75', '\U00016e76':
    '\U00016e76', '\U00016e77': '\U00016e77', '\U00016e78': '\U00016e78',
    '\U00016e79': '\U00016e79', '\U00016e7a': '\U00016e7a', '\U00016e7b':
    '\U00016e7b', '\U00016e7c': '\U00016e7c', '\U00016e7d': '\U00016e7d',
    '\U00016e7e': '\U00016e7e', '\U00016e7f': '\U00016e7f', '\U0001e922':
    '\U0001e922', '\U0001e923': '\U0001e923', '\U0001e924': '\U0001e924',
    '\U0001e925': '\U0001e925', '\U0001e926': '\U0001e926', '\U0001e927':
    '\U0001e927', '\U0001e928': '\U0001e928', '\U0001e929': '\U0001e929',
    '\U0001e92a': '\U0001e92a', '\U0001e92b': '\U0001e92b', '\U0001e92c':
    '\U0001e92c', '\U0001e92d': '\U0001e92d', '\U0001e92e': '\U0001e92e',
    '\U0001e92f': '\U0001e92f', '\U0001e930': '\U0001e930', '\U0001e931':
    '\U0001e931', '\U0001e932': '\U0001e932', '\U0001e933': '\U0001e933',
    '\U0001e934': '\U0001e934', '\U0001e935': '\U0001e935', '\U0001e936':
    '\U0001e936', '\U0001e937': '\U0001e937', '\U0001e938': '\U0001e938',
    '\U0001e939': '\U0001e939', '\U0001e93a': '\U0001e93a', '\U0001e93b':
    '\U0001e93b', '\U0001e93c': '\U0001e93c', '\U0001e93d': '\U0001e93d',
    '\U0001e93e': '\U0001e93e', '\U0001e93f': '\U0001e93f', '\U0001e940':
    '\U0001e940', '\U0001e941': '\U0001e941', '\U0001e942': '\U0001e942',
}.get


class _NotImplementedWarning(RuntimeWarning):

    """Feature that is no longer implemented."""

    pass


class NotImplementedClass(object):

    """No implementation is available."""

    def __init__(self, *args, **kwargs):
        """Initializer."""
        raise NotImplementedError(
            '%s: %s' % (self.__class__.__name__, self.__doc__))


def is_IP(IP):  # noqa N802, N803
    """Verify the IP address provided is valid.

    No logging is performed. Use ip_address instead to catch errors.

    @param IP: IP address
    @type IP: str
    @rtype: bool
    """
    method = ip_address
    if not ip_address:  # Python 2 needs ipaddress to be installed
        issue_deprecation_warning(
            'ipaddr module', 'ipaddress module',
            warning_class=FutureWarning, since='20200120')
        from pywikibot.tools import ip
        with suppress_warnings('pywikibot.tools.ip.is_IP is deprecated'):
            method = ip.is_IP

    try:
        method(IP)
    except ValueError:
        pass
    else:
        return True
    return False


def has_module(module, version=None):
    """Check whether a module can be imported."""
    try:
        m = import_module(module)
    except ImportError:
        pass
    else:
        if version is None:
            return True
        try:
            module_version = LooseVersion(m.__version__)
        except AttributeError:
            pass
        else:
            if module_version >= LooseVersion(version):
                return True
            else:
                warn('Module version {} is lower than requested version {}'
                     .format(module_version, version), ImportWarning)
    return False


def empty_iterator():
    # http://stackoverflow.com/a/13243870/473890
    """An iterator which does nothing."""
    return
    yield


def py2_encode_utf_8(func):
    """Decorator to optionally encode the string result of func on Python 2."""
    if PY2:
        return lambda s: func(s).encode('utf-8')
    else:
        return func


class classproperty(object):  # noqa: N801

    """
    Descriptor class to access a class method as a property.

    This class may be used as a decorator::

        class Foo(object):

            _bar = 'baz'  # a class property

            @classproperty
            def bar(cls):  # a class property method
                return cls._bar

    Foo.bar gives 'baz'.
    """

    def __init__(self, cls_method):
        """Hold the class method."""
        self.method = cls_method
        self.__doc__ = self.method.__doc__

    def __get__(self, instance, owner):
        """Get the attribute of the owner class by its method."""
        return self.method(owner)


class suppress_warnings(catch_warnings):  # noqa: N801

    """A decorator/context manager that temporarily suppresses warnings.

    Those suppressed warnings that do not match the parameters will be raised
    shown upon exit.
    """

    def __init__(self, message='', category=Warning, filename=''):
        """Initialize the object.

        The parameter semantics are similar to those of
        `warnings.filterwarnings`.

        @param message: A string containing a regular expression that the start
            of the warning message must match. (case-insensitive)
        @type message: str
        @param category: A class (a subclass of Warning) of which the warning
            category must be a subclass in order to match.
        @type category: type
        @param filename: A string containing a regular expression that the
            start of the path to the warning module must match.
            (case-sensitive)
        @type filename: str
        """
        self.message_match = re.compile(message, re.I).match
        self.category = category
        self.filename_match = re.compile(filename).match
        super(suppress_warnings, self).__init__(record=True)

    def __enter__(self):
        """Catch all warnings and store them in `self.log`."""
        self.log = super(suppress_warnings, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop logging warnings and show those that do not match to params."""
        super(suppress_warnings, self).__exit__()
        for warning in self.log:
            if (
                not issubclass(warning.category, self.category)
                or not self.message_match(str(warning.message))
                or not self.filename_match(warning.filename)
            ):
                showwarning(
                    warning.message, warning.category, warning.filename,
                    warning.lineno, warning.file, warning.line)

    def __call__(self, func):
        """Decorate func to suppress warnings."""
        @wraps(func)
        def suppressed_func(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return suppressed_func


class UnicodeMixin(object):

    """Mixin class to add __str__ method in Python 2 or 3."""

    @py2_encode_utf_8
    def __str__(self):
        """Return the unicode representation as the str representation."""
        return self.__unicode__()


# From http://python3porting.com/preparing.html
class ComparableMixin(object):

    """Mixin class to allow comparing to other objects which are comparable."""

    def __lt__(self, other):
        """Compare if self is less than other."""
        return other > self._cmpkey()

    def __le__(self, other):
        """Compare if self is less equals other."""
        return other >= self._cmpkey()

    def __eq__(self, other):
        """Compare if self is equal to other."""
        return other == self._cmpkey()

    def __ge__(self, other):
        """Compare if self is greater equals other."""
        return other <= self._cmpkey()

    def __gt__(self, other):
        """Compare if self is greater than other."""
        return other < self._cmpkey()

    def __ne__(self, other):
        """Compare if self is not equal to other."""
        return other != self._cmpkey()


class DotReadableDict(UnicodeMixin):

    """Parent class of Revision() and FileInfo().

    Provide:
    - __getitem__(), __unicode__() and __repr__().

    """

    def __getitem__(self, key):
        """Give access to class values by key.

        Revision class may also give access to its values by keys
        e.g. revid parameter may be assigned by revision['revid']
        as well as revision.revid. This makes formatting strings with
        % operator easier.

        """
        return getattr(self, key)

    def __unicode__(self):
        """Return string representation."""
        # TODO: This is more efficient if the PY2 test is done during
        # class instantiation, and not inside the method.
        if not PY2:
            return repr(self.__dict__)
        else:
            _content = ', '.join(
                '{0}: {1}'.format(k, v) for k, v in self.__dict__.items())
            return '{{{0}}}'.format(_content)

    def __repr__(self):
        """Return a more complete string representation."""
        return repr(self.__dict__)


class FrozenDict(dict):

    """
    Frozen dict, preventing write after initialisation.

    Raises TypeError if write attempted.
    """

    def __init__(self, data=None, error=None):
        """
        Initializer.

        @param data: mapping to freeze
        @type data: mapping
        @param error: error message
        @type error: basestring
        """
        if data:
            args = [data]
        else:
            args = []
        super(FrozenDict, self).__init__(*args)
        self._error = error or 'FrozenDict: not writable'

    def update(self, *args, **kwargs):
        """Prevent updates."""
        raise TypeError(self._error)

    __setitem__ = update


class LazyRegex(object):

    """
    Regex object that obtains and compiles the regex on usage.

    Instances behave like the object created using L{re.compile}.
    """

    def __init__(self, pattern, flags=0):
        """
        Initializer.

        @param pattern: L{re} regex pattern
        @type pattern: str or callable
        @param flags: L{re.compile} flags
        @type flags: int
        """
        self.raw = pattern
        self.flags = flags
        super(LazyRegex, self).__init__()

    @property
    def raw(self):
        """The raw property."""
        if callable(self._raw):
            self._raw = self._raw()

        return self._raw

    @raw.setter
    def raw(self, value):
        self._raw = value
        self._compiled = None

    @property
    def flags(self):
        """The flags property."""
        return self._flags

    @flags.setter
    def flags(self, value):
        self._flags = value
        self._compiled = None

    def __getattr__(self, attr):
        """Compile the regex and delegate all attribute to the regex."""
        if self._raw:
            if not self._compiled:
                self._compiled = re.compile(self.raw, self.flags)

            if hasattr(self._compiled, attr):
                return getattr(self._compiled, attr)

            raise AttributeError('%s: attr %s not recognised'
                                 % (self.__class__.__name__, attr))
        else:
            raise AttributeError('%s.raw not set' % self.__class__.__name__)


class DeprecatedRegex(LazyRegex):

    """Regex object that issues a deprecation notice."""

    def __init__(self, pattern, flags=0, name=None, instead=None, since=None):
        """
        Initializer.

        If name is None, the regex pattern will be used as part of
        the deprecation warning.

        @param name: name of the object that is deprecated
        @type name: str or None
        @param instead: if provided, will be used to specify the replacement
            of the deprecated name
        @type instead: str
        """
        super(DeprecatedRegex, self).__init__(pattern, flags)
        self._name = name or self.raw
        self._instead = instead
        self._since = since

    def __getattr__(self, attr):
        """Issue deprecation warning."""
        issue_deprecation_warning(
            self._name, self._instead, warning_class=FutureWarning,
            since=self._since)
        return super(DeprecatedRegex, self).__getattr__(attr)


def first_lower(string):
    """
    Return a string with the first character uncapitalized.

    Empty strings are supported. The original string is not changed.
    """
    return string[:1].lower() + string[1:]


def first_upper(string):
    """
    Return a string with the first character capitalized.

    Empty strings are supported. The original string is not changed.

    @note: MediaWiki doesn't capitalize some characters the same way as Python.
        This function tries to be close to MediaWiki's capitalize function in
        title.php. See T179115 and T200357.
    """
    first = string[:1]
    return (_first_upper_exception(first) or first.upper()) + string[1:]


def normalize_username(username):
    """Normalize the username."""
    if not username:
        return None
    username = re.sub('[_ ]+', ' ', username).strip()
    return first_upper(username)


class MediaWikiVersion(Version):

    """
    Version object to allow comparing 'wmf' versions with normal ones.

    The version mainly consist of digits separated by periods. After that is a
    suffix which may only be 'wmf<number>', 'alpha', 'beta<number>' or
    '-rc.<number>' (the - and . are optional). They are considered from old to
    new in that order with a version number without suffix is considered the
    newest. This secondary difference is stored in an internal _dev_version
    attribute.

    Two versions are equal if their normal version and dev version are equal. A
    version is greater if the normal version or dev version is greater. For
    example:

        1.24 < 1.24.1 < 1.25wmf1 < 1.25alpha < 1.25beta1 < 1.25beta2
        < 1.25-rc-1 < 1.25-rc.2 < 1.25

    Any other suffixes are considered invalid.
    """

    MEDIAWIKI_VERSION = re.compile(
        r'(\d+(?:\.\d+)+)(-?wmf\.?(\d+)|alpha|beta(\d+)|-?rc\.?(\d+)|.*)?$')

    @classmethod
    def from_generator(cls, generator):
        """Create instance using the generator string."""
        if not generator.startswith('MediaWiki '):
            raise ValueError('Generator string ({0!r}) must start with '
                             '"MediaWiki "'.format(generator))
        return cls(generator[len('MediaWiki '):])

    def parse(self, vstring):
        """Parse version string."""
        version_match = MediaWikiVersion.MEDIAWIKI_VERSION.match(vstring)
        if not version_match:
            raise ValueError('Invalid version number "{0}"'.format(vstring))
        components = [int(n) for n in version_match.group(1).split('.')]
        # The _dev_version numbering scheme might change. E.g. if a stage
        # between 'alpha' and 'beta' is added, 'beta', 'rc' and stable releases
        # are reassigned (beta=3, rc=4, stable=5).
        if version_match.group(3):  # wmf version
            self._dev_version = (0, int(version_match.group(3)))
        elif version_match.group(4):
            self._dev_version = (2, int(version_match.group(4)))
        elif version_match.group(5):
            self._dev_version = (3, int(version_match.group(5)))
        elif version_match.group(2) in ('alpha', '-alpha'):
            self._dev_version = (1, )
        else:
            for handled in ('wmf', 'alpha', 'beta', 'rc'):
                # if any of those pops up here our parser has failed
                assert handled not in version_match.group(2), \
                    'Found "{0}" in "{1}"'.format(handled,
                                                  version_match.group(2))
            if version_match.group(2):
                debug('Additional unused version part '
                      '"{0}"'.format(version_match.group(2)),
                      _logger)
            self._dev_version = (4, )
        self.suffix = version_match.group(2) or ''
        self.version = tuple(components)

    def __str__(self):
        """Return version number with optional suffix."""
        return '.'.join(str(v) for v in self.version) + self.suffix

    def _cmp(self, other):
        if isinstance(other, StringTypes):
            other = MediaWikiVersion(other)

        if self.version > other.version:
            return 1
        if self.version < other.version:
            return -1
        if self._dev_version > other._dev_version:
            return 1
        if self._dev_version < other._dev_version:
            return -1
        return 0

    if PY2:
        __cmp__ = _cmp


class ThreadedGenerator(threading.Thread):

    """Look-ahead generator class.

    Runs a generator in a separate thread and queues the results; can
    be called like a regular generator.

    Subclasses should override self.generator, I{not} self.run

    Important: the generator thread will stop itself if the generator's
    internal queue is exhausted; but, if the calling program does not use
    all the generated values, it must call the generator's stop() method to
    stop the background thread. Example usage:

    >>> gen = ThreadedGenerator(target=range, args=(20,))
    >>> try:
    ...     data = list(gen)
    ... finally:
    ...     gen.stop()
    >>> data
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

    """

    def __init__(self, group=None, target=None, name='GeneratorThread',
                 args=(), kwargs=None, qsize=65536):
        """Initializer. Takes same keyword arguments as threading.Thread.

        target must be a generator function (or other callable that returns
        an iterable object).

        @param qsize: The size of the lookahead queue. The larger the qsize,
            the more values will be computed in advance of use (which can eat
            up memory and processor time).
        @type qsize: int
        """
        if kwargs is None:
            kwargs = {}
        if target:
            self.generator = target
        if not hasattr(self, 'generator'):
            raise RuntimeError('No generator for ThreadedGenerator to run.')
        self.args, self.kwargs = args, kwargs
        threading.Thread.__init__(self, group=group, name=name)
        self.queue = queue.Queue(qsize)
        self.finished = threading.Event()

    def __iter__(self):
        """Iterate results from the queue."""
        if not self.is_alive() and not self.finished.isSet():
            self.start()
        # if there is an item in the queue, yield it, otherwise wait
        while not self.finished.isSet():
            try:
                yield self.queue.get(True, 0.25)
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        """Stop the background thread."""
        self.finished.set()

    def run(self):
        """Run the generator and store the results on the queue."""
        iterable = any(hasattr(self.generator, key)
                       for key in ('__iter__', '__getitem__'))
        if iterable and not self.args and not self.kwargs:
            self.__gen = self.generator
        else:
            self.__gen = self.generator(*self.args, **self.kwargs)
        for result in self.__gen:
            while True:
                if self.finished.isSet():
                    return
                try:
                    self.queue.put_nowait(result)
                except queue.Full:
                    time.sleep(0.25)
                    continue
                break
        # wait for queue to be emptied, then kill the thread
        while not self.finished.isSet() and not self.queue.empty():
            time.sleep(0.25)
        self.stop()


def itergroup(iterable, size):
    """Make an iterator that returns lists of (up to) size items from iterable.

    Example:

    >>> i = itergroup(range(25), 10)
    >>> print(next(i))
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    >>> print(next(i))
    [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    >>> print(next(i))
    [20, 21, 22, 23, 24]
    >>> print(next(i))
    Traceback (most recent call last):
     ...
    StopIteration

    """
    group = []
    for item in iterable:
        group.append(item)
        if len(group) == size:
            yield group
            group = []
    if group:
        yield group


def islice_with_ellipsis(iterable, *args, **kwargs):
    """
    Generator which yields the first n elements of the iterable.

    If more elements are available and marker is True, it returns an extra
    string marker as continuation mark.

    Function takes the
    and the additional keyword marker.

    @param iterable: the iterable to work on
    @type iterable: iterable
    @param args: same args as:
        - C{itertools.islice(iterable, stop)}
        - C{itertools.islice(iterable, start, stop[, step])}
    @keyword marker: element to yield if iterable still contains elements
        after showing the required number.
        Default value: '…'
        No other kwargs are considered.
    @type marker: str
    """
    s = slice(*args)
    marker = kwargs.pop('marker', '…')
    try:
        k, v = kwargs.popitem()
        raise TypeError(
            "islice_with_ellipsis() take only 'marker' as keyword arg, not %s"
            % k)
    except KeyError:
        pass

    _iterable = iter(iterable)
    for el in itertools.islice(_iterable, *args):
        yield el
    if marker and s.stop is not None:
        try:
            next(_iterable)
        except StopIteration:
            pass
        else:
            yield marker


class ThreadList(list):

    """A simple threadpool class to limit the number of simultaneous threads.

    Any threading.Thread object can be added to the pool using the append()
    method. If the maximum number of simultaneous threads has not been reached,
    the Thread object will be started immediately; if not, the append() call
    will block until the thread is able to start.

    >>> pool = ThreadList(limit=10)
    >>> def work():
    ...     time.sleep(1)
    ...
    >>> for x in range(20):
    ...     pool.append(threading.Thread(target=work))
    ...

    """

    _logger = 'threadlist'

    def __init__(self, limit=128, wait_time=2, *args):
        """Initializer.

        @param limit: the number of simultaneous threads
        @type limit: int
        @param wait_time: how long to wait if active threads exceeds limit
        @type wait_time: int or float
        """
        self.limit = limit
        self.wait_time = wait_time
        super(ThreadList, self).__init__(*args)
        for item in self:
            if not isinstance(item, threading.Thread):
                raise TypeError("Cannot add '%s' to ThreadList" % type(item))

    def active_count(self):
        """Return the number of alive threads and delete all non-alive ones."""
        cnt = 0
        for item in self[:]:
            if item.is_alive():
                cnt += 1
            else:
                self.remove(item)
        return cnt

    def append(self, thd):
        """Add a thread to the pool and start it."""
        if not isinstance(thd, threading.Thread):
            raise TypeError("Cannot append '%s' to ThreadList" % type(thd))
        while self.active_count() >= self.limit:
            time.sleep(self.wait_time)
        super(ThreadList, self).append(thd)
        thd.start()
        debug("thread %d ('%s') started" % (len(self), type(thd)),
              self._logger)

    def stop_all(self):
        """Stop all threads the pool."""
        if self:
            debug('EARLY QUIT: Threads: %d' % len(self), self._logger)
        for thd in self:
            thd.stop()
            debug('EARLY QUIT: Queue size left in %s: %s'
                  % (thd, thd.queue.qsize()), self._logger)


def intersect_generators(genlist):
    """
    Intersect generators listed in genlist.

    Yield items only if they are yielded by all generators in genlist.
    Threads (via ThreadedGenerator) are used in order to run generators
    in parallel, so that items can be yielded before generators are
    exhausted.

    Threads are stopped when they are either exhausted or Ctrl-C is pressed.
    Quitting before all generators are finished is attempted if
    there is no more chance of finding an item in all queues.

    @param genlist: list of page generators
    @type genlist: list
    """
    # If any generator is empty, no pages are going to be returned
    for source in genlist:
        if not source:
            debug('At least one generator ({0!r}) is empty and execution was '
                  'skipped immediately.'.format(source), 'intersect')
            return

    # Item is cached to check that it is found n_gen
    # times before being yielded.
    cache = collections.defaultdict(set)
    n_gen = len(genlist)

    # Class to keep track of alive threads.
    # Start new threads and remove completed threads.
    thrlist = ThreadList()

    for source in genlist:
        threaded_gen = ThreadedGenerator(name=repr(source), target=source)
        threaded_gen.daemon = True
        thrlist.append(threaded_gen)

    while True:
        # Get items from queues in a round-robin way.
        for t in thrlist:
            try:
                # TODO: evaluate if True and timeout is necessary.
                item = t.queue.get(True, 0.1)

                # Cache entry is a set of thread.
                # Duplicates from same thread are not counted twice.
                cache[item].add(t)
                if len(cache[item]) == n_gen:
                    yield item
                    # Remove item from cache.
                    # No chance of seeing it again (see later: early stop).
                    cache.pop(item)

                active = thrlist.active_count()
                max_cache = n_gen
                if cache.values():
                    max_cache = max(len(v) for v in cache.values())
                # No. of active threads is not enough to reach n_gen.
                # We can quit even if some thread is still active.
                # There could be an item in all generators which has not yet
                # appeared from any generator. Only when we have lost one
                # generator, then we can bail out early based on seen items.
                if active < n_gen and n_gen - max_cache > active:
                    thrlist.stop_all()
                    return
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                thrlist.stop_all()
            finally:
                # All threads are done.
                if thrlist.active_count() == 0:
                    return


def roundrobin_generators(*iterables):
    """Yield simultaneous from each iterable.

    Sample:
    >>> tuple(roundrobin_generators('ABC', range(5)))
    ('A', 0, 'B', 1, 'C', 2, 3, 4)

    @param iterables: any iterable to combine in roundrobin way
    @type iterables: iterable
    @return: the combined generator of iterables
    @rtype: generator
    """
    return (item
            for item in itertools.chain.from_iterable(zip_longest(*iterables))
            if item is not None)


def filter_unique(iterable, container=None, key=None, add=None):
    """
    Yield unique items from an iterable, omitting duplicates.

    By default, to provide uniqueness, it puts the generated items into a
    set created as a local variable. It only yields items which are not
    already present in the local set.

    For large collections, this is not memory efficient, as a strong reference
    to every item is kept in a local set which can not be cleared.

    Also, the local set can't be re-used when chaining unique operations on
    multiple generators.

    To avoid these issues, it is advisable for the caller to provide their own
    container and set the key parameter to be the function L{hash}, or use a
    L{weakref} as the key.

    The container can be any object that supports __contains__.
    If the container is a set or dict, the method add or __setitem__ will be
    used automatically. Any other method may be provided explicitly using the
    add parameter.

    Beware that key=id is only useful for cases where id() is not unique.

    Note: This is not thread safe.

    @param iterable: the source iterable
    @type iterable: collections.abc.Iterable
    @param container: storage of seen items
    @type container: type
    @param key: function to convert the item to a key
    @type key: callable
    @param add: function to add an item to the container
    @type add: callable
    """
    if container is None:
        container = set()

    if not add:
        if hasattr(container, 'add'):
            def container_add(x):
                container.add(key(x) if key else x)

            add = container_add
        else:
            def container_setitem(x):
                container.__setitem__(key(x) if key else x,
                                      True)

            add = container_setitem

    for item in iterable:
        try:
            if (key(item) if key else item) not in container:
                add(item)
                yield item
        except StopIteration:
            return


class CombinedError(KeyError, IndexError):

    """An error that gets caught by both KeyError and IndexError."""


class EmptyDefault(str, Mapping):

    """
    A default for a not existing siteinfo property.

    It should be chosen if there is no better default known. It acts like an
    empty collections, so it can be iterated through it safely if treated as a
    list, tuple, set or dictionary. It is also basically an empty string.

    Accessing a value via __getitem__ will result in an combined KeyError and
    IndexError.
    """

    def __init__(self):
        """Initialise the default as an empty string."""
        str.__init__(self)

    def _empty_iter(self):
        """An iterator which does nothing and drops the argument."""
        return empty_iterator()

    def __getitem__(self, key):
        """Raise always a L{CombinedError}."""
        raise CombinedError(key)

    iteritems = itervalues = iterkeys = __iter__ = _empty_iter


EMPTY_DEFAULT = EmptyDefault()


class SelfCallMixin(object):

    """
    Return self when called.

    When '_own_desc' is defined it'll also issue a deprecation warning using
    issue_deprecation_warning('Calling ' + _own_desc, 'it directly').
    """

    def __call__(self):
        """Do nothing and just return itself."""
        if hasattr(self, '_own_desc'):
            issue_deprecation_warning('Calling {0}'.format(self._own_desc),
                                      'it directly', since='20150515')
        return self


class SelfCallDict(SelfCallMixin, dict):

    """Dict with SelfCallMixin."""


class SelfCallString(SelfCallMixin, str):

    """Unicode string with SelfCallMixin."""


class IteratorNextMixin(Iterator):

    """Backwards compatibility for Iterators."""

    if PY2:

        def next(self):
            """Python 2 next."""
            return self.__next__()


class DequeGenerator(IteratorNextMixin, collections.deque):

    """A generator that allows items to be added during generating."""

    def __next__(self):
        """Python 3 iterator method."""
        if len(self):
            return self.popleft()
        else:
            raise StopIteration


def open_archive(filename, mode='rb', use_extension=True):
    """
    Open a file and uncompress it if needed.

    This function supports bzip2, gzip, 7zip, lzma, and xz as compression
    containers. It uses the packages available in the standard library for
    bzip2, gzip, lzma, and xz so they are always available. 7zip is only
    available when a 7za program is available and only supports reading
    from it.

    The compression is either selected via the magic number or file ending.

    @param filename: The filename.
    @type filename: str
    @param use_extension: Use the file extension instead of the magic number
        to determine the type of compression (default True). Must be True when
        writing or appending.
    @type use_extension: bool
    @param mode: The mode in which the file should be opened. It may either be
        'r', 'rb', 'a', 'ab', 'w' or 'wb'. All modes open the file in binary
        mode. It defaults to 'rb'.
    @type mode: str
    @raises ValueError: When 7za is not available or the opening mode is
        unknown or it tries to write a 7z archive.
    @raises FileNotFoundError: When the filename doesn't exist and it tries
        to read from it or it tries to determine the compression algorithm (or
        IOError on Python 2).
    @raises OSError: When it's not a 7z archive but the file extension is 7z.
        It is also raised by bz2 when its content is invalid. gzip does not
        immediately raise that error but only on reading it.
    @raises lzma.LZMAError: When error occurs during compression or
        decompression or when initializing the state with lzma or xz.
    @raises ImportError: When file is compressed with bz2 but neither bz2 nor
        bz2file is importable, or when file is compressed with lzma or xz but
        lzma is not importable.
    @return: A file-like object returning the uncompressed data in binary mode.
    @rtype: file-like object
    """
    if mode in ('r', 'a', 'w'):
        mode += 'b'
    elif mode not in ('rb', 'ab', 'wb'):
        raise ValueError('Invalid mode: "{0}"'.format(mode))

    if use_extension:
        # if '.' not in filename, it'll be 1 character long but otherwise
        # contain the period
        extension = filename[filename.rfind('.'):][1:]
    else:
        if mode != 'rb':
            raise ValueError('Magic number detection only when reading')
        with open(filename, 'rb') as f:
            magic_number = f.read(8)
        if magic_number.startswith(b'BZh'):
            extension = 'bz2'
        elif magic_number.startswith(b'\x1F\x8B\x08'):
            extension = 'gz'
        elif magic_number.startswith(b"7z\xBC\xAF'\x1C"):
            extension = '7z'
        # Unfortunately, legacy LZMA container format has no magic number
        elif magic_number.startswith(b'\xFD7zXZ\x00'):
            extension = 'xz'
        else:
            extension = ''

    if extension == 'bz2':
        if isinstance(bz2, ImportError):
            raise bz2
        return bz2.BZ2File(filename, mode)
    if extension == 'gz':
        return gzip.open(filename, mode)
    if extension == '7z':
        if mode != 'rb':
            raise NotImplementedError('It is not possible to write a 7z file.')

        try:
            process = subprocess.Popen(['7za', 'e', '-bd', '-so', filename],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       bufsize=65535)
        except OSError:
            raise ValueError('7za is not installed or cannot '
                             'uncompress "{0}"'.format(filename))
        else:
            stderr = process.stderr.read()
            process.stderr.close()
            if stderr != b'':
                process.stdout.close()
                raise OSError(
                    'Unexpected STDERR output from 7za {0}'.format(stderr))
            else:
                return process.stdout
    if extension == 'lzma':
        if isinstance(lzma, ImportError):
            raise lzma
        return lzma.open(filename, mode, format=lzma.FORMAT_ALONE)
    if extension == 'xz':
        if isinstance(lzma, ImportError):
            raise lzma
        return lzma.open(filename, mode, format=lzma.FORMAT_XZ)
    # assume it's an uncompressed file
    return open(filename, 'rb')


def merge_unique_dicts(*args, **kwargs):
    """
    Return a merged dict and make sure that the original dicts keys are unique.

    The positional arguments are the dictionaries to be merged. It is also
    possible to define an additional dict using the keyword arguments.
    """
    args = list(args) + [dict(kwargs)]
    conflicts = set()
    result = {}
    for arg in args:
        conflicts |= set(arg.keys()) & set(result.keys())
        result.update(arg)
    if conflicts:
        raise ValueError('Multiple dicts contain the same keys: {0}'
                         .format(', '.join(sorted(UnicodeType(key)
                                                  for key in conflicts))))
    return result


# Decorators
#
# Decorator functions without parameters are _invoked_ differently from
# decorator functions with function syntax. For example, @deprecated causes
# a different invocation to @deprecated().

# The former is invoked with the decorated function as args[0].
# The latter is invoked with the decorator arguments as *args & **kwargs,
# and it must return a callable which will be invoked with the decorated
# function as args[0].

# The follow deprecators may support both syntax, e.g. @deprecated and
# @deprecated() both work. In order to achieve that, the code inspects
# args[0] to see if it callable. Therefore, a decorator must not accept
# only one arg, and that arg be a callable, as it will be detected as
# a deprecator without any arguments.


def signature(obj):
    """
    Safely return function Signature object (PEP 362).

    inspect.signature was introduced in 3.3, however backports are available.

    Any exception calling inspect.signature is ignored and None is returned.

    @param obj: Function to inspect
    @type obj: callable
    @rtype: inpect.Signature or None
    """
    try:
        return inspect.signature(obj)
    except (AttributeError, ValueError):
        return None


def add_decorated_full_name(obj, stacklevel=1):
    """Extract full object name, including class, and store in __full_name__.

    This must be done on all decorators that are chained together, otherwise
    the second decorator will have the wrong full name.

    @param obj: A object being decorated
    @type obj: object
    @param stacklevel: level to use
    @type stacklevel: int
    """
    if hasattr(obj, '__full_name__'):
        return
    # The current frame is add_decorated_full_name
    # The next frame is the decorator
    # The next frame is the object being decorated
    frame = sys._getframe(stacklevel + 1)
    class_name = frame.f_code.co_name
    if class_name and class_name != '<module>':
        obj.__full_name__ = '{}.{}.{}'.format(
            obj.__module__, class_name, obj.__name__)
    else:
        obj.__full_name__ = '{}.{}'.format(
            obj.__module__, obj.__name__)


def manage_wrapping(wrapper, obj):
    """Add attributes to wrapper and wrapped functions."""
    wrapper.__doc__ = obj.__doc__
    wrapper.__name__ = obj.__name__
    wrapper.__module__ = obj.__module__
    wrapper.__signature__ = signature(obj)

    if not hasattr(obj, '__full_name__'):
        add_decorated_full_name(obj, 2)
    wrapper.__full_name__ = obj.__full_name__

    # Use the previous wrappers depth, if it exists
    wrapper.__depth__ = getattr(obj, '__depth__', 0) + 1

    # Obtain the wrapped object from the previous wrapper
    wrapped = getattr(obj, '__wrapped__', obj)
    wrapper.__wrapped__ = wrapped

    # Increment the number of wrappers
    if hasattr(wrapped, '__wrappers__'):
        wrapped.__wrappers__ += 1
    else:
        wrapped.__wrappers__ = 1


def get_wrapper_depth(wrapper):
    """Return depth of wrapper function."""
    return wrapper.__wrapped__.__wrappers__ + (1 - wrapper.__depth__)


def add_full_name(obj):
    """
    A decorator to add __full_name__ to the function being decorated.

    This should be done for all decorators used in pywikibot, as any
    decorator that does not add __full_name__ will prevent other
    decorators in the same chain from being able to obtain it.

    This can be used to monkey-patch decorators in other modules.
    e.g.
    <xyz>.foo = add_full_name(<xyz>.foo)

    @param obj: The function to decorate
    @type obj: callable
    @return: decorating function
    @rtype: function
    """
    def outer_wrapper(*outer_args, **outer_kwargs):
        """Outer wrapper.

        The outer wrapper may be the replacement function if the decorated
        decorator was called without arguments, or the replacement decorator
        if the decorated decorator was called without arguments.

        @param outer_args: args
        @param outer_kwargs: kwargs
        """
        def inner_wrapper(*args, **kwargs):
            """Replacement function.

            If the decorator supported arguments, they are in outer_args,
            and this wrapper is used to process the args which belong to
            the function that the decorated decorator was decorating.

            @param args: args passed to the decorated function.
            @param kwargs: kwargs passed to the decorated function.
            """
            add_decorated_full_name(args[0])
            return obj(*outer_args, **outer_kwargs)(*args, **kwargs)

        inner_wrapper.__doc__ = obj.__doc__
        inner_wrapper.__name__ = obj.__name__
        inner_wrapper.__module__ = obj.__module__
        inner_wrapper.__signature__ = signature(obj)

        # The decorator being decorated may have args, so both
        # syntax need to be supported.
        if (len(outer_args) == 1 and len(outer_kwargs) == 0
                and callable(outer_args[0])):
            add_decorated_full_name(outer_args[0])
            return obj(outer_args[0])
        else:
            return inner_wrapper

    if not __debug__:
        return obj

    return outer_wrapper


def _build_msg_string(instead, since):
    """Build a deprecation warning message format string."""
    if not since:
        since = ''
    elif '.' in since:
        since = ' since release ' + since
    else:
        year_str = month_str = day_str = ''
        days = (datetime.utcnow() - datetime.strptime(since, '%Y%m%d')).days
        years = days // 365
        days = days % 365
        months = days // 30
        days = days % 30
        if years == 1:
            years = 0
            months += 12
        if years:
            year_str = '{0} years'.format(years)
        else:
            day_str = '{0} day{1}'.format(days, 's' if days != 1 else '')
        if months:
            month_str = '{0} month{1}'.format(
                months, 's' if months != 1 else '')
        if year_str and month_str:
            year_str += ' and '
        if month_str and day_str:
            month_str += ' and '
        since = ' for {0}{1}{2}'.format(year_str, month_str, day_str)
    if instead:
        msg = '{{0}} is deprecated{since}; use {{1}} instead.'
    else:
        msg = '{{0}} is deprecated{since}.'
    return msg.format(since=since)


def issue_deprecation_warning(name, instead=None, depth=2, warning_class=None,
                              since=None):
    """Issue a deprecation warning.

    @param name: the name of the deprecated object
    @type name: str
    @param instead: suggested replacement for the deprecated object
    @type instead: str or None
    @param depth: depth + 1 will be used as stacklevel for the warnings
    @type depth: int
    @param warning_class: a warning class (category) to be used, defaults to
        DeprecationWarning
    @type warning_class: type
    @param since: a timestamp string of the date when the method was
        deprecated (form 'YYYYMMDD') or a version string.
    @type since: str or None
    """
    msg = _build_msg_string(instead, since)
    if warning_class is None:
        warning_class = (DeprecationWarning
                         if instead else _NotImplementedWarning)
    warn(msg.format(name, instead), warning_class, depth + 1)


@add_full_name
def deprecated(*args, **kwargs):
    """Decorator to output a deprecation warning.

    @kwarg instead: if provided, will be used to specify the replacement
    @type instead: str
    @kwarg since: a timestamp string of the date when the method was
        deprecated (form 'YYYYMMDD') or a version string.
    @type since: str
    @kwarg future_warning: if True a FutureWarning will be thrown,
        otherwise it defaults to DeprecationWarning
    @type future_warning: bool
    """
    def decorator(obj):
        """Outer wrapper.

        The outer wrapper is used to create the decorating wrapper.

        @param obj: function being wrapped
        @type obj: object
        """
        def wrapper(*args, **kwargs):
            """Replacement function.

            @param args: args passed to the decorated function.
            @param kwargs: kwargs passed to the decorated function.
            @return: the value returned by the decorated function
            @rtype: any
            """
            name = obj.__full_name__
            depth = get_wrapper_depth(wrapper) + 1
            issue_deprecation_warning(
                name, instead, depth, since=since,
                warning_class=FutureWarning if future_warning else None)
            return obj(*args, **kwargs)

        def add_docstring(wrapper):
            """Add a Deprecated notice to the docstring."""
            deprecation_notice = 'Deprecated'
            if instead:
                deprecation_notice += '; use ' + instead + ' instead'
            deprecation_notice += '.\n\n'
            if wrapper.__doc__:  # Append old docstring after the notice
                wrapper.__doc__ = deprecation_notice + wrapper.__doc__
            else:
                wrapper.__doc__ = deprecation_notice

        if not __debug__:
            return obj

        manage_wrapping(wrapper, obj)

        # Regular expression to find existing deprecation notices
        deprecated_notice = re.compile(r'(^|\s)DEPRECATED[.:;,]',
                                       re.IGNORECASE)

        # Add the deprecation notice to the docstring if not present
        if not wrapper.__doc__:
            add_docstring(wrapper)
        else:
            if not deprecated_notice.search(wrapper.__doc__):
                add_docstring(wrapper)
            else:
                # Get docstring up to @params so deprecation notices for
                # parameters don't disrupt it
                trim_params = re.compile(r'^.*?((?=@param)|$)', re.DOTALL)
                trimmed_doc = trim_params.match(wrapper.__doc__).group(0)

                if not deprecated_notice.search(trimmed_doc):  # No notice
                    add_docstring(wrapper)

        return wrapper

    since = kwargs.pop('since', None)
    future_warning = kwargs.pop('future_warning', False)
    without_parameters = (len(args) == 1 and len(kwargs) == 0
                          and callable(args[0]))
    if 'instead' in kwargs:
        instead = kwargs['instead']
    elif not without_parameters and len(args) == 1:
        instead = args[0]
    else:
        instead = False

    # When called as @deprecated, return a replacement function
    if without_parameters:
        if not __debug__:
            return args[0]

        return decorator(args[0])
    # Otherwise return a decorator, which returns a replacement function
    else:
        return decorator


def deprecate_arg(old_arg, new_arg):
    """Decorator to declare old_arg deprecated and replace it with new_arg."""
    return deprecated_args(**{old_arg: new_arg})


def deprecated_args(**arg_pairs):
    """
    Decorator to declare multiple args deprecated.

    @param arg_pairs: Each entry points to the new argument name. With True or
        None it drops the value and prints a warning. If False it just drops
        the value.
    """
    def decorator(obj):
        """Outer wrapper.

        The outer wrapper is used to create the decorating wrapper.

        @param obj: function being wrapped
        @type obj: object
        """
        def wrapper(*__args, **__kw):
            """Replacement function.

            @param __args: args passed to the decorated function
            @param __kw: kwargs passed to the decorated function
            @return: the value returned by the decorated function
            @rtype: any
            """
            name = obj.__full_name__
            depth = get_wrapper_depth(wrapper) + 1
            for old_arg, new_arg in arg_pairs.items():
                output_args = {
                    'name': name,
                    'old_arg': old_arg,
                    'new_arg': new_arg,
                }
                if old_arg in __kw:
                    if new_arg not in [True, False, None]:
                        if new_arg in __kw:
                            warn('%(new_arg)s argument of %(name)s '
                                 'replaces %(old_arg)s; cannot use both.'
                                 % output_args,
                                 RuntimeWarning, depth)
                        else:
                            # If the value is positionally given this will
                            # cause a TypeError, which is intentional
                            warn('%(old_arg)s argument of %(name)s '
                                 'is deprecated; use %(new_arg)s instead.'
                                 % output_args,
                                 DeprecationWarning, depth)
                            __kw[new_arg] = __kw[old_arg]
                    else:
                        if new_arg is False:
                            cls = PendingDeprecationWarning
                        else:
                            cls = DeprecationWarning
                        warn('%(old_arg)s argument of %(name)s is deprecated.'
                             % output_args,
                             cls, depth)
                    del __kw[old_arg]
            return obj(*__args, **__kw)

        if not __debug__:
            return obj

        manage_wrapping(wrapper, obj)

        if wrapper.__signature__:
            # Build a new signature with deprecated args added.
            # __signature__ is only available in Python 3 which has OrderedDict
            params = collections.OrderedDict()
            for param in wrapper.__signature__.parameters.values():
                params[param.name] = param.replace()
            for old_arg, new_arg in arg_pairs.items():
                params[old_arg] = inspect.Parameter(
                    old_arg, kind=inspect._POSITIONAL_OR_KEYWORD,
                    default='[deprecated name of ' + new_arg + ']'
                    if new_arg not in [True, False, None]
                    else NotImplemented)
            params = collections.OrderedDict(sorted(params.items(),
                                                    key=lambda x: x[1].kind))
            wrapper.__signature__ = inspect.Signature()
            wrapper.__signature__._parameters = params

        return wrapper
    return decorator


def remove_last_args(arg_names):
    """
    Decorator to declare all args additionally provided deprecated.

    All positional arguments appearing after the normal arguments are marked
    deprecated. It marks also all keyword arguments present in arg_names as
    deprecated. Any arguments (positional or keyword) which are not present in
    arg_names are forwarded. For example a call with 3 parameters and the
    original function requests one and arg_names contain one name will result
    in an error, because the function got called with 2 parameters.

    The decorated function may not use C{*args} or C{**kwargs}.

    @param arg_names: The names of all arguments.
    @type arg_names: iterable; for the most explanatory message it should
        retain the given order (so not a set for example).
    """
    def decorator(obj):
        """Outer wrapper.

        The outer wrapper is used to create the decorating wrapper.

        @param obj: function being wrapped
        @type obj: object
        """
        def wrapper(*__args, **__kw):
            """Replacement function.

            @param __args: args passed to the decorated function
            @param __kw: kwargs passed to the decorated function
            @return: the value returned by the decorated function
            @rtype: any
            """
            name = obj.__full_name__
            depth = get_wrapper_depth(wrapper) + 1
            args, varargs, kwargs, _ = getargspec(wrapper.__wrapped__)
            if varargs is not None and kwargs is not None:
                raise ValueError('{0} may not have * or ** args.'.format(
                    name))
            deprecated = set(__kw) & set(arg_names)
            if len(__args) > len(args):
                deprecated.update(arg_names[:len(__args) - len(args)])
            # remove at most |arg_names| entries from the back
            new_args = tuple(__args[:max(len(args),
                                         len(__args) - len(arg_names))])
            new_kwargs = {arg: val for arg, val in __kw.items()
                          if arg not in arg_names}

            if deprecated:
                # sort them according to arg_names
                deprecated = [arg for arg in arg_names if arg in deprecated]
                warn("The trailing arguments ('{0}') of {1} are deprecated. "
                     "The value(s) provided for '{2}' have been dropped.".
                     format("', '".join(arg_names),
                            name,
                            "', '".join(deprecated)),
                     DeprecationWarning, depth)
            return obj(*new_args, **new_kwargs)

        manage_wrapping(wrapper, obj)

        return wrapper
    return decorator


def redirect_func(target, source_module=None, target_module=None,
                  old_name=None, class_name=None, since=None,
                  future_warning=False):
    """
    Return a function which can be used to redirect to 'target'.

    It also acts like marking that function deprecated and copies all
    parameters.

    @param target: The targeted function which is to be executed.
    @type target: callable
    @param source_module: The module of the old function. If '.' defaults
        to target_module. If 'None' (default) it tries to guess it from the
        executing function.
    @type source_module: basestring
    @param target_module: The module of the target function. If
        'None' (default) it tries to get it from the target. Might not work
        with nested classes.
    @type target_module: basestring
    @param old_name: The old function name. If None it uses the name of the
        new function.
    @type old_name: basestring
    @param class_name: The name of the class. It's added to the target and
        source module (separated by a '.').
    @type class_name: basestring
    @param since: a timestamp string of the date when the method was
        deprecated (form 'YYYYMMDD') or a version string.
    @type since: str
    @param future_warning: if True a FutureWarning will be thrown,
        otherwise it defaults to DeprecationWarning
    @type future_warning: bool
    @return: A new function which adds a warning prior to each execution.
    @rtype: callable
    """
    def call(*a, **kw):
        issue_deprecation_warning(
            old_name, new_name, since=since,
            warning_class=FutureWarning if future_warning else None)
        return target(*a, **kw)
    if target_module is None:
        target_module = target.__module__
    if target_module and target_module[-1] != '.':
        target_module += '.'
    if source_module == '.':
        source_module = target_module
    elif source_module and source_module[-1] != '.':
        source_module += '.'
    else:
        source_module = sys._getframe(1).f_globals['__name__'] + '.'
    if class_name:
        target_module += class_name + '.'
        source_module += class_name + '.'
    old_name = source_module + (old_name or target.__name__)
    new_name = target_module + target.__name__

    if not __debug__:
        return target

    return call


class ModuleDeprecationWrapper(types.ModuleType):

    """A wrapper for a module to deprecate classes or variables of it."""

    def __init__(self, module):
        """
        Initialise the wrapper.

        It will automatically overwrite the module with this instance in
        C{sys.modules}.

        @param module: The module name or instance
        @type module: str or module
        """
        if isinstance(module, StringTypes):
            module = sys.modules[module]
        super(ModuleDeprecationWrapper, self).__setattr__('_deprecated', {})
        super(ModuleDeprecationWrapper, self).__setattr__('_module', module)
        self.__dict__.update(module.__dict__)

        if __debug__:
            sys.modules[module.__name__] = self

    def _add_deprecated_attr(self, name, replacement=None,
                             replacement_name=None, warning_message=None,
                             since=None, future_warning=False):
        """
        Add the name to the local deprecated names dict.

        @param name: The name of the deprecated class or variable. It may not
            be already deprecated.
        @type name: str
        @param replacement: The replacement value which should be returned
            instead. If the name is already an attribute of that module this
            must be None. If None it'll return the attribute of the module.
        @type replacement: any
        @param replacement_name: The name of the new replaced value. Required
            if C{replacement} is not None and it has no __name__ attribute.
            If it contains a '.', it will be interpreted as a Python dotted
            object name, and evaluated when the deprecated object is needed.
        @type replacement_name: str
        @param warning_message: The warning to display, with positional
            variables: {0} = module, {1} = attribute name, {2} = replacement.
        @type warning_message: basestring
        @param since: a timestamp string of the date when the method was
            deprecated (form 'YYYYMMDD') or a version string.
        @type since: str
        @param future_warning: if True a FutureWarning will be thrown,
            otherwise it defaults to DeprecationWarning
        @type future_warning: bool
        """
        if '.' in name:
            raise ValueError('Deprecated name "{0}" may not contain '
                             '".".'.format(name))
        if name in self._deprecated:
            raise ValueError('Name "{0}" is already deprecated.'.format(name))
        if replacement is not None and hasattr(self._module, name):
            raise ValueError('Module has already an attribute named '
                             '"{0}".'.format(name))

        if replacement_name is None:
            if hasattr(replacement, '__name__'):
                replacement_name = replacement.__module__
                if hasattr(replacement, '__self__'):
                    replacement_name += '.'
                    replacement_name += replacement.__self__.__class__.__name__
                replacement_name += '.' + replacement.__name__
            else:
                raise TypeError('Replacement must have a __name__ attribute '
                                'or a replacement name must be set '
                                'specifically.')

        if not warning_message:
            warning_message = _build_msg_string(
                replacement_name, since).format('{0}.{1}', '{2}')
        if hasattr(self, name):
            # __getattr__ will only be invoked if self.<name> does not exist.
            delattr(self, name)
        self._deprecated[name] = (
            replacement_name, replacement, warning_message, future_warning)

    def __setattr__(self, attr, value):
        """Set the value of the wrapped module."""
        self.__dict__[attr] = value
        setattr(self._module, attr, value)

    def __getattr__(self, attr):
        """Return the attribute with a deprecation warning if required."""
        if attr in self._deprecated:
            name, repl, message, future = self._deprecated[attr]
            warning_message = message
            warn(warning_message.format(self._module.__name__, attr, name),
                 FutureWarning if future else DeprecationWarning, 2)
            if repl:
                return repl
            elif '.' in name:
                try:
                    package_name = name.split('.', 1)[0]
                    module = import_module(package_name)
                    context = {package_name: module}
                    replacement = eval(name, context)
                    self._deprecated[attr] = (
                        name, replacement, message, future)
                    return replacement
                except Exception:
                    pass
        return getattr(self._module, attr)


@deprecated('open_archive()', since='20150915')
def open_compressed(filename, use_extension=False):
    """DEPRECATED: Open a file and uncompress it if needed."""
    return open_archive(filename, use_extension=use_extension)


def file_mode_checker(filename, mode=0o600, quiet=False, create=False):
    """Check file mode and update it, if needed.

    @param filename: filename path
    @type filename: basestring
    @param mode: requested file mode
    @type mode: int
    @param quiet: warn about file mode change if False.
    @type quiet: bool
    @param create: create the file if it does not exist already
    @type create: bool
    @raise IOError: The file does not exist and `create` is False.
    """
    try:
        st_mode = os.stat(filename).st_mode
    except OSError:  # file does not exist
        if not create:
            raise
        os.close(os.open(filename, os.O_CREAT | os.O_EXCL, mode))
        return
    warn_str = 'File {0} had {1:o} mode; converted to {2:o} mode.'
    if stat.S_ISREG(st_mode) and (st_mode - stat.S_IFREG != mode):
        os.chmod(filename, mode)
        # re-read and check changes
        if os.stat(filename).st_mode != st_mode and not quiet:
            warn(warn_str.format(filename, st_mode - stat.S_IFREG, mode))


def compute_file_hash(filename, sha='sha1', bytes_to_read=None):
    """Compute file hash.

    Result is expressed as hexdigest().

    @param filename: filename path
    @type filename: basestring

    @param func: hashing function among the following in hashlib:
        md5(), sha1(), sha224(), sha256(), sha384(), and sha512()
        function name shall be passed as string, e.g. 'sha1'.
    @type filename: basestring

    @param bytes_to_read: only the first bytes_to_read will be considered;
        if file size is smaller, the whole file will be considered.
    @type bytes_to_read: None or int

    """
    size = os.path.getsize(filename)
    if bytes_to_read is None:
        bytes_to_read = size
    else:
        bytes_to_read = min(bytes_to_read, size)
    step = 1 << 20

    shas = ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
    assert sha in shas
    sha = getattr(hashlib, sha)()  # sha instance

    with open(filename, 'rb') as f:
        while bytes_to_read > 0:
            read_bytes = f.read(min(bytes_to_read, step))
            assert read_bytes  # make sure we actually read bytes
            bytes_to_read -= len(read_bytes)
            sha.update(read_bytes)
    return sha.hexdigest()

# deprecated parts ############################################################


class ContextManagerWrapper(object):

    """
    DEPRECATED. Wraps an object in a context manager.

    It is redirecting all access to the wrapped object and executes 'close'
    when used as a context manager in with-statements. In such statements the
    value set via 'as' is directly the wrapped object. For example:

    >>> class Wrapper(object):
    ...     def close(self): pass
    >>> an_object = Wrapper()
    >>> wrapped = ContextManagerWrapper(an_object)
    >>> with wrapped as another_object:
    ...      assert another_object is an_object

    It does not subclass the object though, so isinstance checks will fail
    outside a with-statement.
    """

    def __init__(self, wrapped):
        """Create a new wrapper."""
        super(ContextManagerWrapper, self).__init__()
        super(ContextManagerWrapper, self).__setattr__('_wrapped', wrapped)

    def __enter__(self):
        """Enter a context manager and use the wrapped object directly."""
        return self._wrapped

    def __exit__(self, exc_type, exc_value, traceback):
        """Call close on the wrapped object when exiting a context manager."""
        self._wrapped.close()

    def __getattr__(self, name):
        """Get the attribute from the wrapped object."""
        return getattr(self._wrapped, name)

    def __setattr__(self, name, value):
        """Set the attribute in the wrapped object."""
        setattr(self._wrapped, name, value)


@deprecated('bot_choice.Option and its subclasses', since='20181217')
def concat_options(message, line_length, options):
    """DEPRECATED. Concatenate options."""
    indent = len(message) + 2
    line_length -= indent
    option_msg = ''
    option_line = ''
    for option in options:
        if option_line:
            option_line += ', '
        # +1 for ','
        if len(option_line) + len(option) + 1 > line_length:
            if option_msg:
                option_msg += '\n' + ' ' * indent
            option_msg += option_line[:-1]  # remove space
            option_line = ''
        option_line += option
    if option_line:
        if option_msg:
            option_msg += '\n' + ' ' * indent
        option_msg += option_line
    return '{0} ({1}):'.format(message, option_msg)


wrapper = ModuleDeprecationWrapper(__name__)
wrapper._add_deprecated_attr('Counter', collections.Counter, since='20160111')
wrapper._add_deprecated_attr('OrderedDict', collections.OrderedDict,
                             since='20160111')
wrapper._add_deprecated_attr('count', itertools.count, since='20160111')
wrapper._add_deprecated_attr('ContextManagerWrapper', replacement_name='',
                             since='20180402')
