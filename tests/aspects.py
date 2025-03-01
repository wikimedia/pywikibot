"""Test aspects to allow fine grained control over what tests are executed.

Several parts of the test infrastructure are implemented as mixins,
such as API result caching and excessive test durations.
"""
#
# (C) Pywikibot team, 2014-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import inspect
import os
import re
import sys
import time
import unittest
import warnings
from collections.abc import Sized
from contextlib import contextmanager, suppress
from functools import wraps
from http import HTTPStatus
from typing import Any
from unittest.util import safe_repr

import pywikibot
from pywikibot import Site, config
from pywikibot.backports import Iterable, Iterator, removeprefix, removesuffix
from pywikibot.comms import http
from pywikibot.data.api import Request as _original_Request
from pywikibot.exceptions import (
    NoUsernameError,
    ServerError,
    SiteDefinitionError,
)
from pywikibot.family import WikimediaFamily
from pywikibot.site import BaseSite
from pywikibot.tools import (  # noqa: F401 (used by eval())
    MediaWikiVersion,
    suppress_warnings,
)
from tests import (
    WARN_SITE_CODE,
    patch_request,
    unittest_print,
    unpatch_request,
)
from tests.utils import (
    AssertAPIErrorContextManager,
    DryRequest,
    DrySite,
    WarningSourceSkipContextManager,
    execute_pwb,
    skipping,
)


OSWIN32 = (sys.platform == 'win32')
pywikibot.bot.set_interface('buffer')


class TestTimerMixin(unittest.TestCase):

    """Time each test and report excessive durations."""

    # Number of seconds each test may consume
    # before a note is added after the test.
    test_duration_warning_interval = 10

    def setUp(self):
        """Set up test."""
        self.test_start = time.time()
        super().setUp()

    def tearDown(self):
        """Tear down test."""
        super().tearDown()
        self.test_completed = time.time()
        duration = self.test_completed - self.test_start
        if duration > self.test_duration_warning_interval:
            unittest_print(f' {duration:.3f}s', end=' ')
            sys.stdout.flush()


class TestCaseBase(TestTimerMixin):

    """Base class for all tests."""

    def assertIsEmpty(self, seq, msg=None):
        """Check that the sequence is empty."""
        self.assertIsInstance(
            seq, Sized, 'seq argument is not a Sized class containing __len__')
        if seq:
            msg = self._formatMessage(msg, f'{safe_repr(seq)} is not empty')
            self.fail(msg)

    def assertIsNotEmpty(self, seq, msg=None):
        """Check that the sequence is not empty."""
        self.assertIsInstance(
            seq, Sized, 'seq argument is not a Sized class containing __len__')
        if not seq:
            msg = self._formatMessage(msg, f'{safe_repr(seq)} is empty')
            self.fail(msg)

    def assertLength(self, seq, other, msg=None):
        """Verify that a sequence seq has the length of other."""
        # the other parameter may be given as a sequence too
        self.assertIsInstance(
            seq, Sized, 'seq argument is not a Sized class containing __len__')
        first_len = len(seq)
        try:
            second_len = len(other)
        except TypeError:
            second_len = other

        if first_len != second_len:
            msg = self._formatMessage(
                msg, f'len({safe_repr(seq)}): {first_len} != {second_len}')
            self.fail(msg)

    def assertPageInNamespaces(self, page, namespaces: int | set[int]) -> None:
        """Assert that Pages is in namespaces.

        :param page: Page
        :type page: pywikibot.BasePage
        :param namespaces: expected namespaces
        """
        if isinstance(namespaces, int):
            namespaces = {namespaces}

        self.assertIn(page.namespace(), namespaces,
                      f'{page} not in namespace {namespaces!r}')

    def _get_gen_pages(self,
                       gen: Iterable[pywikibot.Page],
                       site: pywikibot.site.APISite = None) -> None:
        """Get pages from gen, asserting they are Page from site.

        .. versionchanged:: 9.3
           the *count* parameter was dropped; all pages from *gen* are
           tested.

        :param gen: Page generator
        :param site: Site of expected pages
        :meta public:
        """
        gen_pages = list(gen)

        for page in gen_pages:
            self.assertIsInstance(page, pywikibot.Page)
            if site:
                self.assertEqual(page.site, site)

        return gen_pages

    def _get_gen_titles(self, gen, site=None) -> list[str]:
        """Return a list of page titles of given iterable."""
        return [page.title() for page in self._get_gen_pages(gen, site)]

    @staticmethod
    def _get_canonical_titles(titles, site=None):
        if site:
            titles = [pywikibot.Link(title, site).canonical_title()
                      for title in titles]
        elif not isinstance(titles, list):
            titles = list(titles)
        return titles

    def assertPagesInNamespaces(self, gen, namespaces: int | set[int]) -> None:
        """Assert that generator returns Pages all in namespaces.

        :param gen: generator to iterate
        :type gen: generator
        :param namespaces: expected namespaces
        """
        for page in gen:
            self.assertPageInNamespaces(page, namespaces)

    def assertPagesInNamespacesAll(self, gen,
                                   namespaces: int | set[int],
                                   skip: bool = False) -> None:
        """Try to confirm that generator returns Pages for all namespaces.

        .. versionchanged:: 9.3
           raises TypeError instead of AssertionError

        :param gen: generator to iterate
        :type gen: generator
        :param namespaces: expected namespaces
        :param skip: skip test if not all namespaces found
        :raises TypeError: Invalid *namespaces* type
        """
        if isinstance(namespaces, int):
            namespaces = {namespaces}  # pragma: no cover
        elif not isinstance(namespaces, set):  # pragma: no cover
            raise TypeError('namespaces argument must be an int or a set, not '
                            f'{type(namespaces).__name__}')

        page_namespaces = {page.namespace() for page in gen}

        if skip and page_namespaces < namespaces:
            raise unittest.SkipTest(
                f'No pages in namespaces {list(namespaces - page_namespaces)}'
                ' found.')

        self.assertEqual(page_namespaces, namespaces)

    def assertPageTitlesEqual(
        self,
        gen: Iterable[pywikibot.Page],
        titles: Iterator[str],
        site: pywikibot.site.APISite | None = None
    ) -> None:
        """Test that pages in gen match expected titles.

        :param gen: Page generator
        :param titles: Expected titles
        :param site: Site of expected pages
        """
        titles = self._get_canonical_titles(titles, site)
        gen_titles = self._get_gen_titles(gen, site)
        self.assertEqual(gen_titles, titles)

    def assertPageTitlesCountEqual(
        self,
        gen: Iterable[pywikibot.Page],
        titles: Iterator[str],
        site: pywikibot.site.APISite | None = None
    ) -> None:
        """Test that pages in gen match expected titles, regardless of order.

        :param gen: Page generator
        :param titles: Expected titles
        :param site: Site of expected pages
        """
        titles = self._get_canonical_titles(titles, site)
        gen_titles = self._get_gen_titles(gen, site)
        self.assertCountEqual(gen_titles, titles)

    def assertAPIError(self, code, info=None, callable_obj=None, *args,
                       regex=None, **kwargs):
        """Assert that a specific APIError wrapped around :exc:`assertRaises`.

        If no callable object is defined and it returns a context manager, that
        context manager will return the underlying context manager used by
        :py:obj:`assertRaises`. So it's possible to access the APIError by
        using it's ``exception`` attribute.

        :param code: The code of the error which must have happened.
        :type code: str
        :param info: The info string of the error or None if no it shouldn't be
            checked.
        :type info: str or None
        :param callable_obj: The object that will be tested. If None it returns
            a context manager like :py:obj:`assertRaises`.
        :type callable_obj: callable
        :param args: The positional arguments forwarded to the callable object.
        :param kwargs: The keyword arguments forwarded to the callable object.
        :return: Context manager if callable_obj is None and None otherwise.
        :rtype: None or context manager
        """
        msg = kwargs.pop('msg', None)
        return AssertAPIErrorContextManager(
            code, info, msg, self, regex).handle(callable_obj, args, kwargs)


def require_modules(*required_modules):
    """Require that the given list of modules can be imported."""
    def test_requirement(obj):
        """Test the requirement and return an optionally decorated object."""
        missing = []
        for required_module in required_modules:
            try:
                __import__(required_module, globals(), locals(), [], 0)
            except ModuleNotFoundError:  # pragma: no cover
                missing += [required_module]
        if not missing:
            return obj
        skip_decorator = unittest.skip(  # pragma: no cover
            f"{', '.join(missing)} not installed")
        return skip_decorator(obj)  # pragma: no cover

    return test_requirement


def require_version(version_needed: str, /, reason: str = ''):
    """Require minimum MediaWiki version to be queried.

    The version needed for the test; must be given with a preleading rich
    comparisons operator like ``<1.31wmf4`` or ``>=1.43``. If the
    comparison does not match the test will be skipped.

    This decorator can only be used for TestCase having a single site.
    It cannot be used for DrySite tests. In addition version comparison
    for other than the current site e.g. for the related data or image
    repositoy of the current site is ot possible.

    .. versionadded:: 8.0

    .. versionchanged:: 10.0
       TypeError and ValueError are used for validation fails.
       *version_needed* parameter is positional only.

    :param version_needed: The version needed
    :param reason: A reason for skipping the test.
    :raises TypeError: self.site is not a BaseSite or the decorated
        method has parameters.
    :raises ValueError: The given *version_needed* parameter is invalid
        or an operand is given on the left or the version number is
        invalid
    """
    def test_requirement(method):
        """Test the requirement and return an optionally decorated object."""
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            """Validate environment."""
            if not isinstance(self.site, BaseSite) \
               or isinstance(self.site, DrySite):
                raise TypeError(
                    f'{type(self).__name__}.site must be a BaseSite not '
                    f'{type(self.site).__name__}.')

            if args or kwargs:
                raise TypeError(
                    f'Test method {method.__name__!r} has parameters which is '
                    f'not supported with require_version decorator.'
                )

            try:
                site_vers, op, version = re.split('([<>]=?)', version_needed)
            except ValueError:
                raise ValueError(f'There is no valid operator given with '
                                 f'version {version_needed!r}')

            if site_vers:
                raise ValueError(
                    f'first operand {site_vers} should not be set')

            skip = not eval(
                f'self.site.mw_version {op} MediaWikiVersion(version)')

            if not skip:
                return method(self)

            myreason = ' to ' + reason if reason else ''
            raise unittest.SkipTest(
                f'MediaWiki {op} v{version} required{myreason}.')

        return wrapper

    return test_requirement


class DisableSiteMixin(TestCaseBase):

    """Test cases not connected to a Site object.

    Do not use this for mock Site objects.

    Never set a class or instance variable called 'site'
    As it will prevent tests from executing when invoked as:
    $ pytest -a 'not site'
    """

    def setUp(self):
        """Set up test."""
        self.old_Site_lookup_method = pywikibot.Site
        pywikibot.Site = lambda *args: self.fail(
            f'{self.__class__.__name__}: Site() not permitted')

        super().setUp()

    def tearDown(self):
        """Tear down test."""
        super().tearDown()

        pywikibot.Site = self.old_Site_lookup_method


class ForceCacheMixin(TestCaseBase):

    """Aggressively cached API test cases.

    Patches pywikibot.data.api to aggressively cache
    API responses.
    """

    def setUp(self):
        """Set up test."""
        patch_request()
        super().setUp()

    def tearDown(self):
        """Tear down test."""
        super().tearDown()
        unpatch_request()


class SiteNotPermitted(pywikibot.site.BaseSite):

    """Site interface to prevent sites being loaded."""

    def __init__(self, code, fam=None, user=None):
        """Initializer."""
        raise SiteDefinitionError(  # pragma: no cover
            f'Loading site {fam}:{code} during dry test not permitted')


class DisconnectedSiteMixin(TestCaseBase):

    """Test cases using a disconnected Site object.

    Do not use this for mock Site objects.

    Never set a class or instance variable called 'site'
    As it will prevent tests from executing when invoked as:
    $ pytest -a 'not site'
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

        super().setUp()

    def tearDown(self):
        """Tear down test."""
        super().tearDown()

        config.site_interface = self.old_config_interface
        pywikibot.data.api.Request = _original_Request
        pywikibot.Claim.TARGET_CONVERTER['commonsMedia'] = self.old_convert


class CheckHostnameMixin(TestCaseBase):

    """Check the hostname is online before running tests."""

    _checked_hostnames = {}

    @classmethod
    def setUpClass(cls):
        """Set up the test class.

        Prevent tests running if the host is down.
        """
        super().setUpClass()

        if not hasattr(cls, 'sites'):
            return  # pragma: no cover

        for key, data in cls.sites.items():
            if 'hostname' not in data:
                raise Exception(  # pragma: no cover
                    f'{cls.__name__}: hostname not defined for {key}')
            hostname = data['hostname']

            if hostname in cls._checked_hostnames:
                if isinstance(cls._checked_hostnames[hostname], Exception):
                    raise unittest.SkipTest(
                        f'{cls.__name__}: hostname {hostname} failed '
                        f'(cached): {cls._checked_hostnames[hostname]}'
                    )
                if cls._checked_hostnames[hostname] is False:
                    raise unittest.SkipTest(
                        f'{cls.__name__}: hostname {hostname} failed (cached)')
                continue

            try:
                if '://' not in hostname:
                    hostname = 'http://' + hostname
                r = http.fetch(hostname,
                               method='HEAD',
                               default_error_handling=False)
                if r.status_code not in {HTTPStatus.OK,
                                         HTTPStatus.MOVED_PERMANENTLY,
                                         HTTPStatus.FOUND,
                                         HTTPStatus.SEE_OTHER,
                                         HTTPStatus.TEMPORARY_REDIRECT,
                                         HTTPStatus.PERMANENT_REDIRECT}:
                    raise ServerError(f'HTTP status: {r.status_code} - '
                                      f'{HTTPStatus(r.status_code).phrase}')
            except Exception as e:
                pywikibot.exception(
                    f'{cls.__name__}: accessing {hostname} caused exception:')

                cls._checked_hostnames[hostname] = e
                raise unittest.SkipTest(f'{cls.__name__}: hostname {hostname}'
                                        ' failed: {e}') from None

            cls._checked_hostnames[hostname] = True


class SiteWriteMixin(TestCaseBase):

    """Test cases involving writing to the server.

    When editing, the API should not be patched to use CachedRequest.
    This class prevents that.
    """

    @classmethod
    def setUpClass(cls) -> None:
        """Set up the test class.

        Reject write test classes configured with non-test wikis, or
        caching. Prevent test classes from writing to the site by
        default.

        The test class is skipped unless environment variable
        :envvar:`PYWIKIBOT_TEST_WRITE` is set to 1.

        .. versionchanged:: 9.2
           :envvar:`PYWIKIBOT_TEST_WRITE_FAIL` environment variable was
           discarded, see :ref:`Environment variables`.

        :raises Exception: test class cannot use *write* attribute
            together with *cached* and must be run on test sites only.
        """
        if issubclass(cls, ForceCacheMixin):  # pragma: no cover
            raise Exception(f'{cls.__name__} cannot be a subclass of both'
                            ' SiteWriteMixin and ForceCacheMixin')

        super().setUpClass()
        site = cls.get_site()

        if os.environ.get('PYWIKIBOT_TEST_WRITE', '0') != '1':
            raise unittest.SkipTest(f'{cls.__name__!r} write tests disabled.'
                                    ' Set PYWIKIBOT_TEST_WRITE=1 to enable.')

        if (not hasattr(site.family, 'test_codes')
                or site.code not in site.family.test_codes):
            raise Exception(  # pragma: no cover
                f'{cls.__name__} should only be run on test sites. To run '
                f'this test, add {site.code!r} to the {site.family.name}'
                " family attribute 'test_codes'."
            )


class RequireLoginMixin(TestCaseBase):

    """Run tests against a specific site, with a login."""

    login = True

    @classmethod
    def require_site_user(cls, family, code):
        """Check the user config has a valid login to the site."""
        if not cls.has_site_user(family, code):
            raise unittest.SkipTest(
                f'{cls.__name__}: No username for {family}:{code}')

    @classmethod
    def setUpClass(cls):
        """Set up the test class.

        Skip the test class if the user config does not have
        a valid login to the site.
        """
        super().setUpClass()

        for site_dict in cls.sites.values():
            cls.require_site_user(site_dict['family'], site_dict['code'])

            if hasattr(cls, 'oauth') and cls.oauth:
                continue

            site = site_dict['site']

            if site.siteinfo['readonly']:
                raise unittest.SkipTest(
                    'Site {} has readonly state: {}'.format(
                        site, site.siteinfo.get('readonlyreason', '')))

            with suppress(NoUsernameError):
                site.login()

            if not site.user():
                raise unittest.SkipTest(
                    f'{cls.__name__}: Not able to login to {site}')

    def setUp(self):
        """Set up the test case.

        Login to the site if it is not logged in.
        """
        super().setUp()
        self._reset_login(True)

    def tearDown(self):
        """Log back into the site."""
        super().tearDown()
        self._reset_login()

    def _reset_login(self, skip_if_login_fails: bool = False):
        """Login to all sites.

        There may be many sites, and setUp doesn't know which site is to
        be tested; ensure they are all logged in.

        .. versionadded:: 7.0
           The `skip_if_login_fails` parameter.

        :param skip_if_login_fails: called with setUp(); if True, skip
            the current current test.
        """
        for site in self.sites.values():
            site = site['site']

            if hasattr(self, 'oauth') and self.oauth:
                continue

            if not site.logged_in():
                site.login()

            if skip_if_login_fails and not site.user():  # during setUp() only
                self.skipTest(
                    f'{type(self).__name__}: Not able to re-login to {site}')

    def get_userpage(self, site=None):
        """Create a User object for the user's userpage."""
        if not site:
            site = self.get_site()

        # For multi-site test classes, or site is specified as a param,
        # the cached userpage object may not be the desired site.
        if hasattr(self, '_userpage') and self._userpage.site == site:
            return self._userpage  # pragma: no cover

        userpage = pywikibot.User(site, site.username())
        self._userpage = userpage
        return userpage


class NeedRightsMixin(TestCaseBase):

    """Require specific rights."""

    @classmethod
    def setUpClass(cls):
        """Set up the test class.

        Skip the test class if the user does not have required rights.
        """
        super().setUpClass()
        for site_dict in cls.sites.values():
            site = site_dict['site']

            if site.siteinfo['readonly'] or site.obsolete:
                raise unittest.SkipTest(
                    'Site {} has readonly state: {}'.format(
                        site, site.siteinfo.get('readonlyreason', '')))

            for right in cls.rights.split(','):
                if not site.has_right(right):
                    raise unittest.SkipTest(
                        f'User "{site.user()}" does not have required user '
                        f'right "{right}" on site "{site}"')


class MetaTestCaseClass(type):

    """Test meta class."""

    def __new__(cls, name, bases, dct):
        """Create the new class.

        .. versionchanged:: 9.3
           raises AttributeError instead of AssertionError for
           duplicated hostname, raises Exception instead of
           AssertionError for missing or wrong "net" attribute with
           hostnames.

        :raises AttributeError: hostname already found
        :raises Exception: Test classes using "pwb" must set "site" or
            test classes without a "site" configured must set "net" or
            test method must accept either 1 or 2 arguments or
            "net" must be True with hostnames defined.
        :meta public:
        """
        def wrap_method(key, sitedata, func):

            def wrapped_method(self):
                sitedata = self.sites[key]
                self.site_key = key
                self.family = sitedata['family']
                self.code = sitedata['code']
                self.site = sitedata['site']
                func(self, key)

            # sitedata['family'] may be an AutoFamily. Use str() for its name
            sitename = str(sitedata['family']) + ':' + sitedata['code']
            if func.__doc__:
                wrapped_method.__doc__ = removesuffix(func.__doc__, '.')
                wrapped_method.__doc__ += ' on ' + sitename
            else:
                wrapped_method.__doc__ = 'Test ' + sitename  # pragma: no cover

            return wrapped_method

        tests = [attr_name
                 for attr_name in dct
                 if attr_name.startswith('test')]

        base_tests = []
        if not tests:
            for base in bases:
                base_tests += [attr_name
                               for attr_name, attr in base.__dict__.items()
                               if (attr_name.startswith('test')
                                   and callable(attr))]

        dct['abstract_class'] = not tests and not base_tests

        # Bail out if it is the abstract class.
        if dct['abstract_class']:
            return super().__new__(cls, name, bases, dct)

        # Inherit superclass attributes
        for base in bases:
            for key in ('cached', 'code', 'dry', 'family', 'hostname',
                        'hostnames', 'login', 'net', 'oauth', 'pwb', 'site',
                        'sites', 'rights', 'wikibase', 'write'):
                if hasattr(base, key) and key not in dct:
                    dct[key] = getattr(base, key)

        # Will be inserted into dct[sites] later
        if 'hostname' in dct:
            hostnames = [dct['hostname']]
            del dct['hostname']
        else:
            hostnames = dct.get('hostnames', [])

        if dct.get('net') is False:
            dct['site'] = False

        if 'sites' in dct:
            dct.setdefault('site', True)

        # If either are specified, assume both should be specified
        if 'family' in dct or 'code' in dct:
            dct['site'] = True

            if (('sites' not in dct or not dct['sites'])
                    and 'family' in dct
                    and 'code' in dct and dct['code'] != '*'):
                # Add entry to self.sites
                dct['sites'] = {
                    str(dct['family'] + ':' + dct['code']): {
                        'code': dct['code'],
                        'family': dct['family'],
                    }
                }

        if hostnames:
            dct.setdefault('sites', {})
            for hostname in hostnames:
                if hostname in dct['sites']:  # pragma: no cover
                    raise AttributeError(f'hostname {hostname!r} already found'
                                         f"in dict['sites']:\n{dict['sites']}")
                dct['sites'][hostname] = {'hostname': hostname}

        if dct.get('dry') is True:
            dct['net'] = False

        if (('sites' not in dct and 'site' not in dct)
                or ('site' in dct and not dct['site'])):
            # Prevent use of pywikibot.Site
            bases = cls.add_base(bases, DisableSiteMixin)

            # 'pwb' tests will _usually_ require a site. To ensure the
            # test class dependencies are declarative, this requires the
            # test writer explicitly sets 'site=False' so code reviewers
            # check that the script invoked by pwb will not load a site.
            if dct.get('pwb') and 'site' not in dct:
                raise Exception(  # pragma: no cover
                    f'{name}: Test classes using pwb must set "site";'
                    ' add site=False if the test script will not use a site'
                )

            # If the 'site' attribute is a false value,
            # remove it so it matches 'not site' in pytest.
            if 'site' in dct:
                del dct['site']

            # If there isn't a site, require declaration of net activity.
            if 'net' not in dct:  # pragma: no cover
                raise Exception(f'{name}: Test classes without a site'
                                ' configured must set "net"')

            # If the 'net' attribute is a false value,
            # remove it so it matches 'not net' in pytest.
            if not dct['net']:
                del dct['net']

            return super().__new__(cls, name, bases, dct)

        # The following section is only processed if the test uses sites.

        if dct.get('dry'):
            bases = cls.add_base(bases, DisconnectedSiteMixin)
            del dct['net']
        else:
            dct['net'] = True

        if dct.get('cached'):
            bases = cls.add_base(bases, ForceCacheMixin)

        if dct.get('net'):
            bases = cls.add_base(bases, CheckHostnameMixin)
        elif hostnames:  # pragma: no cover
            raise Exception('"net" must be True with hostnames defined')

        if dct.get('write'):
            dct.setdefault('login', True)
            bases = cls.add_base(bases, SiteWriteMixin)

        if dct.get('rights'):
            dct.setdefault('login', True)

        if dct.get('login'):
            bases = cls.add_base(bases, RequireLoginMixin)

        # Add NeedRightsMixin after RequireLoginMixin to ensure
        # login is made prior to rights check
        if dct.get('rights'):
            bases = cls.add_base(bases, NeedRightsMixin)

        for test in tests:
            test_func = dct[test]

            # Method decorated with unittest.expectedFailure has no arguments
            # so it is assumed to not be a multi-site test method.
            # A normal test method only accepts 'self'
            if test_func.__code__.co_argcount in (0, 1):
                continue

            # A multi-site test method only accepts 'self' and the site-key
            if test_func.__code__.co_argcount != 2:
                raise Exception(  # pragma: no cover
                    f'{name}: Test method {test} must accept either 1 or 2 '
                    f'arguments;  {test_func.__code__.co_argcount} found'
                )

            # create test methods processed by unittest
            for (key, sitedata) in dct['sites'].items():
                table = str.maketrans('-:', '__')
                test_name = (test + '_' + key.translate(table))
                cls.add_method(dct, test_name,
                               wrap_method(key, sitedata, dct[test]))

                if key in dct.get('expected_failures', []):
                    dct[test_name] = unittest.expectedFailure(dct[test_name])

            del dct[test]

        return super().__new__(cls, name, bases, dct)

    @staticmethod
    def add_base(bases, subclass):
        """Return a tuple of bases with the subclasses added if not already."""
        if not any(issubclass(base, subclass) for base in bases):
            bases = (subclass, *bases)
        return bases

    @staticmethod
    def add_method(dct, test_name, method, doc=None, doc_suffix=None):
        """Set method's __name__ and __doc__ and add it to dct.

        .. versionchanged:: 9.3
           raises ValueError instead of AssertionError

        :raises ValueError: doc string must end with a period.
        """
        dct[test_name] = method
        # it's explicitly using str() because __name__ must be str
        dct[test_name].__name__ = str(test_name)
        if doc_suffix:
            if not doc:
                doc = method.__doc__
            if doc[-1] != '.':  # pragma: no cover
                raise ValueError('doc string must end with a period.')
            doc = doc[:-1] + ' ' + doc_suffix + '.'

        if doc:
            dct[test_name].__doc__ = doc


class TestCase(TestCaseBase, metaclass=MetaTestCaseClass):

    """Run tests on pre-defined sites."""

    @classmethod
    def setUpClass(cls):
        """Set up the test class.

        Prefetch the Site object for each of the sites the test
        class has declared are needed.
        """
        super().setUpClass()

        if not hasattr(cls, 'sites'):
            return

        # This stores the site under the site name.
        if not cls.sites:
            cls.sites = {}  # pragma: no cover

        # If the test is not cached, create new Site objects for this class
        cm = cls._uncached()
        cm.__enter__()

        interface = None  # defaults to 'APISite'
        dry = hasattr(cls, 'dry') and cls.dry
        if dry:
            interface = DrySite

        for data in cls.sites.values():
            if 'site' not in data and 'code' in data and 'family' in data:
                with suppress_warnings(WARN_SITE_CODE, category=UserWarning):
                    data['site'] = Site(data['code'], data['family'],
                                        interface=interface)
            if 'hostname' not in data and 'site' in data:
                # Ignore if the family has defined this as
                # obsolete without a mapping to a hostname.
                with suppress(KeyError):
                    data['hostname'] = (
                        data['site'].base_url(data['site'].apipath()))

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
            pywikibot._sites.clear()
        yield
        if not hasattr(cls, 'cached') or not cls.cached:
            pywikibot._sites = orig_sites

    @classmethod
    def get_site(cls, name=None):
        """Return the prefetched Site object.

        .. versionchanged:: 9.3
           raises Exception instead of AssertionError for site mismatch

        :raises Exception: method called for multiple sites without
            *name* argument given or *name* not found in sites attribute
            or cls.site is not equal to cls.sites content for the given
            *name*.
        """
        if not name and hasattr(cls, 'sites'):
            if len(cls.sites) != 1:  # pragma: no cover
                raise Exception(f'"{cls.__name__}.get_site(name=None)"'
                                ' called with multiple sites')

            name = next(iter(cls.sites.keys()))

        if name and name not in cls.sites:  # pragma: no cover
            raise Exception(f'"{name}" not declared in {cls.__name__}')

        if isinstance(cls.site, BaseSite):
            if cls.sites[name]['site'] != cls.site:  # pragma: no cover
                raise Exception(f'{cls.__name__}.site is different from '
                                f"{cls.__name__}.sites[{name!r}]['site']:\n"
                                f"{cls.site} != {cls.sites[name]['site']}")
            return cls.site

        return cls.sites[name]['site']

    @classmethod
    def has_site_user(cls, family, code):
        """Check the user config has a user for the site."""
        if not family:  # pragma: no cover
            raise Exception(f'no family defined for {cls.__name__}')
        if not code:  # pragma: no cover
            raise Exception(f'no site code defined for {cls.__name__}')

        usernames = config.usernames

        return (code in usernames[family] or '*' in usernames[family]
                or code in usernames['*'] or '*' in usernames['*'])

    def __init__(self, *args, **kwargs):
        """Initializer."""
        super().__init__(*args, **kwargs)

        if not hasattr(self, 'sites'):
            return

        # Create an instance method named the same as the class method
        self.get_site = lambda name=None: self.__class__.get_site(name)

    def get_mainpage(self, site=None, force=False):
        """Create a Page object for the sites main page.

        :param site: Override current site, obtained using :py:obj:`get_site`.
        :type site: pywikibot.site.APISite or None
        :param force: Get an unused Page object
        :type force: bool
        :rtype: pywikibot.Page
        """
        if not site:
            site = self.get_site()

        # For multi-site test classes, or site is specified as a param,
        # the cached mainpage object may not be the desired site.
        if hasattr(self, '_mainpage') and not force \
           and self._mainpage.site == site:
            return self._mainpage

        maintitle = site.siteinfo['mainpage']
        maintitle = removeprefix(maintitle, 'Special:MyLanguage/')  # T278702
        mainpage = pywikibot.Page(site, maintitle)
        if not isinstance(site, DrySite) and mainpage.isRedirectPage():
            mainpage = mainpage.getRedirectTarget()  # pragma: no cover

        if force:
            mainpage = pywikibot.Page(self.site, mainpage.title())

        self._mainpage = mainpage

        return mainpage

    def get_missing_article(self, site=None):
        """Get a Page which refers to a missing page on the site.

        :type site: pywikibot.Site or None
        :rtype: pywikibot.Page
        """
        if not site:
            site = self.get_site()
        page = pywikibot.Page(site, 'There is no page with this title')
        if page.exists():
            raise unittest.SkipTest('Did not find a page that does not exist.')

        return page


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
        """Patch the obj's attribute with the replacement.

        It will be reset after each ``tearDown``.
        """
        self._patched_instances += [(obj, attr_name, getattr(obj, attr_name))]
        setattr(obj, attr_name, replacement)

    def setUp(self):
        """Set up the test by initializing the patched list."""
        super().setUp()
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
        super().tearDown()


class SiteAttributeTestCase(TestCase):

    """Add the sites as attributes to the instances."""

    @classmethod
    def setUpClass(cls):
        """Add each initialized site as an attribute to cls."""
        super().setUpClass()
        for site in cls.sites:
            if 'site' in cls.sites[site]:
                setattr(cls, site, cls.sites[site]['site'])


class DefaultSiteTestCase(TestCase):

    """Run tests against the config specified site."""

    family = config.family
    code = config.mylang

    @classmethod
    def override_default_site(cls, site):
        """Override the default site.

        :param site: site tests should use
        :type site: BaseSite
        """
        unittest_print(
            f'{cls.__name__} using {site} instead of {cls.family}:{cls.code}.')
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
        super().setUp()

    def tearDown(self):
        """Restore the environment."""
        pywikibot.config.family = self.original_family
        pywikibot.config.mylang = self.original_code
        super().tearDown()


class ScriptMainTestCase(AlteredDefaultSiteTestCase):

    """Tests that depend on the default site being set to the test site."""

    def setUp(self):
        """Prepare the environment for running main() in a script."""
        super().setUp()
        site = self.get_site()
        pywikibot.config.family = site.family
        pywikibot.config.mylang = site.code


class DefaultDrySiteTestCase(DefaultSiteTestCase):

    """Run tests using the config specified site in offline mode."""

    dry = True


class WikimediaDefaultSiteTestCase(DefaultSiteTestCase):

    """Test class to run against a WMF site, preferring the default site."""

    @classmethod
    def setUpClass(cls):
        """Set up the test class.

        Check that the default site is a Wikimedia site.
        Use en.wikipedia.org as a fallback.

        .. versionchanged:: 9.3
           raises Exception instead of AssertionError

        :raises Exception: "site" or "sites" attribute is missing or
            "sites" entries count is different from 1.
        """
        super().setUpClass()

        if not (hasattr(cls, 'site') and hasattr(cls, 'sites')) \
           or len(cls.sites) != 1:  # pragma: no cover
            raise Exception('"site" or "sites" attribute is missing or "sites"'
                            'entries count is different from 1')

        site = cls.get_site()
        if not isinstance(site.family, WikimediaFamily):
            cls.override_default_site(pywikibot.Site('en', 'wikipedia'))


class WikibaseTestCase(TestCase):

    """Run tests against a wikibase site."""

    wikibase = True

    @classmethod
    def setUpClass(cls):
        """Set up the test class.

        Checks that all sites are configured with a Wikibase repository,
        with Site.has_data_repository() returning True, and all sites
        use the same data repository.
        """
        super().setUpClass()

        with cls._uncached():
            for data in cls.sites.values():
                if 'site' not in data:
                    continue  # pragma: no cover

                site = data['site']
                if not site.has_data_repository:
                    raise unittest.SkipTest(f'{cls.__name__}: {site!r} does'
                                            ' not have data repository')

                if (hasattr(cls, 'repo')
                        and cls.repo != site.data_repository()):
                    raise Exception(  # pragma: no cover
                        f'{cls.__name__}: sites do not all have the same data'
                        ' repository')

                cls.repo = site.data_repository()

    @classmethod
    def get_repo(cls):
        """Return the prefetched DataSite object."""
        return cls.repo

    def __init__(self, *args, **kwargs):
        """Initializer."""
        super().__init__(*args, **kwargs)

        if not hasattr(self, 'sites'):
            return

        # Create an instance method named the same as the class method
        self.get_repo = lambda: self.repo


class WikibaseClientTestCase(WikibaseTestCase):

    """Run tests against a specific site connected to a wikibase."""

    @classmethod
    def setUpClass(cls):
        """Set up the test class.

        Checks that all sites are configured as a Wikibase client,
        with Site.has_data_repository returning True.
        """
        super().setUpClass()

        for site in cls.sites.values():
            if not site['site'].has_data_repository:
                raise unittest.SkipTest(f"{cls.__name__}: {site['site']!r}"
                                        ' does not have data repository')


class DefaultWikibaseClientTestCase(WikibaseClientTestCase,
                                    DefaultSiteTestCase):

    """Run tests against any site connected to a Wikibase."""


class WikidataTestCase(WikibaseTestCase):

    """Test cases use Wikidata."""

    family = 'wikidata'
    code = 'wikidata'

    cached = True


class DefaultWikidataClientTestCase(DefaultWikibaseClientTestCase):

    """Run tests against any site connected to Wikidata."""

    @classmethod
    def setUpClass(cls):
        """Set up the test class.

        Require the data repository is wikidata.org.
        """
        super().setUpClass()

        if str(cls.get_repo()) != 'wikidata:wikidata':
            raise unittest.SkipTest(f'{cls.__name__}: {cls.get_site()} is not'
                                    'connected to Wikidata.')


class PwbTestCase(TestCase):

    """Test cases use :mod:`pwb` to invoke scripts.

    Test cases which use pwb typically also access a site, and use the
    network. Even during initialisation, scripts may call
    :func:`pywikibot.handle_args`, which initialises loggers and uses
    the network to determine if the code is stale.

    The flag 'pwb' is used by the TestCase metaclass to check that a
    test site is set declared in the class properties, or that
    :code:`site = False` is added to the class properties in the
    unlikely scenario that the test case uses pwb in a way that doesn't
    use a site.

    If a test class is marked as :code:`site = False , the metaclass
    will also check that the ``net`` flag is explicitly set.
    """

    pwb = True

    def setUp(self):
        """Prepare the environment for running the pwb.py script."""
        super().setUp()
        self.orig_pywikibot_dir = None
        if 'PYWIKIBOT_DIR' in os.environ:  # pragma: no cover
            self.orig_pywikibot_dir = os.environ['PYWIKIBOT_DIR']
        base_dir = pywikibot.config.base_dir
        os.environ['PYWIKIBOT_DIR'] = base_dir

    def tearDown(self):
        """Restore the environment after running the pwb.py script."""
        super().tearDown()
        del os.environ['PYWIKIBOT_DIR']
        if self.orig_pywikibot_dir:  # pragma: no cover
            os.environ['PYWIKIBOT_DIR'] = self.orig_pywikibot_dir

    def execute(self, args: list[str], **kwargs):
        """Run :func:`tests.utils.execute_pwb` with default site.

        .. versionchanged:: 9.1
           pass all arguments to :func:`tests.utils.execute_pwb`; make
           this method public.

        :param args: :mod:`pwb` warapper script arguments
        :param kwargs: keyword arguments of :func:`tests.utils.execute_pwb`
        """
        site = self.get_site()
        args.append(f'-site:{site.sitename}')
        return execute_pwb(args, **kwargs)


class RecentChangesTestCase(WikimediaDefaultSiteTestCase):

    """Test cases for tests that use recent change."""

    # site.recentchanges() includes external edits from wikidata,
    # except on wiktionaries which are not linked to wikidata
    # so total=3 should not be too high for most sites.
    length = 3

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        if os.environ.get('PYWIKIBOT_TEST_NO_RC', '0') == '1':
            raise unittest.SkipTest(
                'PYWIKIBOT_TEST_NO_RC is set; RecentChanges tests disabled.')

        super().setUpClass()

        if cls.get_site().code in ('test', 'test2'):
            cls.override_default_site(pywikibot.Site('en', 'wikipedia'))


class DeprecationTestCase(TestCase):

    """Test cases for deprecation function in the tools module."""

    _generic_match = re.compile(
        r'.* is deprecated(?: since release [\d.]+ [^;]*)?'
        r'(; use .* instead)?\.')

    source_adjustment_skips = [
        unittest.case._AssertRaisesContext,
        TestCase.assertRaises,
        TestCase.assertRaisesRegex,
    ]

    # Require no instead string
    NO_INSTEAD = object()
    # Require an instead string
    INSTEAD = object()

    # Python 3 component in the call stack of _AssertRaisesContext
    if hasattr(unittest.case, '_AssertRaisesBaseContext'):
        source_adjustment_skips.append(unittest.case._AssertRaisesBaseContext)

    def __init__(self, *args, **kwargs):
        """Initializer."""
        super().__init__(*args, **kwargs)
        self.warning_log = []

        self.expect_warning_filename = inspect.getfile(self.__class__)
        if self.expect_warning_filename.endswith('.pyc'):  # pragma: no cover
            self.expect_warning_filename = self.expect_warning_filename[:-1]

        self._do_test_warning_filename = True
        self._ignore_unknown_warning_packages = False

        self.context_manager = WarningSourceSkipContextManager(
            self.source_adjustment_skips)

    def _reset_messages(self):
        """Reset captured deprecation warnings."""
        self._do_test_warning_filename = True
        del self.warning_log[:]

    @property
    def deprecation_messages(self):
        """Return captured deprecation warnings."""
        return [str(item.message) for item in self.warning_log]

    @classmethod
    def _build_message(cls,
                       deprecated: str | None,
                       instead: str | bool | None) -> Any:
        """Build a deprecation warning result.

        .. versionchanged:: 9.3
           raises TypeError instead of AssertionError

        :raises TypeError: invalid *instead* type
        """
        if deprecated is not None:
            msg = f'{deprecated} is deprecated'
            if instead:
                msg += f'; use {instead} instead.'
        elif instead is None:  # pragma: no cover
            msg = None
        elif instead is True:  # pragma: no cover
            msg = cls.INSTEAD
        elif instead is False:  # pragma: no cover
            msg = cls.NO_INSTEAD
        else:
            raise TypeError(  # pragma: no cover
                f'instead argument must not be a {type(instead).__name__!r}')
        return msg

    def assertDeprecationParts(self, deprecated=None, instead=None):
        """Assert that a deprecation warning happened.

        To simplify deprecation tests it just requires the to separated parts
        and forwards the result to :py:obj:`assertDeprecation`.

        :param deprecated: The deprecated string. If None it uses a generic
            match depending on instead.
        :type deprecated: str or None
        :param instead: The instead string unless deprecated is None. If it's
            None it allows any generic deprecation string, on True only those
            where instead string is present and on False only those where it's
            missing. If the deprecation string is not None, no instead string
            is expected when instead evaluates to False.
        :type instead: str or None or True or False
        """
        self.assertDeprecation(self._build_message(deprecated, instead))

    def assertDeprecation(self, msg=None):
        """Assert that a deprecation warning happened.

        :param msg: Either the specific message or None to allow any generic
            message. When set to ``INSTEAD`` it only counts those supplying an
            alternative and when ``NO_INSTEAD`` only those not supplying one.
        :type msg: str or None or INSTEAD or NO_INSTEAD
        """
        if msg is None or msg is self.INSTEAD or msg is self.NO_INSTEAD:
            deprecation_messages = self.deprecation_messages
            for deprecation_message in deprecation_messages:
                match = self._generic_match.match(deprecation_message)
                if (match and bool(match[1]) == (msg is self.INSTEAD)
                        or msg is None):
                    break
            else:  # pragma: no cover
                self.fail('No generic deprecation message match found in '
                          f'{deprecation_messages}')
        else:
            head, _, tail = msg.partition('; ')
            for message in self.deprecation_messages:
                if message.startswith(head) \
                   and message.endswith(tail):
                    break
            else:  # pragma: no cover
                self.fail(f"'{msg}' not found in {self.deprecation_messages}"
                          '(ignoring since)')
        if self._do_test_warning_filename:
            self.assertDeprecationFile(self.expect_warning_filename)

    def assertOneDeprecationParts(self, deprecated=None, instead=None,
                                  count=1):
        """Assert that exactly one deprecation message happened and reset.

        It uses the same arguments as :py:obj:`assertDeprecationParts`.
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
        self.assertLength(self.deprecation_messages, count)
        self._reset_messages()

    def assertNoDeprecation(self, msg=None):
        """Assert that no deprecation warning happened."""
        if msg:  # pragma: no cover
            self.assertNotIn(msg, self.deprecation_messages)
        else:
            self.assertIsEmpty(self.deprecation_messages)

    def assertDeprecationClass(self, cls):
        """Assert that all deprecation warning are of one class."""
        for item in self.warning_log:
            self.assertIsInstance(item.message, cls)

    def assertDeprecationFile(self, filename):
        """Assert that all deprecation warning are of one filename."""
        for item in self.warning_log:
            if (self._ignore_unknown_warning_packages
                    and 'pywikibot' not in item.filename):
                continue  # pragma: no cover

            if item.filename != filename:
                self.fail(f'expected warning filename {filename}; warning '
                          f'item: {item}')

    @classmethod
    def setUpClass(cls):
        """Only operate in debug mode."""
        if not __debug__:
            raise unittest.SkipTest(
                f'{cls.__name__} is disabled when __debug__ is disabled.')
        super().setUpClass()

    def setUp(self):
        """Set up unit test."""
        super().setUp()

        self.warning_log = self.context_manager.__enter__()
        warnings.simplefilter('always')

        self._reset_messages()

    def tearDown(self):
        """Tear down unit test."""
        self.context_manager.__exit__()

        super().tearDown()


class HttpbinTestCase(TestCase):

    """Custom test case class, which allows dry httpbin tests.

    Test cases, which use httpbin, need to inherit this class.
    """

    sites = {
        'httpbin': {
            'hostname': 'httpbin.org',
        },
    }

    def get_httpbin_url(self, path=''):
        """Return url of httpbin."""
        return 'http://httpbin.org' + path

    def get_httpbin_hostname(self):
        """Return httpbin hostname."""
        return 'httpbin.org'

    def fetch(self, *args, **kwargs):
        """Delegate http request to http.fetch but skip on ServerError."""
        with skipping(ServerError):
            return http.fetch(*args, **kwargs)
