# -*- coding: utf-8  -*-
"""Test utilities."""
#
# (C) Pywikibot team, 2013-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import print_function
__version__ = '$Id$'
#
import os
import subprocess
import sys
import time

import pywikibot
from pywikibot.tools import SelfCallDict
from pywikibot.site import Namespace
from pywikibot.data.api import CachedRequest
from pywikibot.data.api import Request as _original_Request

from tests import aspects, _pwb_py
from tests import unittest  # noqa

BaseTestCase = aspects.TestCase
NoSiteTestCase = aspects.TestCase
SiteTestCase = aspects.TestCase
CachedTestCase = aspects.TestCase
PywikibotTestCase = aspects.TestCase


def expected_failure_if(expect):
    """
    Unit test decorator to expect failure under conditions.

    @param expect: Flag to check if failure is expected
    @type expect: bool
    """
    if expect:
        return unittest.expectedFailure
    else:
        return lambda orig: orig


def allowed_failure(func):
    """
    Unit test decorator to allow failure.

    Test runners each have different interpretations of what should be
    the result of an @expectedFailure test if it succeeds.  Some consider
    it to be a pass; others a failure.

    This decorator runs the test and, if it is a failure, reports the result
    and considers it a skipped test.
    """
    def wrapper(*args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception:
            pywikibot.exception(tb=True)
            raise unittest.SkipTest()
    wrapper.__name__ = func.__name__
    return wrapper


def allowed_failure_if(expect):
    """
    Unit test decorator to allow failure under conditions.

    @param expect: Flag to check if failure is allowed
    @type expect: bool
    """
    if expect:
        return allowed_failure
    else:
        return lambda orig: orig


class DummySiteinfo():

    """Dummy class to use instead of L{pywikibot.site.Siteinfo}."""

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


class DryRequest(CachedRequest):

    """Dummy class to use instead of L{pywikibot.data.api.Request}."""

    def __init__(self, *args, **kwargs):
        _original_Request.__init__(self, *args, **kwargs)

    def _expired(self, dt):
        """Never invalidate cached data."""
        return False

    def _write_cache(self, data):
        """Never write data."""
        return

    def submit(self):
        raise Exception(u'DryRequest rejecting request: %r'
                        % self._params)


class DrySite(pywikibot.site.APISite):

    """Dummy class to use instead of L{pywikibot.site.APISite}."""

    _loginstatus = pywikibot.site.LoginStatus.NOT_ATTEMPTED

    def __init__(self, code, fam, user, sysop):
        """Constructor."""
        super(DrySite, self).__init__(code, fam, user, sysop)
        self._userinfo = pywikibot.tools.EMPTY_DEFAULT
        self._siteinfo = DummySiteinfo({})
        self._siteinfo._cache['lang'] = (code, True)
        self._namespaces = SelfCallDict(Namespace.builtin_namespaces())

    @property
    def userinfo(self):
        return self._userinfo

    def version(self):
        return self.family.version(self.code)

    def case(self):
        if self.family.name == 'wiktionary':
            return 'case-sensitive'
        else:
            return 'first-letter'

    def image_repository(self):
        """Return Site object for image repository e.g. commons."""
        code, fam = self.shared_image_repository()
        if bool(code or fam):
            return pywikibot.Site(code, fam, self.username(),
                                  interface=self.__class__)

    def data_repository(self):
        """Return Site object for data repository e.g. Wikidata."""
        code, fam = self.shared_data_repository()
        if bool(code or fam):
            return pywikibot.Site(code, fam, self.username(),
                                  interface=DryDataSite)


class DryDataSite(DrySite, pywikibot.site.DataSite):

    """Dummy class to use instead of L{pywikibot.site.DataSite}."""

    def __init__(self, code, fam, user, sysop):
        """Constructor."""
        super(DryDataSite, self).__init__(code, fam, user, sysop)

        self._namespaces[0].defaultcontentmodel = 'wikibase-item'

        self._namespaces.update(
            {
                120: Namespace(id=120,
                               case='first-letter',
                               canonical_name='Property',
                               defaultcontentmodel='wikibase-property')
            })


def execute(command, data_in=None, timeout=0, error=None):
    """
    Execute a command and capture outputs.

    @param command: executable to run and arguments to use
    @type command: list of unicode
    """
    def decode(stream):
        if sys.version_info[0] > 2:
            return stream.decode(pywikibot.config.console_encoding)
        else:
            return stream
    env = os.environ.copy()
    # sys.path may have been modified by the test runner to load dependencies.
    env['PYTHONPATH'] = ":".join(sys.path)
    # Set EDITOR to an executable that ignores all arguments and does nothing.
    if sys.platform == 'win32':
        env['EDITOR'] = 'call'
    else:
        env['EDITOR'] = 'true'
    options = {
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE
    }
    if data_in is not None:
        options['stdin'] = subprocess.PIPE

    p = subprocess.Popen(command, env=env, **options)

    if data_in is not None:
        if sys.version_info[0] > 2:
            data_in = data_in.encode(pywikibot.config.console_encoding)
        p.stdin.write(data_in)
        p.stdin.flush()  # _communicate() otherwise has a broken pipe

    stderr_lines = b''
    waited = 0
    while (error or (waited < timeout)) and p.poll() is None:
        # In order to kill 'shell' and others early, read only a single
        # line per second, and kill the process as soon as the expected
        # output has been seen.
        # Additional lines will be collected later with p.communicate()
        if error:
            line = p.stderr.readline()
            stderr_lines += line
            if error in decode(line):
                break
        time.sleep(1)
        waited += 1

    if (timeout or error) and p.poll() is None:
        p.kill()

    if p.poll() is not None:
        stderr_lines += p.stderr.read()

    data_out = p.communicate()
    return {'exit_code': p.returncode,
            'stdout': decode(data_out[0]),
            'stderr': decode(stderr_lines + data_out[1])}


def execute_pwb(args, data_in=None, timeout=0, error=None):
    """
    Execute the pwb.py script and capture outputs.

    @param args: list of arguments for pwb.py
    @type args: list of unicode
    """
    return execute(command=[sys.executable, _pwb_py] + args,
                   data_in=data_in, timeout=timeout, error=error)
