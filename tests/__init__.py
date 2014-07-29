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

if sys.version_info < (2, 7):
    # Unittest2 is a backport of python 2.7s unittest module to python 2.6
    import unittest2 as unittest
else:
    import unittest

import pywikibot.data.api
from pywikibot.data.api import Request as _original_Request
from pywikibot.data.api import CachedRequest

_tests_dir = os.path.split(__file__)[0]
_cache_dir = os.path.join(_tests_dir, 'apicache')

library_test_modules = [
    'date',
    'ipregex',
    'xmlreader',
    'textlib',
    'http',
    'namespace',
    'dry_api',
    'dry_site',
    'api',
    'site',
    'page',
    'file',
    'timestripper',
    'pagegenerators',
    'wikidataquery',
    'weblib',
    'i18n',
    'ui',
    'wikibase',
]

script_test_modules = [
    'pwb',
    'script',
    'archivebot',
]

disabled_test_modules = [
    'ui',
]

if os.environ.get('TRAVIS', 'false') == 'true':
    disabled_test_modules.append('weblib')

disabled_tests = {
    'textlib': [
        'test_interwiki_format',  # example; very slow test
    ]
}


def _unknown_test_modules():
    """List tests which are to be executed."""
    dir_list = os.listdir(_tests_dir)
    all_test_list = [name[0:-9] for name in dir_list  # strip '_tests.py'
                     if name.endswith('_tests.py')
                     and not name.startswith('_')]   # skip __init__.py and _*

    unknown_test_modules = [name
                            for name in all_test_list
                            if name not in library_test_modules
                            and name not in script_test_modules]

    return unknown_test_modules


extra_test_modules = sorted(_unknown_test_modules())

test_modules = library_test_modules + extra_test_modules + script_test_modules


def collector(loader=unittest.loader.defaultTestLoader):
    """Load the default modules.

    This is the entry point is specified in setup.py
    """
    # Note: Raising SkipTest during load_tests will
    # cause the loader to fallback to its own
    # discover() ordering of unit tests.
    if disabled_test_modules:
        print('Disabled test modules (to run: python -m unittest ...):\n  %s'
              % ', '.join(disabled_test_modules))

    if extra_test_modules:
        print('Extra test modules (run after library, before scripts):\n  %s'
              % ', '.join(extra_test_modules))

    if disabled_tests:
        print('Skipping tests (to run: python -m unittest ...):\n  %r'
              % disabled_tests)

    modules = [module
               for module in library_test_modules +
                             extra_test_modules +
                             script_test_modules
               if module not in disabled_test_modules]

    test_list = []

    for module in modules:
        module_class_name = 'tests.' + module + '_tests'
        if module in disabled_tests:
            discovered = loader.loadTestsFromName(module_class_name)
            enabled_tests = []
            for cls in discovered:
                for test_func in cls:
                    if test_func._testMethodName not in disabled_tests[module]:
                        enabled_tests.append(
                            module_class_name + '.' +
                            test_func.__class__.__name__ + '.' +
                            test_func._testMethodName)

            test_list.extend(enabled_tests)
        else:
            test_list.append(module_class_name)

    tests = loader.loadTestsFromNames(test_list)
    suite = unittest.TestSuite()
    suite.addTests(tests)
    return suite


def load_tests(loader=unittest.loader.defaultTestLoader,
               tests=None, pattern=None):
    """Load the default modules."""
    return collector(loader)


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

        if 'lgpassword' in self._uniquedescriptionstr():
            self._data = None
            return False

        return True

    def _write_cache(self, data):
        """Write data except login details."""
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
