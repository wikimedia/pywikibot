"""Test utilities."""
#
# (C) Pywikibot team, 2013-2023
#
# Distributed under the terms of the MIT license.
#
import inspect
import os
import sys
import unittest
import warnings
from contextlib import contextmanager
from subprocess import PIPE, Popen, TimeoutExpired
from typing import Optional

import pywikibot
from pywikibot import config
from pywikibot.backports import List
from pywikibot.data.api import CachedRequest
from pywikibot.data.api import Request as _original_Request
from pywikibot.exceptions import APIError
from pywikibot.login import LoginStatus
from pywikibot.site import Namespace
from tests import _pwb_py


OSWIN32 = (sys.platform == 'win32')


def expected_failure_if(expect):
    """
    Unit test decorator to expect failure under conditions.

    :param expect: Flag to check if failure is expected
    :type expect: bool
    """
    if expect:
        return unittest.expectedFailure
    return lambda orig: orig


def fixed_generator(iterable):
    """Return a dummy generator ignoring all parameters.

    This can be used to overwrite a generator method and yield
    predefined items:

    >>> from tests.utils import fixed_generator
    >>> site = pywikibot.Site()
    >>> page = pywikibot.Page(site, 'Any page')
    >>> list(page.linkedPages(total=1))
    []
    >>> gen = fixed_generator([
    ...     pywikibot.Page(site, 'User:BobBot/Redir'),
    ...     pywikibot.Page(site, 'Main Page')])
    >>> page.linkedPages = gen
    >>> list(page.linkedPages(total=1))
    [Page('Benutzer:BobBot/Redir'), Page('Main Page')]
    """
    def gen(*args, **kwargs):
        yield from iterable

    return gen


def entered_loop(iterable):
    """Return True if iterable contains items."""
    for _ in iterable:
        return True
    return False


class WarningSourceSkipContextManager(warnings.catch_warnings):

    """
    Warning context manager that adjusts source of warning.

    The source of the warning will be moved further down the
    stack to skip a list of objects that have been monkey
    patched into the call stack.
    """

    def __init__(self, skip_list):
        """
        Initializer.

        :param skip_list: List of objects to be skipped. The source of any
            warning that matches the skip_list won't be adjusted.
        :type skip_list: list of object or (obj, str, int, int)
        """
        super().__init__(record=True)
        self.skip_list = skip_list

    @property
    def skip_list(self):
        """
        Return list of filename and line ranges to skip.

        :rtype: list of (obj, str, int, int)
        """
        return self._skip_list

    @skip_list.setter
    def skip_list(self, value):
        """
        Set list of objects to be skipped.

        :param value: List of objects to be skipped
        :type value: list of object or (obj, str, int, int)
        """
        self._skip_list = []
        for item in value:
            if isinstance(item, tuple):
                self._skip_list.append(item)
            else:
                filename = inspect.getsourcefile(item)
                code, first_line = inspect.getsourcelines(item)
                last_line = first_line + len(code)
                self._skip_list.append(
                    (item, filename, first_line, last_line))

    def __enter__(self):
        """Enter the context manager."""
        def detailed_show_warning(*args, **kwargs):
            """Replacement handler for warnings.showwarning."""
            warn_msg = warnings.WarningMessage(*args, **kwargs)

            skip_frames = 0
            a_frame_has_matched_warn_msg = False

            # The following for-loop will adjust the warn_msg only if the
            # warning does not match the skip_list.
            for _, frame_filename, frame_lineno, *_ in inspect.stack():
                if any(start <= frame_lineno <= end
                       for (_, skip_filename, start, end) in self.skip_list
                       if skip_filename == frame_filename):
                    # this frame matches to one of the items in the skip_list
                    if a_frame_has_matched_warn_msg:
                        continue

                    skip_frames += 1

                if frame_filename == warn_msg.filename \
                   and frame_lineno == warn_msg.lineno:
                    if not skip_frames:
                        break
                    a_frame_has_matched_warn_msg = True

                if a_frame_has_matched_warn_msg:
                    if not skip_frames:
                        # adjust the warn_msg
                        warn_msg.filename = frame_filename
                        warn_msg.lineno = frame_lineno
                        break

                    skip_frames -= 1

            # Ignore socket IO warnings (T183696, T184996)
            if issubclass(warn_msg.category, ResourceWarning) \
               and str(warn_msg.message).startswith(
                   ('unclosed <ssl.SSLSocket', 'unclosed <socket.socket')):
                return

            log.append(warn_msg)

        log = super().__enter__()
        self._module.showwarning = detailed_show_warning
        return log


class AssertAPIErrorContextManager:

    """
    Context manager to assert certain APIError exceptions.

    This is build similar to the :py:obj:`unittest.TestCase.assertError`
    implementation which creates a context manager. It then calls
    :py:obj:`handle` which either returns this manager if no executing
    object given or calls the callable object.
    """

    def __init__(self, code, info, msg, test_case, regex=None):
        """Create instance expecting the code and info."""
        self.code = code
        self.info = info
        self.msg = msg
        self.test_case = test_case
        self.regex = regex

    def __enter__(self):
        """Enter this context manager and the unittest's context manager."""
        if self.regex:
            self.cm = self.test_case.assertRaisesRegex(APIError, self.regex,
                                                       msg=self.msg)
        else:
            self.cm = self.test_case.assertRaises(APIError, msg=self.msg)
        self.cm.__enter__()
        return self.cm

    def __exit__(self, exc_type, exc_value, tb):
        """Exit the context manager and assert code and optionally info."""
        result = self.cm.__exit__(exc_type, exc_value, tb)
        assert result is isinstance(exc_value, APIError)
        if result:
            self.test_case.assertEqual(exc_value.code, self.code)
            if self.info:
                self.test_case.assertEqual(exc_value.info, self.info)
        return result

    def handle(self, callable_obj, args, kwargs):
        """Handle the callable object by returning itself or using itself."""
        if callable_obj is None:
            return self
        with self:
            callable_obj(*args, **kwargs)
        return None


class DryParamInfo(dict):

    """Dummy class to use instead of :py:obj:`data.api.ParamInfo`."""

    def __init__(self, *args, **kwargs):
        """Initializer."""
        super().__init__(*args, **kwargs)
        self.action_modules = set()
        self.query_modules = set()

    def fetch(self, modules, _init=False):
        """Load dry data."""
        return [self[mod] for mod in modules]

    def parameter(self, module, param_name):
        """Load dry data."""
        return self[module].get(param_name)

    def __getitem__(self, name):
        """Return dry data or a dummy parameter block."""
        try:
            return super().__getitem__(name)
        except KeyError:
            return {'name': name, 'limit': None}


class DummySiteinfo:

    """Dummy class to use instead of :py:obj:`pywikibot.site.Siteinfo`."""

    def __init__(self, cache):
        """Initializer."""
        self._cache = {key: (item, False) for key, item in cache.items()}

    def __getitem__(self, key):
        """Get item."""
        return self.get(key, False)

    def __setitem__(self, key, value):
        """Set item."""
        self._cache[key] = (value, False)

    def get(self, key, get_default=True, cache=True, expiry=False):
        """Return dry data."""
        # Default values are always expired, so only expiry=False doesn't force
        # a reload
        force = expiry is not False
        if not force and key in self._cache:
            loaded = self._cache[key]
            if not loaded[1] and not get_default:
                raise KeyError(key)

            return loaded[0]

        if get_default:
            default = pywikibot.site.Siteinfo._get_default(key)
            if cache:
                self._cache[key] = (default, False)
            return default

        raise KeyError(key)

    def __contains__(self, key):
        """Return False."""
        return False

    def is_recognised(self, key):
        """Return None."""
        return None

    def get_requested_time(self, key):
        """Return False."""
        return False


class DryRequest(CachedRequest):

    """Dummy class to use instead of :py:obj:`data.api.Request`."""

    def __init__(self, *args, **kwargs):
        """Initializer."""
        _original_Request.__init__(self, *args, **kwargs)

    @classmethod
    def create_simple(cls, req_site, **kwargs):
        """Skip CachedRequest implementation."""
        return _original_Request.create_simple(req_site, **kwargs)

    def _expired(self, dt):
        """Never invalidate cached data."""
        return False

    def _write_cache(self, data):
        """Never write data."""
        return

    def submit(self):
        """Prevented method."""
        raise Exception('DryRequest rejecting request: {!r}'
                        .format(self._params))


class DrySite(pywikibot.site.APISite):

    """Dummy class to use instead of :py:obj:`pywikibot.site.APISite`."""

    _loginstatus = LoginStatus.NOT_ATTEMPTED

    def __init__(self, code, fam, user):
        """Initializer."""
        super().__init__(code, fam, user)
        self._userinfo = pywikibot.tools.collections.EMPTY_DEFAULT
        self._paraminfo = DryParamInfo()
        self._siteinfo = DummySiteinfo({})
        self._siteinfo._cache['lang'] = (code, True)
        self._siteinfo._cache['case'] = (
            'case-sensitive' if self.family.name == 'wiktionary' else
            'first-letter', True)
        self._siteinfo._cache['mainpage'] = 'Main Page'
        extensions = []
        if self.family.name == 'wikisource':
            extensions.append({'name': 'ProofreadPage'})
        self._siteinfo._cache['extensions'] = (extensions, True)
        aliases = []
        for alias in ('PrefixIndex', ):
            # TODO: Not all follow that scheme (e.g. "BrokenRedirects")
            aliases.append(
                {'realname': alias.capitalize(), 'aliases': [alias]})
        self._siteinfo._cache['specialpagealiases'] = (aliases, True)
        self._msgcache = {'*': 'dummy entry', 'hello': 'world'}

    def _build_namespaces(self):
        ns_dict = Namespace.builtin_namespaces(case=self.siteinfo['case'])
        if hasattr(self.family, 'authornamespaces'):
            assert len(self.family.authornamespaces[self.code]) <= 1
            if self.family.authornamespaces[self.code]:
                author_ns = self.family.authornamespaces[self.code][0]
                assert author_ns not in ns_dict
                ns_dict[author_ns] = Namespace(
                    author_ns, 'Author', case=self.siteinfo['case'])
        return ns_dict

    def linktrail(self):
        """Return default linkrail."""
        return '[a-z]*'

    @property
    def userinfo(self):
        """Return dry data."""
        return self._userinfo

    def version(self):
        """Return a big dummy version string."""
        return '999.999'

    def image_repository(self):
        """Return Site object for image repository e.g. commons."""
        code, fam = self.shared_image_repository()
        if bool(code or fam):
            return pywikibot.Site(code, fam, self.username(),
                                  interface=self.__class__)
        return None

    def data_repository(self):
        """Return Site object for data repository e.g. Wikidata."""
        if self.hostname().endswith('.beta.wmflabs.org'):
            # TODO: Use definition for beta cluster's wikidata
            code, fam = None, None
            fam_name = self.hostname().split('.')[-4]
        else:
            code, fam = 'wikidata', 'wikidata'
            fam_name = self.family.name

        # Only let through valid entries
        if fam_name not in ('commons', 'wikibooks', 'wikidata', 'wikinews',
                            'wikipedia', 'wikiquote', 'wikisource',
                            'wikivoyage'):
            code, fam = None, None

        if bool(code or fam):
            return pywikibot.Site(code, fam, self.username(),
                                  interface=DryDataSite)
        return None

    def login(self, *args, cookie_only=False, **kwargs):
        """Overwrite login which is called when a site is initialized.

        .. versionadded: 8.0.4
        """
        if cookie_only:
            return
        raise Exception(f'Attempting to login with {type(self).__name__}')


class DryDataSite(DrySite, pywikibot.site.DataSite):

    """Dummy class to use instead of :py:obj:`pywikibot.site.DataSite`."""

    def _build_namespaces(self):
        namespaces = super()._build_namespaces()
        namespaces[0].defaultcontentmodel = 'wikibase-item'
        namespaces[120] = Namespace(id=120,
                                    case='first-letter',
                                    canonical_name='Property',
                                    defaultcontentmodel='wikibase-property')
        return namespaces


class DryPage(pywikibot.Page):

    """Dummy class that acts like a Page but avoids network activity."""

    _pageid = 1
    _disambig = False
    _isredir = False

    def isDisambig(self):  # noqa: N802
        """Return disambig status stored in _disambig."""
        return self._disambig


class FakeLoginManager(pywikibot.login.ClientLoginManager):

    """Loads a fake password."""

    @property
    def password(self):
        """Get the fake password."""
        return 'foo'

    @password.setter
    def password(self, value):
        """Ignore password changes."""


def execute(command: List[str], data_in=None, timeout=None, error=None):
    """
    Execute a command and capture outputs.

    :param command: executable to run and arguments to use
    """
    env = os.environ.copy()

    # Prevent output by test package; e.g. 'max_retries reduced from x to y'
    env['PYWIKIBOT_TEST_QUIET'] = '1'

    # sys.path may have been modified by the test runner to load dependencies.
    pythonpath = os.pathsep.join(sys.path)

    env['PYTHONPATH'] = pythonpath
    env['PYTHONIOENCODING'] = config.console_encoding

    # PYWIKIBOT_USERINTERFACE_LANG will be assigned to
    # config.userinterface_lang
    if pywikibot.config.userinterface_lang:
        env['PYWIKIBOT_USERINTERFACE_LANG'] \
            = pywikibot.config.userinterface_lang

    # Set EDITOR to an executable that ignores all arguments and does nothing.
    env['EDITOR'] = 'break' if OSWIN32 else 'true'

    p = Popen(command, env=env, stdout=PIPE, stderr=PIPE,
              stdin=PIPE if data_in is not None else None)

    if data_in is not None:
        data_in = data_in.encode(config.console_encoding)

    try:
        stdout_data, stderr_data = p.communicate(input=data_in,
                                                 timeout=timeout)
    except TimeoutExpired:
        p.kill()
        stdout_data, stderr_data = p.communicate()

    return {'exit_code': p.returncode,
            'stdout': stdout_data.decode(config.console_encoding),
            'stderr': stderr_data.decode(config.console_encoding)}


def execute_pwb(args, data_in=None, timeout=None, error=None, overrides=None):
    """
    Execute the pwb.py script and capture outputs.

    :param args: list of arguments for pwb.py
    :type args: typing.Sequence[str]
    :param overrides: mapping of pywikibot symbols to test replacements
    :type overrides: dict
    """
    command = [sys.executable]

    if overrides:
        command.append('-c')
        overrides = '; '.join(
            f'{key} = {value}' for key, value in overrides.items())
        command.append(
            'import pwb; import pywikibot; {}; pwb.main()'
            .format(overrides))
    else:
        command.append(_pwb_py)

    return execute(command=command + args,
                   data_in=data_in, timeout=timeout, error=error)


@contextmanager
def empty_sites():
    """Empty pywikibot _sites and _code_fam_from_url cache on entry point."""
    pywikibot._sites = {}
    pywikibot._code_fam_from_url.cache_clear()
    yield


@contextmanager
def skipping(*exceptions: BaseException, msg: Optional[str] = None):
    """Context manager to skip test on specified exceptions.

    For example Eventstreams raises ``NotImplementedError`` if no
    ``streams`` parameter was given. Skip the following tests in that
    case::

        with skipping(NotImplementedError):
            self.es = comms.eventstreams.EventStreams(streams=None)
        self.assertIsInstance(self.es, tools.collections.GeneratorWrapper)

    The exception message is used for the ``SkipTest`` reason. To use a
    custom message, add a ``msg`` parameter::

        with skipping(AssertionError, msg='T304786'):
            self.assertEqual(self.get_mainpage().oldest_revision.text, text)

    Multiple context expressions may also be used::

        with (
            skipping(OtherPageSaveError),
            self.assertRaisesRegex(SpamblacklistError, 'badsite.com'),
        ):
            page.save()

    .. note:: The last sample uses Python 3.10 syntax.

    .. versionadded:: 6.2

    :param msg: Optional skipping reason
    :param exceptions: Exceptions to let test skip
    """
    try:
        yield
    except exceptions as e:
        if msg is None:
            msg = e
        raise unittest.SkipTest(msg)
