# -*- coding: utf-8 -*-
"""
Test aspects to allow fine grained control over what tests are executed.

Several parts of the test infrastructure are implemented as mixins,
such as API result caching and excessive test durations. An unused
mixin to show cache usage is included.
"""
#
# (C) Pywikibot team, 2014-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, print_function, unicode_literals
__version__ = '$Id$'
"""
    TODO:

        skip if the user is blocked.
        sysop flag, implement in site & page, and
            possibly some of the script tests.
        labs flag, for wikidataquery
        slow flag
            wikiquerydata - quite slow
            weblib - also slow
            (this class, and a FastTest, could error/pass based
             it consumed more than a specified amount of time allowed.)
        net flag should disable network libraries
        UITestCase:
            Not integrated; direct subclass of unittest.TestCase.
"""
import inspect
import itertools
import os
import re
import sys
import time
import warnings

from contextlib import contextmanager

import pywikibot

import pywikibot.config2 as config

from pywikibot import Site

from pywikibot.comms import http
from pywikibot.data.api import Request as _original_Request
from pywikibot.exceptions import ServerError, NoUsername
from pywikibot.family import WikimediaFamily
from pywikibot.site import BaseSite
from pywikibot.tools import PY2, StringTypes

import tests

from tests import unittest, patch_request, unpatch_request
from tests.utils import (
    add_metaclass, execute_pwb, DrySite, DryRequest,
    WarningSourceSkipContextManager, AssertAPIErrorContextManager,
)

try:
    import pytest_httpbin
    optional_pytest_httpbin_cls_decorator = pytest_httpbin.use_class_based_httpbin
except ImportError:
    pytest_httpbin = None

    def optional_pytest_httpbin_cls_decorator(f):
        """Empty decorator in case pytest_httpbin is not installed."""
        return f

OSWIN32 = (sys.platform == 'win32')


class TestCaseBase(unittest.TestCase):

    """Base class for all tests."""

    if not hasattr(unittest.TestCase, 'assertRaisesRegex'):
        def assertRaisesRegex(self, *args, **kwargs):
            """
            Wrapper of unittest.assertRaisesRegexp for Python 2 unittest.

            assertRaisesRegexp is deprecated in Python 3.
            """
            return self.assertRaisesRegexp(*args, **kwargs)

    if not hasattr(unittest.TestCase, 'assertRegex'):
        def assertRegex(self, *args, **kwargs):
            """
            Wrapper of unittest.assertRegexpMatches for Python 2 unittest.

            assertRegexpMatches is deprecated in Python 3.
            """
            return self.assertRegexpMatches(*args, **kwargs)

    if not hasattr(unittest.TestCase, 'assertCountEqual'):

        def assertCountEqual(self, *args, **kwargs):
            """
            Wrapper of unittest.assertItemsEqual for Python 2 unittest.

            assertItemsEqual is removed in Python 3.
            """
            return self.assertItemsEqual(*args, **kwargs)

    def _addUnexpectedSuccess(self, result):
        """Report and ignore."""
        print(' unexpected success ', end='')
        sys.stdout.flush()
        result.addSuccess(self)

    def _addExpectedFailure(self, result, exc_info=None):
        """Report and ignore."""
        print(' expected failure ', end='')
        sys.stdout.flush()
        result.addSuccess(self)

    def assertMethod(self, method, *args):
        """Generic method assertion."""
        if not method(*args):
            self.fail('{0!r} ({1!r}) fails'.format(method, args))

    def assertStringMethod(self, method, *args):
        """
        Generic string method assertion.

        All args must be already converted to a string.
        """
        for arg in args:
            self.assertIsInstance(arg, StringTypes)
        self.assertMethod(method, *args)

    def assertPageInNamespaces(self, page, namespaces):
        """
        Assert that Pages is in namespaces.

        @param page: Page
        @type page: Page
        @param namespaces: expected namespaces
        @type namespaces: int or set of int
        """
        if isinstance(namespaces, int):
            namespaces = set([namespaces])

        self.assertIn(page.namespace(), namespaces,
                      "%s not in namespace %r" % (page, namespaces))

    def _get_gen_pages(self, gen, count=None, site=None):
        """
        Get pages from gen, asserting they are Page from site.

        Iterates at most two greater than count, including the
        Page after count if it exists, and then a Page with title '...'
        if additional items are in the iterator.

        @param gen: Page generator
        @type gen: generator of Page
        @param count: number of pages to get
        @type titles: int
        @param site: Site of expected pages
        @type site: APISite
        """
        original_iter = iter(gen)

        gen = itertools.islice(original_iter, 0, count)

        gen_pages = list(gen)

        try:
            gen_pages.append(next(original_iter))
            next(original_iter)
            if not site:
                site = gen_pages[0].site
            gen_pages.append(pywikibot.Page(site, '...'))
        except StopIteration:
            pass

        for page in gen_pages:
            self.assertIsInstance(page, pywikibot.Page)
            if site:
                self.assertEqual(page.site, site)

        return gen_pages

    def _get_gen_titles(self, gen, count, site=None):
        gen_pages = self._get_gen_pages(gen, count, site)
        gen_titles = [page.title() for page in gen_pages]
        return gen_titles

    def _get_canonical_titles(self, titles, site=None):
        if site:
            titles = [pywikibot.Link(title, site).canonical_title()
                      for title in titles]
        elif not isinstance(titles, list):
            titles = list(titles)
        return titles

    def assertPagesInNamespaces(self, gen, namespaces):
        """
        Assert that generator returns Pages all in namespaces.

        @param gen: generator to iterate
        @type gen: generator
        @param namespaces: expected namespaces
        @type namespaces: int or set of int
        """
        if isinstance(namespaces, int):
            namespaces = set([namespaces])

        for page in gen:
            self.assertPageInNamespaces(page, namespaces)

    def assertPagesInNamespacesAll(self, gen, namespaces, skip=False):
        """
        Try to confirm that generator returns Pages for all namespaces.

        @param gen: generator to iterate
        @type gen: generator
        @param namespaces: expected namespaces
        @type namespaces: int or set of int
        @param count: maximum results to process
        @type count: int
        @param skip: skip test if not all namespaces found
        @param skip: bool
        """
        if isinstance(namespaces, int):
            namespaces = set([namespaces])
        else:
            assert isinstance(namespaces, set)

        page_namespaces = [page.namespace() for page in gen]

        if skip and set(page_namespaces) != namespaces:
            raise unittest.SkipTest('Pages in namespaces %r not found.'
                                    % list(namespaces - set(page_namespaces)))
        else:
            self.assertEqual(set(page_namespaces), namespaces)

    def assertPageTitlesEqual(self, gen, titles, site=None):
        """
        Test that pages in gen match expected titles.

        Only iterates to the length of titles plus two.

        @param gen: Page generator
        @type gen: generator of Page
        @param titles: Expected titles
        @type titles: iterator
        @param site: Site of expected pages
        @type site: APISite
        """
        titles = self._get_canonical_titles(titles, site)
        gen_titles = self._get_gen_titles(gen, len(titles), site)
        self.assertEqual(gen_titles, titles)

    def assertPageTitlesCountEqual(self, gen, titles, site=None):
        """
        Test that pages in gen match expected titles, regardless of order.

        Only iterates to the length of titles plus two.

        @param gen: Page generator
        @type gen: generator of Page
        @param titles: Expected titles
        @type titles: iterator
        @param site: Site of expected pages
        @type site: APISite
        """
        titles = self._get_canonical_titles(titles, site)
        gen_titles = self._get_gen_titles(gen, len(titles), site)
        self.assertCountEqual(gen_titles, titles)

    assertPagelistTitles = assertPageTitlesEqual

    def assertAPIError(self, code, info=None, callable_obj=None, *args,
                       **kwargs):
        """
        Assert that a specific APIError wrapped around L{assertRaises}.

        If no callable object is defined and it returns a context manager, that
        context manager will return the underlying context manager used by
        L{assertRaises}. So it's possible to access the APIError by using it's
        C{exception} attribute.

        @param code: The code of the error which must have happened.
        @type code: str
        @param info: The info string of the error or None if no it shouldn't be
            checked.
        @type info: str or None
        @param callable_obj: The object that will be tested. If None it returns
            a context manager like L{assertRaises}.
        @type callable_obj: callable
        @param args: The positional arguments forwarded to the callable object.
        @param kwargs: The keyword arguments forwared to the callable object.
        @return: The context manager if callable_obj is None and None otherwise.
        @rtype: None or context manager
        """
        msg = kwargs.pop('msg', None)
        return AssertAPIErrorContextManager(
            code, info, msg, self).handle(callable_obj, args, kwargs)


class TestTimerMixin(TestCaseBase):

    """Time each test and report excessive durations."""

    # Number of seconds each test may consume
    # before a note is added after the test.
    test_duration_warning_interval = 10

    def setUp(self):
        """Set up test."""
        super(TestTimerMixin, self).setUp()
        self.test_start = time.time()

    def tearDown(self):
        """Tear down test."""
        self.test_completed = time.time()
        duration = self.test_completed - self.test_start

        if duration > self.test_duration_warning_interval:
            print(' %0.3fs' % duration, end=' ')
            sys.stdout.flush()

        super(TestTimerMixin, self).tearDown()


def require_modules(*required_modules):
    """Require that the given list of modules can be imported."""
    def test_requirement(obj):
        """Test the requirement and return an optionally decorated object."""
        missing = []
        for required_module in required_modules:
            try:
                __import__(required_module, globals(), locals(), [], 0)
            except ImportError:
                missing += [required_module]
        if missing:
            skip_decorator = unittest.skip('{0} not installed'.format(
                ', '.join(missing)))
            if (inspect.isclass(obj) and issubclass(obj, TestCaseBase) and
                    'nose' in sys.modules.keys()):
                # There is a known bug in nosetests which causes setUpClass()
                # to be called even if the unittest class is skipped.
                # Here, we decorate setUpClass() as a patch to skip it
                # because of the missing modules too.
                # Upstream report: https://github.com/nose-devs/nose/issues/946
                obj.setUpClass = classmethod(skip_decorator(lambda cls: None))
            return skip_decorator(obj)
        else:
            return obj

    return test_requirement


class DisableSiteMixin(TestCaseBase):

    """Test cases not connected to a Site object.

    Do not use this for mock Site objects.

    Never set a class or instance variable called 'site'
    As it will prevent tests from executing when invoked as:
    $ nosetests -a '!site' -v
    """

    def setUp(self):
        """Set up test."""
        self.old_Site_lookup_method = pywikibot.Site
        pywikibot.Site = lambda *args: self.fail('%s: Site() not permitted'
                                                 % self.__class__.__name__)

        super(DisableSiteMixin, self).setUp()

    def tearDown(self):
        """Tear down test."""
        super(DisableSiteMixin, self).tearDown()

        pywikibot.Site = self.old_Site_lookup_method


class ForceCacheMixin(TestCaseBase):

    """Aggressively cached API test cases.

    Patches pywikibot.data.api to aggressively cache
    API responses.
    """

    def setUp(self):
        """Set up test."""
        patch_request()

        super(ForceCacheMixin, self).setUp()

    def tearDown(self):
        """Tear down test."""
        super(ForceCacheMixin, self).tearDown()

        unpatch_request()


class SiteNotPermitted(pywikibot.site.BaseSite):

    """Site interface to prevent sites being loaded."""

    def __init__(self, code, fam=None, user=None, sysop=None):
        """Constructor."""
        raise pywikibot.SiteDefinitionError(
            'Loading site %s:%s during dry test not permitted'
            % (fam, code))


class DisconnectedSiteMixin(TestCaseBase):

    """Test cases using a disconnected Site object.

    Do not use this for mock Site objects.

    Never set a class or instance variable called 'site'
    As it will prevent tests from executing when invoked as:
    $ nosetests -a '!site' -v
    """

    def setUp(self):
        """Set up test."""
        self.old_config_interface = config.site_interface
        # TODO: put a dummy subclass into config.site_interface
        #       as the default, to show a useful error message.
        config.site_interface = SiteNotPermitted

        pywikibot.data.api.Request = DryRequest
        self.old_convert = pywikibot.Claim.TARGET_CONVERTER['commonsMedia']
        pywikibot.Claim.TARGET_CONVERTER['commonsMedia'] = (
            lambda value, site: pywikibot.FilePage(
                pywikibot.Site('commons', 'commons', interface=DrySite),
                value))

        super(DisconnectedSiteMixin, self).setUp()

    def tearDown(self):
        """Tear down test."""
        super(DisconnectedSiteMixin, self).tearDown()

        config.site_interface = self.old_config_interface
        pywikibot.data.api.Request = _original_Request
        pywikibot.Claim.TARGET_CONVERTER['commonsMedia'] = self.old_convert


class CacheInfoMixin(TestCaseBase):

    """Report cache hits and misses."""

    def setUp(self):
        """Set up test."""
        super(CacheInfoMixin, self).setUp()
        self.cache_misses_start = tests.cache_misses
        self.cache_hits_start = tests.cache_hits

    def tearDown(self):
        """Tear down test."""
        self.cache_misses = tests.cache_misses - self.cache_misses_start
        self.cache_hits = tests.cache_hits - self.cache_hits_start

        if self.cache_misses:
            print(' %d cache misses' % self.cache_misses, end=' ')
        if self.cache_hits:
            print(' %d cache hits' % self.cache_hits, end=' ')

        if self.cache_misses or self.cache_hits:
            sys.stdout.flush()

        super(CacheInfoMixin, self).tearDown()


class CheckHostnameMixin(TestCaseBase):

    """Check the hostname is online before running tests."""

    _checked_hostnames = {}

    @classmethod
    def setUpClass(cls):
        """
        Set up the test class.

        Prevent tests running if the host is down.
        """
        super(CheckHostnameMixin, cls).setUpClass()

        if not hasattr(cls, 'sites'):
            return

        if issubclass(cls, HttpbinTestCase):
            # If test uses httpbin, then check is pytest test runner is used
            # and pytest_httpbin module is installed.
            httpbin_used = hasattr(sys, '_test_runner_pytest') and pytest_httpbin
        else:
            httpbin_used = False

        # If pytest_httpbin will be used during tests, then remove httpbin.org from sites.
        if httpbin_used:
            cls.sites = dict((k, v) for k, v in cls.sites.items()
                             if 'httpbin.org' not in v['hostname'])

        for key, data in cls.sites.items():
            if 'hostname' not in data:
                raise Exception('%s: hostname not defined for %s'
                                % (cls.__name__, key))
            hostname = data['hostname']

            if hostname in cls._checked_hostnames:
                if isinstance(cls._checked_hostnames[hostname], Exception):
                    raise unittest.SkipTest(
                        '%s: hostname %s failed (cached): %s'
                        % (cls.__name__, hostname,
                           cls._checked_hostnames[hostname]))
                elif cls._checked_hostnames[hostname] is False:
                    raise unittest.SkipTest('%s: hostname %s failed (cached)'
                                            % (cls.__name__, hostname))
                else:
                    continue

            e = None
            try:
                if '://' not in hostname:
                    hostname = 'http://' + hostname
                r = http.fetch(uri=hostname,
                               method='HEAD',
                               default_error_handling=False)
                if r.exception:
                    e = r.exception
                else:
                    if r.status not in [200, 301, 302, 303, 307, 308]:
                        raise ServerError('HTTP status: %d' % r.status)
            except Exception as e2:
                pywikibot.error('%s: accessing %s caused exception:'
                                % (cls.__name__, hostname))
                pywikibot.exception(e2, tb=True)
                e = e2
                pass

            if e:
                cls._checked_hostnames[hostname] = e
                raise unittest.SkipTest(
                    '%s: hostname %s failed: %s'
                    % (cls.__name__, hostname, e))

            cls._checked_hostnames[hostname] = True


class SiteWriteMixin(TestCaseBase):

    """
    Test cases involving writing to the server.

    When editing, the API should not be patched to use
    CachedRequest. This class prevents that.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up the test class.

        Reject write test classes configured with non-test wikis, or caching.

        Prevent test classes from writing to the site by default.

        If class attribute 'write' is -1, the test class is skipped unless
        environment variable PYWIKIBOT2_TEST_WRITE_FAIL is set to 1.

        Otherwise the test class is skipped unless environment variable
        PYWIKIBOT2_TEST_WRITE is set to 1.
        """
        if issubclass(cls, ForceCacheMixin):
            raise Exception(
                '%s can not be a subclass of both '
                'SiteWriteMixin and ForceCacheMixin'
                % cls.__name__)

        super(SiteWriteMixin, cls).setUpClass()

        site = cls.get_site()

        if cls.write == -1:
            env_var = 'PYWIKIBOT2_TEST_WRITE_FAIL'
        else:
            env_var = 'PYWIKIBOT2_TEST_WRITE'

        if os.environ.get(env_var, '0') != '1':
            raise unittest.SkipTest(
                '%r write tests disabled. '
                'Set %s=1 to enable.'
                % (cls.__name__, env_var))

        if (not hasattr(site.family, 'test_codes') or
                site.code not in site.family.test_codes):
            raise Exception(
                '%s should only be run on test sites. '
                'To run this test, add \'%s\' to the %s family '
                'attribute \'test_codes\'.'
                % (cls.__name__, site.code, site.family.name))


class RequireUserMixin(TestCaseBase):

    """Run tests against a specific site, with a login."""

    user = True

    @classmethod
    def require_site_user(cls, family, code, sysop=False):
        """Check the user config has a valid login to the site."""
        if not cls.has_site_user(family, code, sysop=sysop):
            raise unittest.SkipTest(
                '%s: No %susername for %s:%s'
                % (cls.__name__,
                   "sysop " if sysop else "",
                   family, code))

    @classmethod
    def setUpClass(cls):
        """
        Set up the test class.

        Skip the test class if the user config does not have
        a valid login to the site.
        """
        super(RequireUserMixin, cls).setUpClass()

        sysop = hasattr(cls, 'sysop') and cls.sysop

        for site in cls.sites.values():
            cls.require_site_user(site['family'], site['code'], sysop)

            if hasattr(cls, 'oauth') and cls.oauth:
                continue

            try:
                site['site'].login(sysop)
            except NoUsername:
                pass

            if not site['site'].user():
                raise unittest.SkipTest(
                    '%s: Not able to login to %s as %s'
                    % (cls.__name__,
                       'sysop' if sysop else 'bot',
                       site['site']))

    def setUp(self):
        """
        Set up the test case.

        Login to the site if it is not logged in.
        """
        super(RequireUserMixin, self).setUp()
        self._reset_login()

    def tearDown(self):
        """Log back into the site."""
        super(RequireUserMixin, self).tearDown()
        self._reset_login()

    def _reset_login(self):
        """Login to all sites."""
        sysop = hasattr(self, 'sysop') and self.sysop

        # There may be many sites, and setUp doesnt know
        # which site is to be tested; ensure they are all
        # logged in.
        for site in self.sites.values():
            site = site['site']

            if hasattr(self, 'oauth') and self.oauth:
                continue

            if not site.logged_in(sysop):
                site.login(sysop)
            assert(site.user())

    def get_userpage(self, site=None):
        """Create a User object for the user's userpage."""
        if not site:
            site = self.get_site()

        if hasattr(self, '_userpage'):
            # For multi-site test classes, or site is specified as a param,
            # the cached userpage object may not be the desired site.
            if self._userpage.site == site:
                return self._userpage

        sysop = hasattr(self, 'sysop') and self.sysop

        userpage = pywikibot.User(site, site.username(sysop))

        self._userpage = userpage

        return userpage


class MetaTestCaseClass(type):

    """Test meta class."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def wrap_method(key, sitedata, func):

            def wrapped_method(self):
                sitedata = self.sites[key]
                self.site_key = key
                self.family = sitedata['family']
                self.code = sitedata['code']
                self.site = sitedata['site']
                func(self, key)

            sitename = sitedata['family'] + ':' + sitedata['code']
            if func.__doc__:
                if func.__doc__.endswith('.'):
                    wrapped_method.__doc__ = func.__doc__[:-1]
                else:
                    wrapped_method.__doc__ = func.__doc__
                wrapped_method.__doc__ += ' on ' + sitename
            else:
                wrapped_method.__doc__ = 'Test ' + sitename

            return wrapped_method

        tests = [attr_name
                 for attr_name in dct
                 if attr_name.startswith('test')]

        base_tests = []
        if not tests:
            for base in bases:
                base_tests += [attr_name
                               for attr_name, attr in base.__dict__.items()
                               if attr_name.startswith('test') and callable(attr)]

        dct['abstract_class'] = not tests and not base_tests

        # Bail out if it is the abstract class.
        if dct['abstract_class']:
            return super(MetaTestCaseClass, cls).__new__(cls, name, bases, dct)

        # Inherit superclass attributes
        for base in bases:
            for key in ('pwb', 'net', 'site', 'user', 'sysop', 'write',
                        'sites', 'family', 'code', 'dry', 'hostname', 'oauth',
                        'hostnames', 'cached', 'cacheinfo', 'wikibase'):
                if hasattr(base, key) and key not in dct:
                    # print('%s has %s; copying to %s'
                    #       % (base.__name__, key, name))
                    dct[key] = getattr(base, key)

        # Will be inserted into dct[sites] later
        if 'hostname' in dct:
            hostnames = [dct['hostname']]
            del dct['hostname']
        elif 'hostnames' in dct:
            hostnames = dct['hostnames']
        else:
            hostnames = []

        if 'net' in dct and dct['net'] is False:
            dct['site'] = False

        if 'sites' in dct and 'site' not in dct:
            dct['site'] = True

        # If either are specified, assume both should be specified
        if 'family' in dct or 'code' in dct:
            dct['site'] = True

            if (('sites' not in dct or not len(dct['sites'])) and
                    'family' in dct and
                    'code' in dct and dct['code'] != '*'):
                # Add entry to self.sites
                dct['sites'] = {
                    str(dct['family'] + ':' + dct['code']): {
                        'code': dct['code'],
                        'family': dct['family'],
                    }
                }

        if hostnames:
            if 'sites' not in dct:
                dct['sites'] = {}
            for hostname in hostnames:
                assert hostname not in dct['sites']
                dct['sites'][hostname] = {'hostname': hostname}

        if 'dry' in dct and dct['dry'] is True:
            dct['net'] = False

        if (('sites' not in dct and 'site' not in dct) or
                ('site' in dct and not dct['site'])):
            # Prevent use of pywikibot.Site
            bases = cls.add_base(bases, DisableSiteMixin)

            # 'pwb' tests will _usually_ require a site. To ensure the
            # test class dependencies are declarative, this requires the
            # test writer explicitly sets 'site=False' so code reviewers
            # check that the script invoked by pwb will not load a site.
            if 'pwb' in dct and dct['pwb']:
                if 'site' not in dct:
                    raise Exception(
                        '%s: Test classes using pwb must set "site"; add '
                        'site=False if the test script will not use a site'
                        % name)

            # If the 'site' attribute is a false value,
            # remove it so it matches !site in nose.
            if 'site' in dct:
                del dct['site']

            # If there isn't a site, require declaration of net activity.
            if 'net' not in dct:
                raise Exception(
                    '%s: Test classes without a site configured must set "net"'
                    % name)

            # If the 'net' attribute is a false value,
            # remove it so it matches !net in nose.
            if not dct['net']:
                del dct['net']

            return super(MetaTestCaseClass, cls).__new__(cls, name, bases, dct)

        # The following section is only processed if the test uses sites.

        if 'dry' in dct and dct['dry']:
            bases = cls.add_base(bases, DisconnectedSiteMixin)
            del dct['net']
        else:
            dct['net'] = True

        if 'cacheinfo' in dct and dct['cacheinfo']:
            bases = cls.add_base(bases, CacheInfoMixin)

        if 'cached' in dct and dct['cached']:
            bases = cls.add_base(bases, ForceCacheMixin)

        if 'net' in dct and dct['net']:
            bases = cls.add_base(bases, CheckHostnameMixin)
        else:
            assert not hostnames, 'net must be True with hostnames defined'

        if 'write' in dct and dct['write']:
            if 'user' not in dct:
                dct['user'] = True
            bases = cls.add_base(bases, SiteWriteMixin)

        if ('user' in dct and dct['user']) or ('sysop' in dct and dct['sysop']):
            bases = cls.add_base(bases, RequireUserMixin)

        for test in tests:
            test_func = dct[test]

            # method decorated with unittest.expectedFailure has no arguments
            # so it is assumed to not be a multi-site test method.
            if test_func.__code__.co_argcount == 0:
                continue

            # a normal test method only accepts 'self'
            if test_func.__code__.co_argcount == 1:
                continue

            # a multi-site test method only accepts 'self' and the site-key
            if test_func.__code__.co_argcount != 2:
                raise Exception(
                    '%s: Test method %s must accept either 1 or 2 arguments; '
                    ' %d found'
                    % (name, test, test_func.__code__.co_argcount))

            # create test methods processed by unittest
            for (key, sitedata) in dct['sites'].items():
                test_name = test + '_' + key.replace('-', '_')
                cls.add_method(dct, test_name,
                               wrap_method(key, sitedata, dct[test]))

                if key in dct.get('expected_failures', []):
                    dct[test_name] = unittest.expectedFailure(dct[test_name])

            del dct[test]

        return super(MetaTestCaseClass, cls).__new__(cls, name, bases, dct)

    @staticmethod
    def add_base(bases, subclass):
        """Return a tuple of bases with the subclasses added if not already."""
        if not any(issubclass(base, subclass) for base in bases):
            bases = (subclass, ) + bases
        return bases

    @staticmethod
    def add_method(dct, test_name, method, doc=None, doc_suffix=None):
        """Add a method to a dictionary and set its name and documention."""
        dct[test_name] = method
        # it's explicitly using str() because __name__ must be str
        dct[test_name].__name__ = str(test_name)
        if doc_suffix:
            if not doc:
                doc = method.__doc__
            assert doc[-1] == '.'
            doc = doc[:-1] + ' ' + doc_suffix + '.'

        if doc:
            dct[test_name].__doc__ = doc


@add_metaclass
class TestCase(TestTimerMixin, TestCaseBase):

    """Run tests on pre-defined sites."""

    __metaclass__ = MetaTestCaseClass

    @classmethod
    def setUpClass(cls):
        """
        Set up the test class.

        Prefetch the Site object for each of the sites the test
        class has declared are needed.
        """
        super(TestCase, cls).setUpClass()

        if not hasattr(cls, 'sites'):
            return

        # This stores the site under the site name.
        if not cls.sites:
            cls.sites = {}

        # If the test is not cached, create new Site objects for this class
        cm = cls._uncached()
        cm.__enter__()

        interface = None  # defaults to 'APISite'
        dry = hasattr(cls, 'dry') and cls.dry
        if dry:
            interface = DrySite

        for data in cls.sites.values():
            if ('code' in data and data['code'] in ('test', 'mediawiki') and
                    'PYWIKIBOT2_TEST_PROD_ONLY' in os.environ and not dry):
                raise unittest.SkipTest(
                    'Site code "%s" and PYWIKIBOT2_TEST_PROD_ONLY is set.'
                    % data['code'])

            if 'site' not in data and 'code' in data and 'family' in data:
                data['site'] = Site(data['code'], data['family'],
                                    interface=interface)
            if 'hostname' not in data and 'site' in data:
                try:
                    data['hostname'] = data['site'].base_url(data['site'].path())
                except KeyError:
                    # The family has defined this as obsolete
                    # without a mapping to a hostname.
                    pass

        cm.__exit__(None, None, None)

        if len(cls.sites) == 1:
            key = next(iter(cls.sites.keys()))
            if 'site' in cls.sites[key]:
                cls.site = cls.sites[key]['site']

    @classmethod
    @contextmanager
    def _uncached(cls):
        if not hasattr(cls, 'cached') or not cls.cached:
            orig_sites = pywikibot._sites
            pywikibot._sites = {}
        yield
        if not hasattr(cls, 'cached') or not cls.cached:
            pywikibot._sites = orig_sites

    @classmethod
    def get_site(cls, name=None):
        """Return the prefetched Site object."""
        if not name and hasattr(cls, 'sites'):
            if len(cls.sites) == 1:
                name = next(iter(cls.sites.keys()))
            else:
                raise Exception(
                    '"%s.get_site(name=None)" called with multiple sites'
                    % cls.__name__)

        if name and name not in cls.sites:
            raise Exception('"%s" not declared in %s'
                            % (name, cls.__name__))

        if isinstance(cls.site, BaseSite):
            assert cls.sites[name]['site'] == cls.site
            return cls.site

        return cls.sites[name]['site']

    @classmethod
    def has_site_user(cls, family, code, sysop=False):
        """Check the user config has a user for the site."""
        if not family:
            raise Exception('no family defined for %s' % cls.__name__)
        if not code:
            raise Exception('no site code defined for %s' % cls.__name__)

        usernames = config.sysopnames if sysop else config.usernames

        return code in usernames[family] or '*' in usernames[family]

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(TestCase, self).__init__(*args, **kwargs)

        if not hasattr(self, 'sites'):
            return

        # Create an instance method named the same as the class method
        self.get_site = lambda name=None: self.__class__.get_site(name)

    def get_mainpage(self, site=None, force=False):
        """Create a Page object for the sites main page.

        @param site: Override current site, obtained using L{get_site}.
        @type site: APISite or None
        @param force: Get an unused Page object
        @type force: bool
        @rtype: Page
        """
        if not site:
            site = self.get_site()

        if hasattr(self, '_mainpage') and not force:
            # For multi-site test classes, or site is specified as a param,
            # the cached mainpage object may not be the desired site.
            if self._mainpage.site == site:
                return self._mainpage

        mainpage = pywikibot.Page(site, site.siteinfo['mainpage'])
        if not isinstance(site, DrySite) and mainpage.isRedirectPage():
            mainpage = mainpage.getRedirectTarget()

        if force:
            mainpage = pywikibot.Page(self.site, mainpage.title())

        self._mainpage = mainpage

        return mainpage

    def get_missing_article(self, site=None):
        """Get a Page which refers to a missing page on the site."""
        if not site:
            site = self.get_site()
        page = pywikibot.Page(pywikibot.page.Link(
                              "There is no page with this title", site))
        if page.exists():
            raise unittest.SkipTest("Did not find a page that does not exist.")

        return page


class CapturingTestCase(TestCase):

    """
    Capture assertion calls to do additional calls around them.

    All assertions done which start with "assert" are patched in such a way that
    after the assertion it calls C{process_assertion} with the assertion and the
    arguments.

    To avoid that it patches the assertion it's possible to put the call in an
    C{disable_assert_capture} with-statement.

    """

    # Is True while an assertion is running, so that assertions won't be patched
    # when they are executed while an assertion is running and only the outer
    # most assertion gets actually patched.
    _patched = False

    @contextmanager
    def disable_assert_capture(self):
        """A context manager which preventing that asssertions are patched."""
        nested = self._patched  # Don't reset if it was set before
        self._patched = True
        yield
        if not nested:
            self._patched = False

    @contextmanager
    def _delay_assertion(self, context, assertion, args, kwargs):
        with self.disable_assert_capture():
            with context as ctx:
                yield ctx
            self.after_assert(assertion, *args, **kwargs)

    def process_assert(self, assertion, *args, **kwargs):
        """Handle the assertion call."""
        return assertion(*args, **kwargs)

    def after_assert(self, assertion, *args, **kwargs):
        """Handle after the assertion."""
        pass

    def patch_assert(self, assertion):
        """Execute process_assert when the assertion is called."""
        def inner_assert(*args, **kwargs):
            assert self._patched is False
            self._patched = True
            try:
                context = self.process_assert(assertion, *args, **kwargs)
                if hasattr(context, '__enter__'):
                    return self._delay_assertion(context, assertion, args, kwargs)
                else:
                    self.after_assert(assertion, *args, **kwargs)
                    return context
            finally:
                self._patched = False
        return inner_assert

    def __getattribute__(self, attr):
        """Patch assertions if enabled."""
        result = super(CapturingTestCase, self).__getattribute__(attr)
        if attr.startswith('assert') and not self._patched:
            return self.patch_assert(result)
        else:
            return result


class PatchingTestCase(TestCase):

    """Easily patch and unpatch instances."""

    @staticmethod
    def patched(obj, attr_name):
        """Apply patching information."""
        def add_patch(decorated):
            decorated._patching = (obj, attr_name)
            return decorated
        return add_patch

    def patch(self, obj, attr_name, replacement):
        """
        Patch the obj's attribute with the replacement.

        It will be reset after each C{tearDown}.
        """
        self._patched_instances += [(obj, attr_name, getattr(obj, attr_name))]
        setattr(obj, attr_name, replacement)

    def setUp(self):
        """Set up the test by initializing the patched list."""
        super(TestCaseBase, self).setUp()
        self._patched_instances = []
        for attribute in dir(self):
            attribute = getattr(self, attribute)
            if callable(attribute) and hasattr(attribute, '_patching'):
                self.patch(attribute._patching[0], attribute._patching[1],
                           attribute)

    def tearDown(self):
        """Tear down the test by unpatching the patched."""
        for patched in self._patched_instances:
            setattr(*patched)
        super(TestCaseBase, self).tearDown()


class SiteAttributeTestCase(TestCase):

    """Add the sites as attributes to the instances."""

    @classmethod
    def setUpClass(cls):
        """Add each initialized site as an attribute to cls."""
        super(SiteAttributeTestCase, cls).setUpClass()
        for site in cls.sites:
            if 'site' in cls.sites[site]:
                setattr(cls, site, cls.sites[site]['site'])


class DefaultSiteTestCase(TestCase):

    """Run tests against the config specified site."""

    family = config.family
    code = config.mylang

    @classmethod
    def override_default_site(cls, site):
        """
        Override the default site.

        @param site: site tests should use
        @type site: BaseSite
        """
        print('%s using %s instead of %s:%s.'
              % (cls.__name__, site, cls.family, cls.code))
        cls.site = site
        cls.family = site.family.name
        cls.code = site.code

        cls.sites = {
            cls.site: {
                'family': cls.family,
                'code': cls.code,
                'site': cls.site,
                'hostname': cls.site.hostname(),
            }
        }


class AlteredDefaultSiteTestCase(TestCase):

    """Save and restore the config.mylang and config.family."""

    def setUp(self):
        """Prepare the environment for running main() in a script."""
        self.original_family = pywikibot.config.family
        self.original_code = pywikibot.config.mylang
        super(AlteredDefaultSiteTestCase, self).setUp()

    def tearDown(self):
        """Restore the environment."""
        pywikibot.config.family = self.original_family
        pywikibot.config.mylang = self.original_code
        super(AlteredDefaultSiteTestCase, self).tearDown()


class ScenarioDefinedDefaultSiteTestCase(AlteredDefaultSiteTestCase):

    """Tests that depend on the default site being set to the test site."""

    def setUp(self):
        """Prepare the environment for running main() in a script."""
        super(ScenarioDefinedDefaultSiteTestCase, self).setUp()
        site = self.get_site()
        pywikibot.config.family = site.family
        pywikibot.config.mylang = site.code


class DefaultDrySiteTestCase(DefaultSiteTestCase):

    """Run tests using the config specified site in offline mode."""

    dry = True


class WikimediaSiteTestCase(TestCase):

    """Test class uses only WMF sites."""

    wmf = True


class WikimediaDefaultSiteTestCase(DefaultSiteTestCase, WikimediaSiteTestCase):

    """Test class to run against a WMF site, preferring the default site."""

    @classmethod
    def setUpClass(cls):
        """
        Set up the test class.

        Check that the default site is a Wikimedia site.
        Use en.wikipedia.org as a fallback.
        """
        super(WikimediaDefaultSiteTestCase, cls).setUpClass()

        assert hasattr(cls, 'site') and hasattr(cls, 'sites')

        assert len(cls.sites) == 1

        site = cls.get_site()

        if not isinstance(site.family, WikimediaFamily):
            cls.override_default_site(pywikibot.Site('en', 'wikipedia'))


class WikibaseTestCase(TestCase):

    """Run tests against a wikibase site."""

    wikibase = True

    @classmethod
    def setUpClass(cls):
        """
        Set up the test class.

        Checks that all sites are configured with a Wikibase repository,
        with Site.has_data_repository() returning True, and all sites
        use the same data repository.
        """
        super(WikibaseTestCase, cls).setUpClass()

        with cls._uncached():
            for data in cls.sites.values():
                if 'site' not in data:
                    continue

                site = data['site']
                if not site.has_data_repository:
                    raise unittest.SkipTest(
                        u'%s: %r does not have data repository'
                        % (cls.__name__, site))

                if (hasattr(cls, 'repo') and
                        cls.repo != site.data_repository()):
                    raise Exception(
                        '%s: sites do not all have the same data repository'
                        % cls.__name__)

                cls.repo = site.data_repository()

    @classmethod
    def get_repo(cls):
        """Return the prefetched DataSite object."""
        return cls.repo

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(WikibaseTestCase, self).__init__(*args, **kwargs)

        if not hasattr(self, 'sites'):
            return

        # Create an instance method named the same as the class method
        self.get_repo = lambda: self.repo


class WikibaseClientTestCase(WikibaseTestCase):

    """Run tests against a specific site connected to a wikibase."""

    @classmethod
    def setUpClass(cls):
        """
        Set up the test class.

        Checks that all sites are configured as a Wikibase client,
        with Site.has_data_repository returning True.
        """
        super(WikibaseClientTestCase, cls).setUpClass()

        for site in cls.sites.values():
            if not site['site'].has_data_repository:
                raise unittest.SkipTest(
                    '%s: %r does not have data repository'
                    % (cls.__name__, site['site']))


class DefaultWikibaseClientTestCase(WikibaseClientTestCase,
                                    DefaultSiteTestCase):

    """Run tests against any site connected to a Wikibase."""

    pass


class WikidataTestCase(WikibaseTestCase):

    """Test cases use Wikidata."""

    family = 'wikidata'
    code = 'wikidata'

    cached = True


class DefaultWikidataClientTestCase(DefaultWikibaseClientTestCase):

    """Run tests against any site connected to Wikidata."""

    @classmethod
    def setUpClass(cls):
        """
        Set up the test class.

        Require the data repository is wikidata.org.
        """
        super(WikibaseClientTestCase, cls).setUpClass()

        if str(cls.get_repo()) != 'wikidata:wikidata':
            raise unittest.SkipTest(
                u'%s: %s is not connected to Wikidata.'
                % (cls.__name__, cls.get_site()))


class ScriptMainTestCase(ScenarioDefinedDefaultSiteTestCase):

    """Test running a script main()."""

    pass


class PwbTestCase(TestCase):

    """
    Test cases use pwb.py to invoke scripts.

    Test cases which use pwb typically also access a site, and use the network.
    Even during initialisation, scripts may call pywikibot.handle_args, which
    initialises loggers and uses the network to determine if the code is stale.

    The flag 'pwb' is used by the TestCase metaclass to check that a test site
    is set declared in the class properties, or that 'site = False' is added
    to the class properties in the unlikely scenario that the test case
    uses pwb in a way that doesnt use a site.

    If a test class is marked as 'site = False', the metaclass will also check
    that the 'net' flag is explicitly set.
    """

    pwb = True

    def setUp(self):
        """Prepare the environment for running the pwb.py script."""
        super(PwbTestCase, self).setUp()
        self.orig_pywikibot_dir = None
        if 'PYWIKIBOT2_DIR' in os.environ:
            self.orig_pywikibot_dir = os.environ['PYWIKIBOT2_DIR']
        base_dir = pywikibot.config.base_dir
        if OSWIN32 and PY2:
            base_dir = str(base_dir)
        os.environ[str('PYWIKIBOT2_DIR')] = base_dir

    def tearDown(self):
        """Restore the environment after running the pwb.py script."""
        super(PwbTestCase, self).tearDown()
        del os.environ['PYWIKIBOT2_DIR']
        if self.orig_pywikibot_dir:
            os.environ[str('PYWIKIBOT2_DIR')] = self.orig_pywikibot_dir

    def _execute(self, args, data_in=None, timeout=0, error=None):
        site = self.get_site()

        args = args + ['-family:' + site.family.name,
                       '-code:' + site.code]

        return execute_pwb(args, data_in, timeout, error)


class RecentChangesTestCase(WikimediaDefaultSiteTestCase):

    """Test cases for tests that use recent change."""

    # site.recentchanges() includes external edits from wikidata,
    # except on wiktionaries which are not linked to wikidata
    # so total=3 should not be too high for most sites.
    length = 3

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        if os.environ.get('PYWIKIBOT2_TEST_NO_RC', '0') == '1':
            raise unittest.SkipTest('RecentChanges tests disabled.')

        super(RecentChangesTestCase, cls).setUpClass()

        if cls.get_site().code == 'test':
            cls.override_default_site(pywikibot.Site('en', 'wikipedia'))


class DebugOnlyTestCase(TestCase):

    """Test cases that only operate in debug mode."""

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        if not __debug__:
            raise unittest.SkipTest(
                '%s is disabled when __debug__ is disabled.' % cls.__name__)
        super(DebugOnlyTestCase, cls).setUpClass()


class DeprecationTestCase(DebugOnlyTestCase, TestCase):

    """Test cases for deprecation function in the tools module."""

    _generic_match = re.compile(r'.* is deprecated(; use .* instead)?\.')

    skip_list = [
        unittest.case._AssertRaisesContext,
        TestCase.assertRaises,
        TestCase.assertRaisesRegex,
        TestCase.assertRaisesRegexp,
    ]

    # Require no instead string
    NO_INSTEAD = object()
    # Require an instead string
    INSTEAD = object()

    # Python 3 component in the call stack of _AssertRaisesContext
    if hasattr(unittest.case, '_AssertRaisesBaseContext'):
        skip_list.append(unittest.case._AssertRaisesBaseContext)

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(DeprecationTestCase, self).__init__(*args, **kwargs)
        self.warning_log = []

        self.expect_warning_filename = inspect.getfile(self.__class__)
        if self.expect_warning_filename.endswith((".pyc", ".pyo")):
            self.expect_warning_filename = self.expect_warning_filename[:-1]

        self._do_test_warning_filename = True
        self._ignore_unknown_warning_packages = False

        self.context_manager = WarningSourceSkipContextManager(self.skip_list)

    def _reset_messages(self):
        """Reset captured deprecation warnings."""
        self._do_test_warning_filename = True
        del self.warning_log[:]

    @property
    def deprecation_messages(self):
        """Return captured deprecation warnings."""
        messages = [str(item.message) for item in self.warning_log]
        return messages

    @classmethod
    def _build_message(cls, deprecated, instead):
        if deprecated is None:
            if instead is None:
                msg = None
            elif instead is True:
                msg = cls.INSTEAD
            else:
                assert instead is False
                msg = cls.NO_INSTEAD
        else:
            msg = '{0} is deprecated'.format(deprecated)
            if instead:
                msg += '; use {0} instead'.format(instead)
            msg += '.'
        return msg

    def assertDeprecationParts(self, deprecated=None, instead=None):
        """
        Assert that a deprecation warning happened.

        To simplify deprecation tests it just requires the to separated parts
        and forwards the result to L{assertDeprecation}.

        @param deprecated: The deprecated string. If None it uses a generic
            match depending on instead.
        @type deprecated: str or None
        @param instead: The instead string unless deprecated is None. If it's
            None it allows any generic deprecation string, on True only those
            where instead string is present and on False only those where it's
            missing. If the deprecation string is not None, no instead string
            is expected when instead evaluates to False.
        @type instead: str or None or True or False
        """
        self.assertDeprecation(self._build_message(deprecated, instead))

    def assertDeprecation(self, msg=None):
        """
        Assert that a deprecation warning happened.

        @param msg: Either the specific message or None to allow any generic
            message. When set to C{INSTEAD} it only counts those supplying an
            alternative and when C{NO_INSTEAD} only those not supplying one.
        @type msg: string or None or INSTEAD or NO_INSTEAD
        """
        if msg is None or msg is self.INSTEAD or msg is self.NO_INSTEAD:
            deprecation_messages = self.deprecation_messages
            for deprecation_message in deprecation_messages:
                match = self._generic_match.match(deprecation_message)
                if (match and bool(match.group(1)) == (msg is self.INSTEAD) or
                        msg is None):
                    break
            else:
                self.fail('No generic deprecation message match found in '
                          '{0}'.format(deprecation_messages))
        else:
            self.assertIn(msg, self.deprecation_messages)
        if self._do_test_warning_filename:
            self.assertDeprecationFile(self.expect_warning_filename)

    def assertOneDeprecationParts(self, deprecated=None, instead=None, count=1):
        """
        Assert that exactly one deprecation message happened and reset.

        It uses the same arguments as L{assertDeprecationParts}.
        """
        self.assertOneDeprecation(self._build_message(deprecated, instead),
                                  count)

    def assertOneDeprecation(self, msg=None, count=1):
        """Assert that exactly one deprecation message happened and reset."""
        self.assertDeprecation(msg)
        # This is doing such a weird structure, so that it shows any other
        # deprecation message from the set.
        self.assertCountEqual(set(self.deprecation_messages),
                              [self.deprecation_messages[0]])
        self.assertEqual(len(self.deprecation_messages), count)
        self._reset_messages()

    def assertNoDeprecation(self, msg=None):
        """Assert that no deprecation warning happened."""
        if msg:
            self.assertNotIn(msg, self.deprecation_messages)
        else:
            self.assertEqual([], self.deprecation_messages)

    def assertDeprecationClass(self, cls):
        """Assert that all deprecation warning are of one class."""
        self.assertTrue(all(isinstance(item.message, cls)
                            for item in self.warning_log))

    def assertDeprecationFile(self, filename):
        """Assert that all deprecation warning are of one filename."""
        for item in self.warning_log:
            if (self._ignore_unknown_warning_packages and
                    'pywikibot' not in item.filename):
                continue

            if item.filename != filename:
                self.fail(
                    'expected warning filename %s; warning item: %s'
                    % (filename, item))

    def setUp(self):
        """Set up unit test."""
        super(DeprecationTestCase, self).setUp()

        self.warning_log = self.context_manager.__enter__()
        warnings.simplefilter("always")

        self._reset_messages()

    def tearDown(self):
        """Tear down unit test."""
        self.context_manager.__exit__()

        super(DeprecationTestCase, self).tearDown()


class AutoDeprecationTestCase(CapturingTestCase, DeprecationTestCase):

    """
    A test case capturing asserts and asserting a deprecation afterwards.

    For example C{assertEqual} will do first C{assertEqual} and then
    C{assertOneDeprecation}.
    """

    def after_assert(self, assertion, *args, **kwargs):
        """Handle assertion and call C{assertOneDeprecation} after it."""
        super(AutoDeprecationTestCase, self).after_assert(
            assertion, *args, **kwargs)
        self.assertOneDeprecation()

    skip_list = DeprecationTestCase.skip_list + [
        CapturingTestCase.process_assert,
        CapturingTestCase.patch_assert,
    ]


@optional_pytest_httpbin_cls_decorator
class HttpbinTestCase(TestCase):

    """
    Custom test case class, which allows doing dry httpbin tests using pytest-httpbin.

    Test cases, which use httpbin, need to inherit this class.
    """

    sites = {
        'httpbin': {
            'hostname': 'httpbin.org',
        },
    }

    def get_httpbin_url(self, path=''):
        """
        Return url of httpbin.

        If pytest is used, returns url of local httpbin server.
        Otherwise, returns: http://httpbin.org
        """
        if hasattr(self, 'httpbin'):
            return self.httpbin.url + path
        else:
            return 'http://httpbin.org' + path

    def get_httpbin_hostname(self):
        """
        Return httpbin hostname.

        If pytest is used, returns hostname of local httpbin server.
        Otherwise, returns: httpbin.org
        """
        if hasattr(self, 'httpbin'):
            return '{0}:{1}'.format(self.httpbin.host, self.httpbin.port)
        else:
            return 'httpbin.org'
