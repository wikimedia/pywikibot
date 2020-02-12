# -*- coding: utf-8 -*-
"""Test utilities."""
#
# (C) Pywikibot team, 2013-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from contextlib import contextmanager
import inspect
import json
import os
from subprocess import PIPE, Popen
import sys
import warnings

try:
    from collections.abc import Mapping
except ImportError:  # Python 2.7
    from collections import Mapping
    from multiprocessing import TimeoutError
    from threading import Timer
from types import ModuleType

try:
    from cryptography import __version__ as cryptography_version
    cryptography_version = list(map(int, cryptography_version.split('.')))
except ImportError:
    cryptography_version = None

import pywikibot
from pywikibot.comms import threadedhttp
from pywikibot import config
from pywikibot.data.api import CachedRequest, APIError
from pywikibot.data.api import Request as _original_Request
from pywikibot.site import Namespace
from pywikibot.tools import (
    PY2, PYTHON_VERSION,
    UnicodeType as unicode,
)
from tests import _pwb_py, unittest

if not PY2:
    import six
else:
    ResourceWarning = None


OSWIN32 = (sys.platform == 'win32')


class DrySiteNote(RuntimeWarning):

    """Information regarding dry site."""

    pass


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


def add_metaclass(cls):
    """Call six's add_metaclass with the site's __metaclass__ in Python 3."""
    if not PY2:
        return six.add_metaclass(cls.__metaclass__)(cls)
    else:
        assert cls.__metaclass__
        return cls


def fixed_generator(iterable):
    """Return a dummy generator ignoring all parameters."""
    def gen(*args, **kwargs):
        for item in iterable:
            yield item

    return gen


def entered_loop(iterable):
    """Return True if iterable contains items."""
    for iterable_item in iterable:
        return True
    return False


class FakeModule(ModuleType):

    """An empty fake module."""

    @classmethod
    def create_dotted(cls, name):
        """Create a chain of modules based on the name separated by periods."""
        modules = name.split('.')
        mod = None
        for mod_name in modules[::-1]:
            module = cls(str(mod_name))
            if mod:
                setattr(module, mod.__name__, mod)
            mod = module
        return mod


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

        @param skip_list: List of objects to be skipped. The source of any
            warning that matches the skip_list won't be adjusted.
        @type skip_list: list of object or (obj, str, int, int)
        """
        super(WarningSourceSkipContextManager, self).__init__(record=True)
        self.skip_list = skip_list

    @property
    def skip_list(self):
        """
        Return list of filename and line ranges to skip.

        @rtype: list of (obj, str, int, int)
        """
        return self._skip_list

    @skip_list.setter
    def skip_list(self, value):
        """
        Set list of objects to be skipped.

        @param value: List of objects to be skipped
        @type value: list of object or (obj, str, int, int)
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
            for (_, frame_filename, frame_lineno, _, _, _) in inspect.stack():
                if any(start <= frame_lineno <= end
                       for (_, skip_filename, start, end) in self.skip_list
                       if skip_filename == frame_filename):
                    # this frame matches to one of the items in the skip_list
                    if a_frame_has_matched_warn_msg:
                        continue
                    else:
                        skip_frames += 1

                if (
                    frame_filename == warn_msg.filename
                    and frame_lineno == warn_msg.lineno
                ):
                    if not skip_frames:
                        break
                    a_frame_has_matched_warn_msg = True

                if a_frame_has_matched_warn_msg:
                    if not skip_frames:
                        # adjust the warn_msg
                        warn_msg.filename = frame_filename
                        warn_msg.lineno = frame_lineno
                        break
                    else:
                        skip_frames -= 1

            # Ignore socket IO warnings (T183696, T184996)
            if (not PY2
                    and issubclass(warn_msg.category, ResourceWarning)
                    and str(warn_msg.message).startswith(
                        ('unclosed <ssl.SSLSocket',
                         'unclosed <socket.socket'))):
                return

            log.append(warn_msg)

        log = super(WarningSourceSkipContextManager, self).__enter__()
        self._module.showwarning = detailed_show_warning
        return log


class AssertAPIErrorContextManager(object):

    """
    Context manager to assert certain APIError exceptions.

    This is build similar to the L{unittest.TestCase.assertError}
    implementation which creates an context manager. It then calls L{handle}
    which either returns this manager if no executing object given or calls
    the callable object.
    """

    def __init__(self, code, info, msg, test_case):
        """Create instance expecting the code and info."""
        self.code = code
        self.info = info
        self.msg = msg
        self.test_case = test_case

    def __enter__(self):
        """Enter this context manager and the unittest's context manager."""
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


class DryParamInfo(dict):

    """Dummy class to use instead of L{pywikibot.data.api.ParamInfo}."""

    def __init__(self, *args, **kwargs):
        """Initializer."""
        super(DryParamInfo, self).__init__(*args, **kwargs)
        self.modules = set()
        self.action_modules = set()
        self.query_modules = set()
        self.query_modules_with_limits = set()
        self.prefixes = set()

    def fetch(self, modules, _init=False):
        """Load dry data."""
        return [self[mod] for mod in modules]

    def parameter(self, module, param_name):
        """Load dry data."""
        return self[module].get(param_name)

    def __getitem__(self, name):
        """Return dry data or a dummy parameter block."""
        try:
            return super(DryParamInfo, self).__getitem__(name)
        except KeyError:
            return {'name': name, 'limit': None}


class DummySiteinfo(object):

    """Dummy class to use instead of L{pywikibot.site.Siteinfo}."""

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
        """Return False."""
        return False

    def is_recognised(self, key):
        """Return None."""
        return None

    def get_requested_time(self, key):
        """Return False."""
        return False


class DryRequest(CachedRequest):

    """Dummy class to use instead of L{pywikibot.data.api.Request}."""

    def __init__(self, *args, **kwargs):
        """Initializer."""
        _original_Request.__init__(self, *args, **kwargs)

    @classmethod
    def create_simple(cls, **kwargs):
        """Skip CachedRequest implementation."""
        return _original_Request.create_simple(**kwargs)

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

    """Dummy class to use instead of L{pywikibot.site.APISite}."""

    _loginstatus = pywikibot.site.LoginStatus.NOT_ATTEMPTED

    def __init__(self, code, fam, user):
        """Initializer."""
        super(DrySite, self).__init__(code, fam, user)
        self._userinfo = pywikibot.tools.EMPTY_DEFAULT
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


class DryDataSite(DrySite, pywikibot.site.DataSite):

    """Dummy class to use instead of L{pywikibot.site.DataSite}."""

    def _build_namespaces(self):
        namespaces = super(DryDataSite, self)._build_namespaces()
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

    def isDisambig(self):
        """Return disambig status stored in _disambig."""
        return self._disambig


class FakeLoginManager(pywikibot.data.api.LoginManager):

    """Loads a fake password."""

    @property
    def password(self):
        """Get the fake password."""
        return 'foo'

    @password.setter
    def password(self, value):
        """Ignore password changes."""
        pass


class DummyHttp(object):

    """A class simulating the http module."""

    def __init__(self, wrapper):
        """Initializer with the given PatchedHttp instance."""
        self.__wrapper = wrapper

    def request(self, *args, **kwargs):
        """The patched request method."""
        result = self.__wrapper.before_request(*args, **kwargs)
        if result is False:
            result = self.__wrapper._old_http.request(*args, **kwargs)
        elif isinstance(result, Mapping):
            result = json.dumps(result)
        elif not isinstance(result, unicode):
            raise ValueError('The result is not a valid type '
                             '"{0}"'.format(type(result)))
        response = self.__wrapper.after_request(result, *args, **kwargs)
        if response is None:
            response = result
        return response

    def fetch(self, *args, **kwargs):
        """The patched fetch method."""
        result = self.__wrapper.before_fetch(*args, **kwargs)
        if result is False:
            result = self.__wrapper._old_http.fetch(*args, **kwargs)
        elif not isinstance(result, threadedhttp.HttpRequest):
            raise ValueError('The result is not a valid type '
                             '"{0}"'.format(type(result)))
        response = self.__wrapper.after_fetch(result, *args, **kwargs)
        if response is None:
            response = result
        return response


class PatchedHttp(object):

    """
    A ContextWrapper to handle any data going through the http module.

    This patches the C{http} import in the given module to a class simulating
    C{request} and C{fetch}. It has a C{data} attribute which is either a
    static value which the requests will return or it's a callable returning
    the data. If it's a callable it'll be called with the same parameters as
    the original function in the L{http} module. For fine grained control it's
    possible to override/monkey patch the C{before_request} and C{before_fetch}
    methods. By default they just return C{data} directory or call it if it's
    callable.

    Even though L{http.request} is calling L{http.fetch}, it won't call the
    patched method.

    The data returned for C{request} may either be C{False}, a C{unicode} or a
    C{Mapping} which is converted into a json string. The data returned for
    C{fetch} can only be C{False} or a L{threadedhttp.HttpRequest}. For both
    variants any other types are not allowed and if it is False it'll use the
    original method and do an actual request.

    Afterwards it is always calling C{after_request} or C{after_fetch} with the
    response and given arguments. That can return a different response too, but
    can also return None so that the original response is forwarded.
    """

    def __init__(self, module, data=None):
        """
        Initializer.

        @param module: The given module to patch. It must have the http module
            imported as http.
        @type module: Module
        @param data: The data returned for any request or fetch.
        @type data: callable or False (or other depending on request/fetch)
        """
        super(PatchedHttp, self).__init__()
        self._module = module
        self.data = data

    def _handle_data(self, *args, **kwargs):
        """Return the data after it may have been called."""
        if self.data is None:
            raise ValueError('No handler is defined.')
        elif callable(self.data):
            return self.data(*args, **kwargs)
        else:
            return self.data

    def before_request(self, *args, **kwargs):
        """Return the value which should is returned by request."""
        return self._handle_data(*args, **kwargs)

    def before_fetch(self, *args, **kwargs):
        """Return the value which should is returned by fetch."""
        return self._handle_data(*args, **kwargs)

    def after_request(self, response, *args, **kwargs):
        """Handle the response after request."""
        pass

    def after_fetch(self, response, *args, **kwargs):
        """Handle the response after fetch."""
        pass

    def __enter__(self):
        """Patch the http module property."""
        self._old_http = self._module.http
        self._module.http = DummyHttp(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Reset the http module property."""
        self._module.http = self._old_http


def execute(command, data_in=None, timeout=None, error=None):
    """
    Execute a command and capture outputs.

    @param command: executable to run and arguments to use
    @type command: list of unicode
    """
    if PY2 or PYTHON_VERSION < (3, 5, 0):
        command.insert(1, '-W ignore::FutureWarning:pywikibot:128')
    if cryptography_version and cryptography_version < [1, 3, 4]:
        command.insert(1, '-W ignore:Old version of cryptography:Warning')
    # Any environment variables added on Windows must be of type
    # str() on Python 2.
    if OSWIN32 and PY2:
        env = {str(k): str(v) for k, v in os.environ.items()}
    else:
        env = os.environ.copy()

    # Prevent output by test package; e.g. 'max_retries reduced from x to y'
    env[str('PYWIKIBOT_TEST_QUIET')] = str('1')

    # sys.path may have been modified by the test runner to load dependencies.
    pythonpath = os.pathsep.join(sys.path)
    if OSWIN32 and PY2:
        pythonpath = str(pythonpath)
    env[str('PYTHONPATH')] = pythonpath
    env[str('PYTHONIOENCODING')] = str(config.console_encoding)

    # PYWIKIBOT_USERINTERFACE_LANG will be assigned to
    # config.userinterface_lang
    if pywikibot.config.userinterface_lang:
        env[str('PYWIKIBOT_USERINTERFACE_LANG')] = \
            str(pywikibot.config.userinterface_lang)

    # Set EDITOR to an executable that ignores all arguments and does nothing.
    env[str('EDITOR')] = str('call' if OSWIN32 else 'true')
    try:
        p = Popen(
            command, env=env, stdout=PIPE, stderr=PIPE,
            stdin=PIPE if data_in is not None else None)
    except TypeError as e:
        # Generate a more informative error
        if OSWIN32 and PY2:
            unicode_env = [(k, v) for k, v in os.environ.items()
                           if not isinstance(k, str)
                           or not isinstance(v, str)]
            if unicode_env:
                raise TypeError(
                    '{}: unicode in os.environ: {!r}'.format(e, unicode_env))

            child_unicode_env = [(k, v) for k, v in env.items()
                                 if not isinstance(k, str)
                                 or not isinstance(v, str)]
            if child_unicode_env:
                raise TypeError(
                    '{}: unicode in child env: {!r}'
                    .format(e, child_unicode_env))
        raise

    if data_in is not None:
        p.stdin.write(data_in.encode(config.console_encoding))
        p.stdin.flush()  # _communicate() otherwise has a broken pipe

    if PY2:   # subprocess.communicate does not support timeout
        def timeout_handler():
            p.kill()
            raise TimeoutError

        timer = Timer(timeout, timeout_handler)
        timer.start()
        try:
            stdout_data, stderr_data = p.communicate()
        finally:
            timer.cancel()
    else:
        stdout_data, stderr_data = p.communicate(timeout=timeout)
    return {'exit_code': p.returncode,
            'stdout': stdout_data.decode(config.console_encoding),
            'stderr': stderr_data.decode(config.console_encoding)}


def execute_pwb(args, data_in=None, timeout=None, error=None, overrides=None):
    """
    Execute the pwb.py script and capture outputs.

    @param args: list of arguments for pwb.py
    @type args: typing.Sequence[unicode]
    @param overrides: mapping of pywikibot symbols to test replacements
    @type overrides: dict
    """
    command = [sys.executable]

    if overrides:
        command.append('-c')
        overrides = '; '.join(
            '{} = {}'.format(key, value) for key, value in overrides.items())
        command.append(
            'import pwb; import pywikibot; {}; pwb.main()'
            .format(overrides))
    else:
        command.append(_pwb_py)

    return execute(command=command + args,
                   data_in=data_in, timeout=timeout, error=error)


@contextmanager
def empty_sites():
    """Empty pywikibot._sites and pywikibot._url_cache cache on entry point."""
    pywikibot._sites = {}
    pywikibot._url_cache = {}
    yield
