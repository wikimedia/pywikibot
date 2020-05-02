# -*- coding: utf-8 -*-
"""Interface to Mediawiki's api.php."""
#
# (C) Pywikibot team, 2007-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import datetime
import hashlib
import inspect
import json
import os
import pprint
import re
import traceback

try:
    from collections.abc import Container, MutableMapping
except ImportError:  # Python 2.7
    from collections import Container, MutableMapping
from email.mime.nonmultipart import MIMENonMultipart
from warnings import warn

try:
    import cPickle as pickle  # noqa: N813
except ImportError:
    import pickle

import pywikibot

from pywikibot import config, login

from pywikibot.comms import http
from pywikibot.exceptions import (
    Server504Error, Server414Error, FatalServerError, NoUsername,
    Error, TimeoutError, MaxlagTimeoutError, InvalidTitle, UnsupportedPage
)
from pywikibot.family import SubdomainFamily
from pywikibot.tools import (
    deprecated, itergroup, PY2, PYTHON_VERSION,
    getargspec, UnicodeType, remove_last_args
)
from pywikibot.tools.formatter import color_format

if not PY2:
    from urllib.parse import urlencode, unquote

    # Bug: T113120, T228841
    # Subclassing necessary to fix bug of the email package in Python 3:
    # see https://bugs.python.org/issue19003
    # see https://bugs.python.org/issue18886
    # The following solution might be removed if the bug is fixed for
    # Python versions which are supported by PWB.

    from email.generator import BytesGenerator
    from email.mime.multipart import MIMEMultipart as MIMEMultipartOrig
    from io import BytesIO

    class CTEBinaryBytesGenerator(BytesGenerator):

        """Workaround for bug in python 3 email handling of CTE binary."""

        def __init__(self, *args, **kwargs):
            """Initializer."""
            super(CTEBinaryBytesGenerator, self).__init__(*args, **kwargs)
            self._writeBody = self._write_body

        def _write_body(self, msg):
            if msg['content-transfer-encoding'] == 'binary':
                self._fp.write(msg.get_payload(decode=True))
            else:
                super(CTEBinaryBytesGenerator, self)._handle_text(msg)

    class CTEBinaryMIMEMultipart(MIMEMultipartOrig):

        """Workaround for bug in python 3 email handling of CTE binary."""

        def as_bytes(self, unixfrom=False, policy=None):
            """Return unmodified binary payload."""
            policy = self.policy if policy is None else policy
            fp = BytesIO()
            g = CTEBinaryBytesGenerator(fp, mangle_from_=False, policy=policy)
            g.flatten(self, unixfrom=unixfrom)
            return fp.getvalue()

    MIMEMultipart = CTEBinaryMIMEMultipart
else:
    from urllib import urlencode, unquote
    from email.mime.multipart import MIMEMultipart

    # Bug: T243710 (Python 2)
    # see https://github.com/jxtech/wechatpy/issues/375
    from urllib import quote
    quote(b'non-empty-string', safe=b'')


_logger = 'data.api'

lagpattern = re.compile(
    r'Waiting for [\w.: ]+: (?P<lag>\d+(?:\.\d+)?) seconds? lagged')


def _invalidate_superior_cookies(family):
    """
    Clear cookies for site's second level domain.

    get_login_token() will generate new cookies needed.
    This is a workaround for requests bug, see T224712
    and https://github.com/psf/requests/issues/5411
    for more details.
    """
    if isinstance(family, SubdomainFamily):
        for cookie in http.cookie_jar:
            if family.domain == cookie.domain:
                http.cookie_jar.clear(cookie.domain, cookie.path, cookie.name)


class APIError(Error):

    """The wiki site returned an error message."""

    def __init__(self, code, info, **kwargs):
        """Save error dict returned by MW API."""
        self.code = code
        self.info = info
        self.other = kwargs
        self.unicode = UnicodeType(self.__str__())

    def __repr__(self):
        """Return internal representation."""
        return '{name}("{code}", "{info}", {other})'.format(
            name=self.__class__.__name__, **self.__dict__)

    def __str__(self):
        """Return a string representation."""
        if self.other:
            return '{0}: {1}\n[{2}]'.format(
                self.code,
                self.info,
                ';\n '.join(
                    '{0}: {1}'.format(key, val)
                    for key, val in self.other.items()))

        return '{0}: {1}'.format(self.code, self.info)


class UploadWarning(APIError):

    """Upload failed with a warning message (passed as the argument)."""

    def __init__(self, code, message, file_key=None, offset=0):
        """
        Create a new UploadWarning instance.

        @param filekey: The filekey of the uploaded file to reuse it later. If
            no key is known or it is an incomplete file it may be None.
        @type filekey: str or None
        @param offset: The starting offset for a chunked upload. Is False when
            there is no offset.
        @type offset: int or bool
        """
        super(UploadWarning, self).__init__(code, message)
        self.file_key = file_key
        self.offset = offset

    @property
    def message(self):
        """Return warning message."""
        return self.info


class APIMWException(APIError):

    """The API site returned an error about a MediaWiki internal exception."""

    def __init__(self, mediawiki_exception_class_name, info, **kwargs):
        """Save error dict returned by MW API."""
        self.mediawiki_exception_class_name = mediawiki_exception_class_name
        code = 'internal_api_error_' + mediawiki_exception_class_name
        super(APIMWException, self).__init__(code, info, **kwargs)


class ParamInfo(Container):

    """
    API parameter information data object.

    Provides cache aware fetching of parameter information.

    It does not support the format modules.
    """

    paraminfo_keys = frozenset(['modules', 'querymodules', 'formatmodules',
                                'mainmodule', 'pagesetmodule'])

    root_modules = frozenset(['main', 'pageset'])

    init_modules = frozenset(['main', 'paraminfo'])

    def __init__(self, site, preloaded_modules=None, modules_only_mode=None):
        """
        Initializer.

        @param preloaded_modules: API modules to preload
        @type preloaded_modules: set of string
        @param modules_only_mode: use the 'modules' only syntax for API request
        @type modules_only_mode: bool or None to only use default, which True
            if the site is 1.25wmf4+
        """
        self.site = site

        # Keys are module names, values are the raw responses from the server.
        self._paraminfo = {}

        # Cached data.
        self._prefixes = {}
        self._prefix_map = {}
        self._with_limits = None

        self._action_modules = frozenset()  # top level modules
        self._modules = {}  # filled in _init() (and enlarged in fetch)
        self._limit = None

        self.preloaded_modules = self.init_modules
        if preloaded_modules:
            self.preloaded_modules |= set(preloaded_modules)

        self.modules_only_mode = modules_only_mode
        if self.modules_only_mode:
            self.paraminfo_keys = frozenset(['modules'])

    def _add_submodules(self, name, modules):
        """Add the modules to the internal cache or check if equal."""
        # The current implementation here doesn't support submodules inside of
        # submodules, because that would require to fetch all modules when only
        # the names of them were requested
        assert '+' not in name
        modules = frozenset(modules)
        if name == 'main':
            # The main module behaves differently as it has no prefix
            if self._action_modules:
                assert modules == self._action_modules
            else:
                self._action_modules = modules
        elif name in self._modules:
            assert modules == self._modules[name]
        else:
            self._modules[name] = modules

    def _init(self):
        assert ('query' in self._modules) is ('main' in self._paraminfo)
        if 'query' in self._modules:
            return
        mw_ver = self.site.mw_version

        if mw_ver < '1.15':
            self._parse_help()

        # The paraminfo api deprecated the old request syntax of
        # querymodules='info'; to avoid warnings sites with 1.25wmf4+
        # must only use 'modules' parameter.
        if self.modules_only_mode is None:
            self.modules_only_mode = mw_ver >= '1.25wmf4'
            if self.modules_only_mode:
                self.paraminfo_keys = frozenset(['modules'])

        # v1.18 and earlier paraminfo doesn't include modules; must use 'query'
        # Assume that by v1.26, it will be desirable to prefetch 'query'
        if mw_ver > '1.26' or mw_ver < '1.19':
            self.preloaded_modules |= {'query'}

        self._fetch(self.preloaded_modules)

        # paraminfo 'mainmodule' was added 1.15
        assert('main' in self._paraminfo)
        main_modules_param = self.parameter('main', 'action')

        assert(main_modules_param)
        assert('type' in main_modules_param)
        assert(isinstance(main_modules_param['type'], list))
        assert self._action_modules == set(main_modules_param['type'])

        # While deprecated with warning in 1.25, paraminfo param 'querymodules'
        # provides a list of all query modules. This will likely be removed
        # from the API in the future, in which case the fallback is the use
        # the same data available in the paraminfo for query.
        query_modules_param = self.parameter('paraminfo', 'querymodules')

        assert('limit' in query_modules_param)
        self._limit = query_modules_param['limit']

        if query_modules_param and 'type' in query_modules_param:
            # 1.19+ 'type' is the list of modules; on 1.18, it is 'string'
            if isinstance(query_modules_param['type'], list):
                self._add_submodules('query', query_modules_param['type'])

        if 'query' not in self._modules:
            assert 'query' not in self._paraminfo
            self._fetch({'query'})
        assert 'query' in self._modules

    def _emulate_pageset(self):
        """Emulate the pageset module, which existed in MW 1.15-1.24."""
        # pageset isn't a module in the new system, so it is emulated, with
        # the paraminfo from the query module.
        assert('query' in self._paraminfo)

        self._paraminfo['pageset'] = {
            'name': 'pageset',
            'path': 'pageset',
            'classname': 'ApiPageSet',
            'prefix': '',
            'readrights': '',
            'helpurls': [],
            'parameters': self._paraminfo['query']['parameters']
        }

    def _parse_help(self):
        """Emulate paraminfo['main'] data using help for mw 1.14."""
        # Request need ParamInfo to determine use_get
        request = self.site._request(expiry=config.API_config_expiry,
                                     use_get=True,
                                     parameters={'action': 'help'})
        result = request.submit()

        assert('help' in result)
        assert(isinstance(result['help'], dict))
        assert('mime' in result['help'])
        assert(result['help']['mime'] == 'text/plain')
        assert('help' in result['help'])
        assert(isinstance(result['help']['help'], UnicodeType))

        help_text = result['help']['help']

        start = help_text.find('What action you would like to perform')
        start = help_text.find('One value: ', start) + len('One value: ')
        end = help_text.find('\n', start)

        action_modules = help_text[start:end].split(', ')

        start = help_text.find('The format of the output')
        start = help_text.find('One value: ', start) + len('One value: ')
        end = help_text.find('\n', start)

        format_modules = help_text[start:end].split(', ')

        self._paraminfo['main'] = {
            'name': 'main',
            'path': 'main',
            'classname': 'ApiMain',
            'prefix': '',
            'readrights': '',
            'helpurls': [],
            'parameters': [
                {
                    'name': 'action',
                    'type': action_modules,
                    'submodules': '',
                },
                {
                    'name': 'format',
                    'type': format_modules,
                    'submodules': '',
                },
            ],
        }

    @staticmethod
    def _modules_to_set(modules):
        """Return modules as a set.

        @type modules: iterable or basestring
        @rtype: set
        """
        if isinstance(modules, UnicodeType):
            return set(modules.split('|'))
        return set(modules)

    def fetch(self, modules):
        """
        Fetch paraminfo for multiple modules.

        No exception is raised when paraminfo for a module does not exist.
        Use __getitem__ to cause an exception if a module does not exist.

        @param modules: API modules to load
        @type modules: iterable or str
        @rtype: NoneType
        """
        if 'main' not in self._paraminfo:
            # The first request should be 'paraminfo', so that
            # query modules can be prefixed with 'query+'
            self._init()

        modules = self._modules_to_set(modules)

        if self._action_modules:
            # The query module may be added before the action modules have been
            if 'query' in self._modules:
                # It does fetch() while initializing, and this method can't be
                # called before it's initialized.
                modules = self._normalize_modules(modules)
            else:
                # We do know the valid action modules and require a subset
                assert not modules - self._action_modules - self.root_modules

        self._fetch(modules)

    def _fetch(self, modules):
        """
        Fetch paraminfo for multiple modules without initializing beforehand.

        @param modules: API modules to load and which haven't been loaded yet.
        @type modules: set
        @rtype: NoneType
        """
        def module_generator():
            """A generator yielding batches of modules."""
            i = itergroup(sorted(modules), self._limit)
            for batch in i:
                for failed_module in failed_modules:
                    yield [failed_module]
                del failed_modules[:]
                yield batch

        modules = modules - set(self._paraminfo.keys())
        if not modules:
            return

        assert 'query' in self._modules or 'paraminfo' not in self._paraminfo

        # If something went wrong in a batch it can add each module to the
        # batch and the generator will on the next iteration yield each module
        # separately
        failed_modules = []

        # This can be further optimised, by grouping them in more stable
        # subsets, which are unlikely to change. i.e. first request core
        # modules which have been a stable part of the API for a long time.
        # Also detecting extension based modules may help.
        # Also, when self.modules_only_mode is disabled, both modules and
        # querymodules may each be filled with self._limit items, doubling the
        # number of modules that may be processed in a single batch.
        for module_batch in module_generator():
            if self.modules_only_mode and 'pageset' in module_batch:
                pywikibot.debug('paraminfo fetch: removed pageset', _logger)
                module_batch.remove('pageset')
                # If this occurred during initialisation,
                # also record it in the preloaded_modules.
                # (at least so tests know an extra load was intentional)
                if 'query' not in self._paraminfo:
                    pywikibot.debug('paraminfo batch: added query', _logger)
                    module_batch.append('query')
                    self.preloaded_modules |= {'query'}

            params = {
                'action': 'paraminfo',
            }

            if self.modules_only_mode:
                params['modules'] = module_batch
            else:
                params['modules'] = [mod for mod in module_batch
                                     if not mod.startswith('query+')
                                     and mod not in self.root_modules]
                params['querymodules'] = [mod[6:] for mod in module_batch
                                          if mod.startswith('query+')]

                for mod in set(module_batch) & self.root_modules:
                    params[mod + 'module'] = 1

            # Request need ParamInfo to determine use_get
            request = self.site._request(expiry=config.API_config_expiry,
                                         use_get=True,
                                         parameters=params)
            result = request.submit()

            normalized_result = self.normalize_paraminfo(result)
            for path in list(normalized_result):
                if normalized_result[path] is False:
                    del normalized_result[path]

            # Sometimes the name/path of the module is not actually the name
            # which was requested, so we need to manually determine which
            # (wrongly named) module uses which actual name. See also T105478
            missing_modules = [m for m in module_batch
                               if m not in normalized_result]
            if len(missing_modules) == 1 and len(normalized_result) == 1:
                # Okay it's possible to recover
                normalized_result = next(iter(normalized_result.values()))
                pywikibot.warning('The module "{0[name]}" ("{0[path]}") '
                                  'was returned as path even though "{1}" '
                                  'was requested'.format(normalized_result,
                                                         missing_modules[0]))
                normalized_result['path'] = missing_modules[0]
                normalized_result['name'] = missing_modules[0].rsplit('+')[0]
                normalized_result = {missing_modules[0]: normalized_result}
            elif len(module_batch) > 1 and missing_modules:
                # Rerequest the missing ones separately
                pywikibot.log('Inconsitency in batch "{0}"; rerequest '
                              'separately'.format(missing_modules))
                failed_modules.extend(missing_modules)

            # Remove all modules which weren't requested, we can't be sure that
            # they are valid
            for path in list(normalized_result):
                if path not in module_batch:
                    del normalized_result[path]

            self._paraminfo.update(normalized_result)
            self._generate_submodules(mod['path']
                                      for mod in normalized_result.values())

        if 'pageset' in modules and 'pageset' not in self._paraminfo:
            self._emulate_pageset()

    def _generate_submodules(self, modules):
        """Check and generate submodules for the given modules."""
        for module in modules:
            parameters = self._paraminfo[module].get('parameters', [])
            submodules = set()
            # Advanced submodule into added to MW API in df80f1ea
            if self.site.mw_version >= '1.26wmf9':
                # This is supplying submodules even if they aren't submodules
                # of the given module so skip those
                for param in parameters:
                    if ((module == 'main' and param['name'] == 'format')
                            or 'submodules' not in param):
                        continue
                    for submodule in param['submodules'].values():
                        if '+' in submodule:
                            parent, child = submodule.rsplit('+', 1)
                        else:
                            parent = 'main'
                            child = submodule
                        if parent == module:
                            submodules.add(child)
            else:
                # Boolean submodule info added to MW API in afa153ae
                if self.site.mw_version < '1.24wmf18':
                    if module == 'main':
                        params = {'action'}
                    elif module == 'query':
                        params = {'prop', 'list', 'meta'}
                    else:
                        params = set()
                    for param in parameters:
                        if param['name'] in params:
                            param['submodules'] = ''

                for param in parameters:
                    # Do not add format modules
                    if ('submodules' in param
                        and (module != 'main'
                             or param['name'] != 'format')):
                        submodules |= set(param['type'])

            if submodules:
                self._add_submodules(module, submodules)
            if module == 'query':
                # Previously also modules from generator were used as query
                # modules, but verify that those are just a subset of the
                # prop/list/meta modules. There is no sanity check as this
                # needs to be revisited if query has no generator parameter
                for param in parameters:
                    if param['name'] == 'generator':
                        break
                assert param['name'] == 'generator' and \
                    submodules >= set(param['type'])

    def _normalize_modules(self, modules):
        """Add query+ to any query module name not also in action modules."""
        # Users will supply the wrong type, and expect it to work.
        modules = self._modules_to_set(modules)

        assert(self._action_modules)

        return {'query+' + mod
                if '+' not in mod and mod in self.query_modules
                and mod not in self._action_modules
                else mod
                for mod in modules}

    def normalize_modules(self, modules):
        """
        Convert the modules into module paths.

        Add query+ to any query module name not also in action modules.

        @return: The modules converted into a module paths
        @rtype: set
        """
        self._init()
        return self._normalize_modules(modules)

    @classmethod
    def normalize_paraminfo(cls, data):
        """
        Convert both old and new API JSON into a new-ish data structure.

        For duplicate paths, the value will be False.
        """
        result_data = {}
        for paraminfo_key, modules_data in data['paraminfo'].items():
            if not modules_data:
                continue

            if paraminfo_key[:-len('module')] in cls.root_modules:
                modules_data = [modules_data]
            elif not paraminfo_key.endswith('modules'):
                continue

            for mod_data in modules_data:
                if 'missing' in mod_data:
                    continue

                name = mod_data.get('name')
                php_class = mod_data.get('classname')

                if not name and php_class:
                    if php_class == 'ApiMain':
                        name = 'main'
                    elif php_class == 'ApiPageSet':
                        name = 'pageset'
                    else:
                        pywikibot.warning('Unknown paraminfo module "{0}"'
                                          .format(php_class))
                        name = '<unknown>:' + php_class

                    mod_data['name'] = name

                if 'path' not in mod_data:
                    # query modules often contain 'ApiQuery' and have a suffix.
                    # 'ApiQuery' alone is the action 'query'
                    if ('querytype' in mod_data
                        or php_class and len(php_class) > 8
                            and 'ApiQuery' in php_class):
                        mod_data['path'] = 'query+' + name
                    else:
                        mod_data['path'] = name

                path = mod_data['path']

                if path in result_data:
                    # Only warn first time
                    if result_data[path] is not False:
                        pywikibot.warning('Path "{0}" is ambiguous.'
                                          .format(path))
                    else:
                        pywikibot.log('Found another path "{0}"'.format(path))
                    result_data[path] = False
                else:
                    result_data[path] = mod_data

        return result_data

    def __getitem__(self, key):
        """
        Return a paraminfo module for the module path, caching it.

        Use the module path, such as 'query+x', to obtain the paraminfo for
        submodule 'x' in the query module.

        If the key does not include a '+' and is not present in the top level
        of the API, it will fallback to looking for the key 'query+x'.
        """
        self.fetch({key})
        if key in self._paraminfo:
            return self._paraminfo[key]
        elif '+' not in key:
            return self._paraminfo['query+' + key]
        else:
            raise KeyError(key)

    def __contains__(self, key):
        """Return whether the key is valid."""
        try:
            self[key]
            return True
        except KeyError:
            return False

    def __len__(self):
        """Return number of cached modules."""
        return len(self._paraminfo)

    def parameter(self, module, param_name):
        """
        Get details about one modules parameter.

        Returns None if the parameter does not exist.

        @param module: API module name
        @type module: str
        @param param_name: parameter name in the module
        @type param_name: str
        @return: metadata that describes how the parameter may be used
        @rtype: dict or None
        """
        # TODO: the 'description' field of each parameter is not in the default
        # output of v1.25, and can't removed from previous API versions.
        # There should be an option to remove this verbose data from the cached
        # version, for earlier versions of the API, and/or extract any useful
        # data and discard the entire received paraminfo structure. There are
        # also params which are common to many modules, such as those provided
        # by the ApiPageSet php class: titles, pageids, redirects, etc.
        try:
            module = self[module]
        except KeyError:
            raise ValueError("paraminfo for '%s' not loaded" % module)

        try:
            params = module['parameters']
        except KeyError:
            pywikibot.warning("module '{}' has no parameters".format(module))
            return None

        param_data = [param for param in params
                      if param['name'] == param_name]

        if not param_data:
            return None

        assert(len(param_data) == 1)
        return param_data[0]

    @property
    @deprecated('submodules() or module_paths', since='20150715')
    def modules(self):
        """
        Set of all main and query modules without path prefixes.

        Modules with the same names will be only added once (e.g. 'tokens' from
        the action modules and query modules).

        @return: module names
        @rtype: set of str
        """
        return self.action_modules | self.query_modules

    @property
    def module_paths(self):
        """Set of all modules using their paths."""
        return self._module_set(True)

    # As soon as modules() is removed, module_paths and _module_set can be
    # combined, so don't add any code between these two methods.
    def _module_set(self, path):
        # Load the submodules of all action modules available
        self.fetch(self.action_modules)
        modules = set(self.action_modules)
        for parent_module in self._modules:
            submodules = self.submodules(parent_module, path)
            assert not submodules & modules or not path
            modules |= submodules
        return modules

    @property
    def action_modules(self):
        """Set of all action modules."""
        self._init()
        return self._action_modules

    @property
    def query_modules(self):
        """Set of all query module names without query+ path prefix."""
        return self.submodules('query')

    def submodules(self, name, path=False):
        """
        Set of all submodules.

        @param name: The name of the parent module.
        @type name: str
        @param path: Whether the path and not the name is returned.
        @type path: bool
        @return: The names or paths of the submodules.
        @rtype: set
        """
        if name not in self._modules:
            self.fetch([name])
        submodules = self._modules[name]
        if path:
            submodules = self._prefix_submodules(submodules, name)
        return submodules

    @staticmethod
    def _prefix_submodules(modules, prefix):
        """Prefix submodules with path."""
        return {'{0}+{1}'.format(prefix, mod) for mod in modules}

    @property
    @deprecated('prefix_map', since='20150715')
    def prefixes(self):
        """
        Mapping of module to its prefix for all modules with a prefix.

        This loads paraminfo for all modules.
        """
        if not self._prefixes:
            self._prefixes = self.module_attribute_map('prefix')
        return self._prefixes

    @property
    def prefix_map(self):
        """
        Mapping of module to its prefix for all modules with a prefix.

        This loads paraminfo for all modules.
        """
        if not self._prefix_map:
            self._prefix_map = {module: prefix
                                for module, prefix
                                in self.attributes('prefix').items()
                                if prefix}
        return self._prefix_map.copy()

    def attributes(self, attribute, modules=None):
        """
        Mapping of modules with an attribute to the attribute value.

        It will include all modules which have that attribute set, also if that
        attribute is empty or set to False.

        @param attribute: attribute name
        @type attribute: basestring
        @param modules: modules to include. If None (default), it'll load all
            modules including all submodules using the paths.
        @type modules: set or None
        @rtype: dict using modules as keys
        """
        if modules is None:
            modules = self.module_paths
        self.fetch(modules)

        return {mod: self[mod][attribute]
                for mod in modules if attribute in self[mod]}

    @deprecated('attributes', since='20150715')
    def module_attribute_map(self, attribute, modules=None):
        """
        Mapping of modules with an attribute to the attribute value.

        @param attribute: attribute name
        @type attribute: basestring
        @param modules: modules to include. If None (default) it'll load all
            action and query modules using the module names. It only uses the
            path for query modules which have the same name as an action
            module.
        @type modules: set
        @rtype: dict using modules as keys
        """
        if modules is None:
            modules = self.modules | self._prefix_submodules(
                self.query_modules & self.action_modules, 'query')

        self.fetch(modules)

        return {mod: self[mod][attribute]
                for mod in modules if self[mod][attribute]}

    @property
    @deprecated('parameter()', since='20150905')
    def query_modules_with_limits(self):
        """Set of all query modules which have limits."""
        if not self._with_limits:
            self.fetch(self.submodules('query', True))
            self._with_limits = frozenset(
                mod for mod in self.query_modules
                if self.parameter('query+' + mod, 'limit'))
        return self._with_limits


class OptionSet(MutableMapping):

    """
    A class to store a set of options which can be either enabled or not.

    If it is instantiated with the associated site, module and parameter it
    will only allow valid names as options. If instantiated 'lazy loaded' it
    won't checks if the names are valid until the site has been set (which
    isn't required, but recommended). The site can only be set once if it's not
    None and after setting it, any site (even None) will fail.
    """

    def __init__(self, site=None, module=None, param=None, dict=None):
        """
        Initializer.

        If a site is given, the module and param must be given too.

        @param site: The associated site
        @type site: piwikibot.site.APISite
        @param module: The module name which is used by paraminfo. (Ignored
            when site is None)
        @type module: str
        @param param: The parameter name inside the module. That parameter must
            have a 'type' entry. (Ignored when site is None)
        @type param: str
        @param dict: The initializing dict which is used for L{from_dict}.
        @type dict: dict
        """
        self._site_set = False
        self._enabled = set()
        self._disabled = set()
        self._set_site(site, module, param)
        if dict:
            self.from_dict(dict)

    def _set_site(self, site, module, param, clear_invalid=False):
        """
        Set the site and valid names.

        As soon as the site has been not None, any subsequent calls will fail,
        unless there had been invalid names and a KeyError was thrown.

        @param site: The associated site
        @type site: pywikibot.site.APISite
        @param module: The module name which is used by paraminfo.
        @type module: str
        @param param: The parameter name inside the module. That parameter must
            have a 'type' entry.
        @type param: str
        @param clear_invalid: Instead of throwing a KeyError, invalid names are
            silently removed from the options (disabled by default).
        @type clear_invalid: bool
        """
        if self._site_set:
            raise TypeError('The site can not be set multiple times.')
        # If the entries written to this are valid, it will never be
        # overwritten
        self._valid_enable = set()
        self._valid_disable = set()
        if site is None:
            return
        for type in site._paraminfo.parameter(module, param)['type']:
            if type[0] == '!':
                self._valid_disable.add(type[1:])
            else:
                self._valid_enable.add(type)
        if clear_invalid:
            self._enabled &= self._valid_enable
            self._disabled &= self._valid_disable
        else:
            invalid_names = ((self._enabled - self._valid_enable)
                             | (self._disabled - self._valid_disable))
            if invalid_names:
                raise KeyError('OptionSet already contains invalid name(s) '
                               '"{0}"'.format('", "'.join(invalid_names)))
        self._site_set = True

    def from_dict(self, dict):
        """
        Load options from the dict.

        The options are not cleared before. If changes have been made
        previously, but only the dict values should be applied it needs to be
        cleared first.

        @param dict: A dictionary containing for each entry either the value
            False, True or None. The names must be valid depending on whether
            they enable or disable the option. All names with the value None
            can be in either of the list.
        @type dict: dict (keys are strings, values are bool/None)
        """
        enabled = set()
        disabled = set()
        removed = set()
        for name, value in dict.items():
            if value is True:
                enabled.add(name)
            elif value is False:
                disabled.add(name)
            elif value is None:
                removed.add(name)
            else:
                raise ValueError('Dict contains invalid value "{0}"'.format(
                    value))
        invalid_names = (
            (enabled - self._valid_enable) | (disabled - self._valid_disable)
            | (removed - self._valid_enable - self._valid_disable)
        )
        if invalid_names and self._site_set:
            raise ValueError('Dict contains invalid name(s) "{0}"'.format(
                '", "'.join(invalid_names)))
        self._enabled = enabled | (self._enabled - disabled - removed)
        self._disabled = disabled | (self._disabled - enabled - removed)

    def clear(self):
        """Clear all enabled and disabled options."""
        self._enabled.clear()
        self._disabled.clear()

    def __setitem__(self, name, value):
        """Set option to enabled, disabled or neither."""
        if value is True:
            if self._site_set and name not in self._valid_enable:
                raise KeyError('Invalid name "{0}"'.format(name))
            self._enabled.add(name)
            self._disabled.discard(name)
        elif value is False:
            if self._site_set and name not in self._valid_disable:
                raise KeyError('Invalid name "{0}"'.format(name))
            self._disabled.add(name)
            self._enabled.discard(name)
        elif value is None:
            if self._site_set and (name not in self._valid_enable
                                   or name not in self._valid_disable):
                raise KeyError('Invalid name "{0}"'.format(name))
            self._enabled.discard(name)
            self._disabled.discard(name)
        else:
            raise ValueError('Invalid value "{0}"'.format(value))

    def __getitem__(self, name):
        """
        Return whether the option is enabled.

        @return: If the name has been set it returns whether it is enabled.
            Otherwise it returns None. If the site has been set it raises a
            KeyError if the name is invalid. Otherwise it might return a value
            even though the name might be invalid.
        @rtype: bool/None
        """
        if name in self._enabled:
            return True
        if name in self._disabled:
            return False
        if (self._site_set or name in self._valid_enable
                or name in self._valid_disable):
            return None
        raise KeyError('Invalid name "{0}"'.format(name))

    def __delitem__(self, name):
        """Remove the item by setting it to None."""
        self[name] = None

    def __contains__(self, name):
        """Return True if option has been set."""
        return name in self._enabled or name in self._disabled

    def __iter__(self):
        """Iterate over each enabled and disabled option."""
        for enabled in self._enabled:
            yield enabled
        for disabled in self._disabled:
            yield disabled

    def api_iter(self):
        """Iterate over each option as they appear in the URL."""
        for enabled in self._enabled:
            yield enabled
        for disabled in self._disabled:
            yield '!{0}'.format(disabled)

    def __len__(self):
        """Return the number of enabled and disabled options."""
        return len(self._enabled) + len(self._disabled)


class Request(MutableMapping):

    """A request to a Site's api.php interface.

    Attributes of this object (except for the special parameters listed
    below) get passed as commands to api.php, and can be get or set using
    the dict interface. All attributes must be strings (or unicode). Use
    an empty string for parameters that don't require a value. For example,
    Request(action="query", titles="Foo bar", prop="info", redirects="")
    corresponds to the API request
    "api.php?action=query&titles=Foo%20bar&prop=info&redirects"

    This is the lowest-level interface to the API, and can be used for any
    request that a particular site's API supports. See the API documentation
    (https://www.mediawiki.org/wiki/API) and site-specific settings for
    details on what parameters are accepted for each request type.

    Uploading files is a special case: to upload, the parameter "mime" must
    be true, and the parameter "file" must be set equal to a valid
    filename on the local computer, _not_ to the content of the file.

    Returns a dict containing the JSON data returned by the wiki. Normally,
    one of the dict keys will be equal to the value of the 'action'
    parameter. Errors are caught and raise an APIError exception.

    Example:

    >>> r = Request(parameters={'action': 'query', 'meta': 'userinfo'})
    >>> # This is equivalent to
    >>> # https://{path}/api.php?action=query&meta=userinfo&format=json
    >>> # change a parameter
    >>> r['meta'] = "userinfo|siteinfo"
    >>> # add a new parameter
    >>> r['siprop'] = "namespaces"
    >>> # note that "uiprop" param gets added automatically
    >>> str(r.action)
    'query'
    >>> sorted(str(key) for key in r._params.keys())
    ['action', 'meta', 'siprop']
    >>> [str(key) for key in r._params['action']]
    ['query']
    >>> [str(key) for key in r._params['meta']]
    ['userinfo', 'siteinfo']
    >>> [str(key) for key in r._params['siprop']]
    ['namespaces']
    >>> data = r.submit()
    >>> isinstance(data, dict)
    True
    >>> set(['query', 'batchcomplete', 'warnings']).issuperset(data.keys())
    True
    >>> 'query' in data
    True
    >>> sorted(str(key) for key in data['query'].keys())
    ['namespaces', 'userinfo']

    """

    # To make sure the default value of 'parameters' can be identified.
    _PARAM_DEFAULT = object()

    def __init__(self, site=None, mime=None, throttle=True, mime_params=None,
                 max_retries=None, retry_wait=None, use_get=None,
                 parameters=_PARAM_DEFAULT, **kwargs):
        """
        Create a new Request instance with the given parameters.

        The parameters for the request can be defined via either the
        'parameters' parameter or the keyword arguments. The keyword arguments
        were the previous implementation but could cause problems when there
        are arguments to the API named the same as normal arguments to this
        class. So the second parameter 'parameters' was added which just
        contains all parameters. When a Request instance is created it must use
        either one of them and not both at the same time. To have backwards
        compatibility it adds a parameter named 'parameters' to kwargs when
        both parameters are set as that indicates an old call and 'parameters'
        was originally supplied as a keyword parameter.

        If undefined keyword arguments were given AND the 'parameters'
        parameter was supplied as a positional parameter it still assumes
        'parameters' were part of the keyword arguments.

        If a class is using Request and is directly forwarding the parameters,
        L{Request.clean_kwargs} can be used to automatically convert the old
        kwargs mode into the new parameter mode. This normalizes the arguments
        so that when the API parameters are modified the changes can always be
        applied to the 'parameters' parameter.

        @param parameters: The parameters used for the request to the API.
        @type parameters: dict
        @param site: The Site to which the request will be submitted. If not
               supplied, uses the user's configured default Site.
        @param mime: If true, send in "multipart/form-data" format (default
               False). Parameters which should only be transferred via mime
               mode can be defined via that parameter too (an empty dict acts
               like 'True' not like 'False'!).
        @type mime: bool or dict
        @param mime_params: DEPRECATED! A dictionary of parameter which should
               only be transferred via mime mode. If not None sets mime to
               True.
        @param max_retries: (optional) Maximum number of times to retry after
               errors, defaults to config.max_retries.
        @param retry_wait: (optional) Minimum time in seconds to wait after an
               error, defaults to config.retry_wait seconds (doubles each retry
               until config.retry_max seconds is reached).
        @param use_get: (optional) Use HTTP GET request if possible. If False
               it uses a POST request. If None, it'll try to determine via
               action=paraminfo if the action requires a POST.
        @param kwargs: The parameters used for the request to the API.
        """
        if site is None:
            self.site = pywikibot.Site()
            warn('Request() invoked without a site; setting to {}'
                 .format(self.site), RuntimeWarning, 2)
        else:
            self.site = site
        if mime_params is not None:
            # mime may not be different from mime_params
            if mime is not None and mime is not True:
                raise ValueError('If mime_params is set, mime may not differ '
                                 'from it.')
            warn('Use the "mime" parameter instead of the "mime_params".')
            mime = mime_params
        self.mime = mime  # this also sets self.mime_params
        self.throttle = throttle
        self.use_get = use_get
        if max_retries is None:
            self.max_retries = pywikibot.config.max_retries
        else:
            self.max_retries = max_retries
        if retry_wait is None:
            self.retry_wait = pywikibot.config.retry_wait
        else:
            self.retry_wait = retry_wait
        # The only problem with that system is that it won't detect when
        # 'parameters' is actually the only parameter for the request as it
        # then assumes it's using the new mode (and the parameters are actually
        # in the parameter 'parameters' not that the parameter 'parameters' is
        # actually a parameter for the request). But that is invalid anyway as
        # it MUST have at least an action parameter for the request which would
        # be in kwargs if it's using the old mode.
        if kwargs:
            if parameters is not self._PARAM_DEFAULT:
                # 'parameters' AND kwargs is set. In that case think of
                # 'parameters' being an old kwarg which is now filled in an
                # actual parameter
                self._warn_both()
                kwargs['parameters'] = parameters
            # When parameters wasn't set it's likely that kwargs-mode was used
            self._warn_kwargs()
            parameters = kwargs
        elif parameters is self._PARAM_DEFAULT:
            parameters = {}
        self._params = {}
        if 'action' not in parameters:
            raise ValueError("'action' specification missing from Request.")
        self.action = parameters['action']
        self.update(parameters)  # also convert all parameter values to lists
        self._warning_handler = None
        # Actions that imply database updates on the server, used for various
        # things like throttling or skipping actions when we're in simulation
        # mode
        self.write = self.action in (
            'block', 'clearhasmsg', 'createaccount', 'delete', 'edit',
            'emailuser', 'filerevert', 'flowthank', 'imagerotate', 'import',
            'managetags', 'mergehistory', 'move', 'options', 'patrol',
            'protect', 'purge', 'resetpassword', 'revisiondelete', 'rollback',
            'setnotificationtimestamp', 'setpagelanguage', 'tag', 'thank',
            'unblock', 'undelete', 'upload', 'userrights', 'watch',
            'wbcreateclaim', 'wbcreateredirect', 'wbeditentity',
            'wblinktitles', 'wbmergeitems', 'wbremoveclaims',
            'wbremovequalifiers', 'wbremovereferences', 'wbsetaliases',
            'wbsetclaim', 'wbsetclaimvalue', 'wbsetdescription', 'wbsetlabel',
            'wbsetqualifier', 'wbsetreference', 'wbsetsitelink',
        )
        # Client side verification that the request is being performed
        # by a logged in user, and warn if it isn't a config username.
        if self.write:
            try:
                username = self.site.userinfo['name']
            except KeyError:
                raise Error('API write action attempted without user name')

            if 'anon' in self.site.userinfo:
                raise Error("API write action attempted as IP '{}'"
                            .format(username))

            if not self.site.user() or self.site.username() != username:
                pywikibot.warning(
                    'API write action by unexpected username {} commenced.\n'
                    'userinfo: {!r}'.format(username, self.site.userinfo))

        # MediaWiki 1.23 allows assertion for any action,
        # whereas earlier WMF wikis and others used an extension which
        # could only allow assert for action=edit.
        #
        # When we can't easily check whether the extension is loaded,
        # to avoid cyclic recursion in the Pywikibot codebase, assume
        # that it is present, which will cause a API warning emitted
        # to the logging (console) if it is not present, but will not
        # otherwise be a problem.
        # This situation is only tripped when one of the first actions
        # on the site is a write action and the extension isn't installed.
        if (self.write and self.site.mw_version >= '1.23'
            or self.action == 'edit'
                and self.site.has_extension('AssertEdit')):
            pywikibot.debug('Adding user assertion', _logger)
            self['assert'] = 'user'  # make sure user is logged in

    @classmethod
    def create_simple(cls, site, **kwargs):
        """Create a new instance using all args except site for the API."""
        # This ONLY support site so that any caller can be sure there will be
        # no conflict with PWB parameters
        # TODO: Use ParamInfo request to determine valid parameters
        if isinstance(kwargs.get('parameters'), dict):
            warn('The request contains already a "parameters" entry which is '
                 'a dict.')
        return cls(site, parameters=kwargs)

    @classmethod
    def _warn_both(cls):
        """Warn that kwargs mode was used but parameters was set too."""
        warn('Both kwargs and parameters are set in Request.__init__. It '
             'assumes that "parameters" is actually a parameter of the '
             'Request and is added to kwargs.', DeprecationWarning, 3)

    @classmethod
    def _warn_kwargs(cls):
        """Warn that kwargs was used instead of parameters."""
        warn('Instead of using kwargs from Request.__init__, parameters '
             'for the request to the API should be added via the '
             '"parameters" parameter.', DeprecationWarning, 3)

    @classmethod
    def clean_kwargs(cls, kwargs):
        """
        Convert keyword arguments into new parameters mode.

        If there are no other arguments in kwargs apart from the used arguments
        by the class' initializer it'll just return kwargs and otherwise remove
        those which aren't in the initializer and put them in a dict which is
        added as a 'parameters' keyword. It will always create a shallow copy.

        @param kwargs: The original keyword arguments which is not modified.
        @type kwargs: dict
        @return: The normalized keyword arguments.
        @rtype: dict
        """
        if 'expiry' in kwargs and kwargs['expiry'] is None:
            del kwargs['expiry']

        args = set()
        for super_cls in inspect.getmro(cls):
            if not super_cls.__name__.endswith('Request'):
                break
            args |= set(getargspec(super_cls.__init__)[0])
        else:
            raise ValueError('Request was not a super class of '
                             '{0!r}'.format(cls))
        args -= {'self'}
        old_kwargs = set(kwargs)
        # all kwargs defined above but not in args indicate 'kwargs' mode
        if old_kwargs - args:
            # Move all kwargs into parameters
            parameters = {name: value for name, value in kwargs.items()
                          if name not in args or name == 'parameters'}
            if 'parameters' in parameters:
                cls._warn_both()
            # Copy only arguments and not the parameters
            kwargs = {name: value for name, value in kwargs.items()
                      if name in args or name == 'self'}
            kwargs['parameters'] = parameters
            # Make sure that all arguments have remained
            assert(old_kwargs | {'parameters'}
                   == set(kwargs) | set(kwargs['parameters']))
            assert(('parameters' in old_kwargs)
                   is ('parameters' in kwargs['parameters']))
            cls._warn_kwargs()
        else:
            kwargs = dict(kwargs)
            kwargs.setdefault('parameters', {})
        return kwargs

    def _format_value(self, value):
        """
        Format the MediaWiki API request parameter.

        Converts from Python datatypes to MediaWiki API parameter values.

        Supports:
         * datetime.datetime (using strftime and ISO8601 format)
         * pywikibot.page.BasePage (using title (+namespace; -section))

        All other datatypes are converted to string using unicode() on Python 2
        and str() on Python 3.
        """
        if isinstance(value, datetime.datetime):
            return value.strftime(pywikibot.Timestamp.ISO8601Format)
        elif isinstance(value, pywikibot.page.BasePage):
            assert(value.site == self.site)
            return value.title(with_section=False)
        else:
            return UnicodeType(value)

    def __getitem__(self, key):
        """Implement dict interface."""
        return self._params[key]

    def __setitem__(self, key, value):
        """Set MediaWiki API request parameter.

        @param key: param key

        @type key: basestring

        @param value: param value(s)

        @type value: str in site encoding
            (string types may be a `|`-separated list)
            iterable, where items are converted to unicode
            with special handling for datetime.datetime to convert it to a
            string using the ISO 8601 format accepted by the MediaWiki API.
        """
        # Allow site encoded bytes (note: str is a subclass of bytes in py2)
        if isinstance(value, bytes):
            value = value.decode(self.site.encoding())

        if isinstance(value, UnicodeType):
            value = value.split('|')

        if hasattr(value, 'api_iter'):
            self._params[key] = value
        else:
            try:
                iter(value)
            except TypeError:
                # convert any non-iterable value into a single-element list
                self._params[key] = [value]
            else:
                self._params[key] = list(value)

    def __delitem__(self, key):
        """Implement dict interface."""
        del self._params[key]

    def keys(self):
        """Implement dict interface."""
        return list(self._params.keys())

    def __contains__(self, key):
        """Implement dict interface."""
        return key in self._params

    def __iter__(self):
        """Implement dict interface."""
        return iter(self._params)

    def __len__(self):
        """Implement dict interface."""
        return len(self._params)

    def iteritems(self):
        """Implement dict interface."""
        return iter(self._params.items())

    def items(self):
        """Return a list of tuples containing the parameters in any order."""
        return list(self._params.items())

    @property
    def mime(self):
        """Return whether mime parameters are defined."""
        return self.mime_params is not None

    @mime.setter
    def mime(self, value):
        """
        Change whether mime parameter should be defined.

        This will clear the mime parameters.
        """
        try:
            self.mime_params = dict(value)
        except TypeError:
            self.mime_params = {} if value else None

    @deprecated('_http_param_string', since='20141006')
    def http_params(self):
        """Return the parameters formatted for inclusion in an HTTP request.

        DEPRECATED. See _encoded_items for explanation of encoding used.
        """
        self._add_defaults()
        return self._http_param_string()

    def _add_defaults(self):
        """
        Add default parameters to the API request.

        This method will only add them once.
        """
        if hasattr(self, '__defaulted'):
            return

        if self.mime_params \
           and set(self._params.keys()) & set(self.mime_params.keys()):
            raise ValueError('The mime_params and params may not share the '
                             'same keys.')

        if self.action == 'query':
            meta = self._params.get('meta', [])
            # Special logic for private wikis (T153903).
            # If the wiki requires login privileges to read articles, pywikibot
            # will be blocked from accessing the userinfo.
            # Work around this by requiring userinfo only if 'tokens' and
            # 'login' are not both set.
            typep = self._params.get('type', [])
            if not ('tokens' in meta and 'login' in typep):
                if 'userinfo' not in meta:
                    meta = set(meta + ['userinfo'])
                    self['meta'] = sorted(meta)
                uiprop = self._params.get('uiprop', [])
                uiprop = set(uiprop + ['blockinfo', 'hasmsg'])
                self['uiprop'] = sorted(uiprop)
            if 'prop' in self._params:
                if self.site.has_extension('ProofreadPage'):
                    prop = set(self['prop'] + ['proofread'])
                    self['prop'] = sorted(prop)
            # When neither 'continue' nor 'rawcontinue' is present and the
            # version number is at least 1.25wmf5 we add a dummy rawcontinue
            # parameter. Querying siteinfo is save as it adds 'continue'.
            if ('continue' not in self._params
                    and self.site.mw_version >= '1.25wmf5'):
                self._params.setdefault('rawcontinue', [''])
        elif self.action == 'help' and self.site.mw_version > '1.24':
            self['wrap'] = ''

        if config.maxlag:
            self._params.setdefault('maxlag', [str(config.maxlag)])
        self._params.setdefault('format', ['json'])
        if self['format'] != ['json']:
            raise TypeError(
                "Query format '{}' cannot be parsed.".format(self['format']))

        self.__defaulted = True

    def _encoded_items(self):
        """
        Build a dict of params with minimal encoding needed for the site.

        This helper method only prepares params for serialisation or
        transmission, so it only encodes values which are not ASCII,
        requiring callers to consider how to handle ASCII vs other values,
        however the output is designed to enable __str__ and __repr__ to
        do the right thing in most circumstances.

        Servers which use an encoding that is not a superset of ASCII
        are not supported.

        @return: Parameters either in the site encoding, or ASCII strings
        @rtype: dict with values of either str or bytes
        """
        params = {}
        for key, values in self._params.items():
            try:
                iterator = values.api_iter()
            except AttributeError:
                if len(values) == 1:
                    value = values[0]
                    if value is True:
                        values = ['']
                    elif value is False or value is None:
                        # False and None are not included in the http URI
                        continue
                iterator = iter(values)
            value = '|'.join(self._format_value(value) for value in iterator)
            # If the value is encodable as ascii, do not encode it.
            # This means that any value which can be encoded as ascii
            # is presumed to be ascii, and servers using a site encoding
            # which is not a superset of ascii may be problematic.
            try:
                value.encode('ascii')
                # In Python 2, ascii API params should be represented as 'foo'
                # rather than u'foo'
                if PY2:
                    value = str(value)
            except UnicodeError:
                try:
                    value = value.encode(self.site.encoding())
                except Exception:
                    pywikibot.error(
                        "_encoded_items: '%s' could not be encoded as '%s':"
                        ' %r' % (key, self.site.encoding(), value))
            if PY2:
                key = key.encode('ascii')
            else:
                assert key.encode('ascii')
            assert isinstance(key, str)
            params[key] = value
        return params

    def _http_param_string(self):
        """
        Return the parameters as a HTTP URL query fragment.

        URL encodes the parameters provided by _encoded_items()

        @note: Not all parameters are sorted, therefore for two given
            CachedRequest objects with equal _params, the result of
            _http_param_string() is not necessarily equal.
        """
        return encode_url(self._encoded_items())

    def __str__(self):
        """Return a string representation."""
        return unquote(self.site.scriptpath()
                       + '/api.php?'
                       + self._http_param_string())

    def __repr__(self):
        """Return internal representation."""
        return '{}.{}<{}->{!r}>'.format(self.__class__.__module__,
                                        self.__class__.__name__,
                                        self.site, str(self))

    def _simulate(self, action):
        """Simulate action."""
        if action and config.simulate and (
                self.write or action in config.actions_to_block):
            pywikibot.output(color_format(
                '{lightyellow}SIMULATION: {0} action blocked.{default}',
                action))
            return {action: {'result': 'Success', 'nochange': ''}}

    def _is_wikibase_error_retryable(self, error):
        ERR_MSG = (
            'edit-already-exists',
            'actionthrottledtext',  # T192912
        )
        messages = error.get('messages')
        message = None
        # bug T68619; after Wikibase breaking change 1ca9cee change we have a
        # list of messages
        if isinstance(messages, list):
            for item in messages:
                message = item['name']
                if message in ERR_MSG:
                    return True
        elif isinstance(messages, dict):
            try:  # behaviour before gerrit 124323 breaking change
                message = messages['0']['name']
            except KeyError:  # unsure the new output is always a list
                message = messages['name']
        return message in ERR_MSG

    @staticmethod
    def _generate_MIME_part(key, content, keytype=None, headers=None):
        if not keytype:
            try:
                content.encode('ascii')
                keytype = ('text', 'plain')
            except (UnicodeError, AttributeError):
                keytype = ('application', 'octet-stream')
        submsg = MIMENonMultipart(*keytype)
        content_headers = {'name': key}
        if headers:
            content_headers.update(headers)
        submsg.add_header('Content-disposition', 'form-data',
                          **content_headers)

        if keytype != ('text', 'plain'):
            submsg['Content-Transfer-Encoding'] = 'binary'

        submsg.set_payload(content)
        return submsg

    def _use_get(self):
        """Verify whether 'get' is to be used."""
        if (not config.enable_GET_without_SSL
                and self.site.protocol() != 'https'
                or self.site.is_oauth_token_available()):  # T108182 workaround
            use_get = False
        elif self.use_get is None:
            if self.action == 'query':
                # for queries check the query module
                modules = set()
                for mod_type_name in ('list', 'prop', 'generator'):
                    modules.update(self._params.get(mod_type_name, []))
            else:
                modules = {self.action}
            if modules:
                self.site._paraminfo.fetch(modules)
                use_get = all('mustbeposted' not in self.site._paraminfo[mod]
                              for mod in modules)
            else:
                # If modules is empty, just 'meta' was given, which doesn't
                # require POSTs, and is required for ParamInfo
                use_get = True
        else:
            use_get = self.use_get
        return use_get

    @classmethod
    def _build_mime_request(cls, params, mime_params):
        """
        Construct a MIME multipart form post.

        @param params: HTTP request params
        @type params: dict
        @param mime_params: HTTP request parts which must be sent in the body
        @type mime_params: dict of (content, keytype, headers)
        @return: HTTP request headers and body
        @rtype: tuple (dict, str)
        """
        # construct a MIME message containing all API key/values
        container = MIMEMultipart(_subtype='form-data')
        for key, value in params.items():
            submsg = cls._generate_MIME_part(key, value)
            container.attach(submsg)
        for key, value in mime_params.items():
            submsg = cls._generate_MIME_part(key, *value)
            container.attach(submsg)

        # strip the headers to get the HTTP message body
        if not PY2:
            body = container.as_bytes()
        else:
            body = container.as_string()
        marker = b'\n\n'  # separates headers from body
        eoh = body.find(marker)
        body = body[eoh + len(marker):]
        # retrieve the headers from the MIME object
        headers = dict(container.items())
        return headers, body

    def _get_request_params(self, use_get, paramstring):
        """Get request parameters."""
        uri = self.site.apipath()
        if self.mime:
            (headers, body) = Request._build_mime_request(
                self._encoded_items(), self.mime_params)
            use_get = False  # MIME requests require HTTP POST
        else:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            if (not self.site.maximum_GET_length()
                    or self.site.maximum_GET_length() < len(paramstring)):
                use_get = False
            if use_get:
                uri = '{0}?{1}'.format(uri, paramstring)
                body = None
            else:
                body = paramstring

        pywikibot.debug('API request to {0} (uses get: {1}):\n'
                        'Headers: {2!r}\nURI: {3!r}\nBody: {4!r}'
                        .format(self.site, use_get, headers, uri, body),
                        _logger)
        return use_get, uri, body, headers

    def _http_request(self, use_get, uri, body, headers, paramstring):
        """Get or post a http request with exception handling.

        @return: a tuple containing data from request and use_get value
        @rtype: tuple
        """
        try:
            data = http.request(
                site=self.site, uri=uri,
                method='GET' if use_get else 'POST',
                body=body, headers=headers)
        except Server504Error:
            pywikibot.log('Caught HTTP 504 error; retrying')
        except Server414Error:
            if use_get:
                pywikibot.log('Caught HTTP 414 error; retrying')
                use_get = False
            else:
                pywikibot.warning('Caught HTTP 414 error, although not '
                                  'using GET.')
                raise
        except FatalServerError:
            # This error is not going to be fixed by just waiting
            pywikibot.error(traceback.format_exc())
            raise
        # TODO: what other exceptions can occur here?
        except Exception:
            # for any other error on the http request, wait and retry
            pywikibot.error(traceback.format_exc())
            pywikibot.log('{}, {}'.format(uri, paramstring))
        else:
            return data, use_get
        self.wait()
        return None, use_get

    def _json_loads(self, data):
        """Read source text and return a dict.

        @param data: raw data string
        @type data: str
        @return: a data dict
        @rtype: dict
        @raises APIError: unknown action found
        @raises APIError: unknown query result type
        """
        if not isinstance(data, UnicodeType):
            data = data.decode(self.site.encoding())
        pywikibot.debug(('API response received from {}:\n'
                         .format(self.site)) + data, _logger)
        if data.startswith('unknown_action'):
            raise APIError(data[:14], data[16:])
        try:
            result = json.loads(data)
        except ValueError:
            # if the result isn't valid JSON, there must be a server
            # problem. Wait a few seconds and try again
            pywikibot.warning(
                'Non-JSON response received from server {}; '
                'the server may be down.'.format(self.site))
            # there might also be an overflow, so try a smaller limit
            for param in self._params:
                if param.endswith('limit'):
                    # param values are stored a list of str
                    value = self[param][0]
                    if value.isdigit():
                        self[param] = [str(int(value) // 2)]
                        pywikibot.output('Set {} = {}'
                                         .format(param, self[param]))
        else:
            if result and not isinstance(result, dict):
                raise APIError('Unknown',
                               'Unable to process query response of type {}.'
                               .format(type(result)),
                               data=result)
            return result or {}
        self.wait()
        return None

    def _relogin(self, message=''):
        """Force re-login and inform user."""
        pywikibot.error('{}{}Forcing re-login.'.format(message,
                                                       ' ' if message else ''))
        self.site._relogin()

    def _userinfo_query(self, result):
        """Handle userinfo query."""
        if self.action == 'query' and 'userinfo' in result.get('query', ()):
            # if we get passed userinfo in the query result, we can confirm
            # that we are logged in as the correct user. If this is not the
            # case, force a re-login.
            username = result['query']['userinfo']['name']
            if (self.site.user() is not None and self.site.user() != username
                    and self.site._loginstatus
                    != pywikibot.site.LoginStatus.IN_PROGRESS):
                message = ("Logged in as '{actual}' instead of '{expected}'."
                           .format(actual=username, expected=self.site.user()))
                self._relogin(message)
                return True
        return False

    def _handle_warnings(self, result):
        if 'warnings' in result:
            for mod, warning in result['warnings'].items():
                if mod == 'info':
                    continue
                if '*' in warning:
                    text = warning['*']
                elif 'html' in warning:
                    # bug T51978
                    text = warning['html']['*']
                else:
                    pywikibot.warning(
                        'API warning ({0}) of unknown format: {1}'.
                        format(mod, warning))
                    continue
                # multiple warnings are in text separated by a newline
                for single_warning in text.splitlines():
                    if (not callable(self._warning_handler)
                            or not self._warning_handler(mod, single_warning)):
                        pywikibot.warning('API warning ({}): {}'
                                          .format(mod, single_warning))

    def _logged_in(self, code):
        """Check whether user is logged in.

        Older wikis returned an error instead of a warning when the request
        asked for too many values. If we get this error, assume we are not
        logged in (we can't check this because the userinfo data is not
        present) and force a re-login
        """
        if code.endswith('limit'):
            message = 'Received API limit error.'

        # If the user assertion failed, we're probably logged out as well.
        elif code == 'assertuserfailed':
            message = 'User assertion failed.'

        # Lastly, the purge module requires a POST if used as anonymous user,
        # but we normally send a GET request. If the API tells us the request
        # has to be POSTed, we're probably logged out.
        elif code == 'mustbeposted' and self.action == 'purge':
            message = "Received unexpected 'mustbeposted' error."

        else:
            return True

        self._relogin(message)
        return False

    def _internal_api_error(self, code, error, result):
        """Check for internal_api_error_ or readonly and retry.

        @raises APIMWException: internal_api_error or readonly
        """
        IAE = 'internal_api_error_'
        if not (code.startswith(IAE) or code == 'readonly'):
            return False

        # T154011
        class_name = code if code == 'readonly' else code[len(IAE):]

        del error['code']  # is added via class_name
        e = APIMWException(class_name, **error)

        # If the error key is in this table, it is probably a temporary
        # problem, so we will retry the edit.
        # TODO: T154011: 'ReadOnlyError' seems replaced by 'readonly'
        retry = class_name in ['DBConnectionError',  # T64974
                               'DBQueryError',  # T60158
                               'ReadOnlyError',  # T61227
                               'readonly',  # T154011
                               ]

        pywikibot.error('Detected MediaWiki API exception {}{}'
                        .format(e, '; retrying' if retry else '; raising'))
        # Due to bug T66958, Page's repr may return non ASCII bytes
        # Get as bytes in PY2 and decode with the console encoding as
        # the rest should be ASCII anyway.
        param_repr = str(self._params)
        if PY2:
            param_repr = param_repr.decode(config.console_encoding)
        pywikibot.log('MediaWiki exception {} details:\n'
                      '          query=\n{}\n'
                      '          response=\n{}'
                      .format(class_name,
                              pprint.pformat(param_repr),
                              result))
        if not retry:
            raise e

        self.wait()
        return True

    def _bad_token(self, code):
        """Check for bad token."""
        if (code != 'badtoken' or self.site._loginstatus
                == pywikibot.site.LoginStatus.IN_PROGRESS):
            return False

        user_tokens = self.site.tokens._tokens[self.site.user()]
        # all token values mapped to their type
        tokens = {token: t_type for t_type, token in user_tokens.items()}
        # determine which tokens are bad
        invalid_param = {name: tokens[param[0]]
                         for name, param in self._params.items()
                         if len(param) == 1 and param[0] in tokens}
        # doesn't care about the cache so can directly load them
        if invalid_param:
            pywikibot.log(
                'Bad token error for {}. Tokens for "{}" used in request; '
                'invalidated them.'
                .format(self.site.user(),
                        '", "'.join(sorted(set(invalid_param.values())))))
            # invalidate superior wiki cookies (T224712)
            _invalidate_superior_cookies(self.site.family)
            # request new token(s) instead of invalid
            self.site.tokens.load_tokens(set(invalid_param.values()))
            # fix parameters; lets hope that it doesn't mistake actual
            # parameters as tokens
            for name, t_type in invalid_param.items():
                self[name] = self.site.tokens[t_type]
            return True
        else:
            # otherwise couldn't find any … weird there is nothing what
            # can be done here because it doesn't know which parameters
            # to fix
            pywikibot.log(
                'Bad token error for {} but no parameter is using a '
                'token. Current tokens: {}'
                .format(self.site.user(),
                        ', '.join('{}: {}'.format(*e)
                                  for e in user_tokens.items())))
        return False

    def submit(self):
        """
        Submit a query and parse the response.

        @return: a dict containing data retrieved from api.php
        @rtype: dict
        """
        self._add_defaults()
        use_get = self._use_get()
        retries = 0
        while True:
            paramstring = self._http_param_string()

            simulate = self._simulate(self.action)
            if simulate:
                return simulate

            if self.throttle:
                self.site.throttle(write=self.write)
            else:
                pywikibot.log(
                    "Submitting unthrottled action '{0}'.".format(self.action))

            use_get, uri, body, headers = self._get_request_params(use_get,
                                                                   paramstring)
            rawdata, use_get = self._http_request(use_get, uri, body, headers,
                                                  paramstring)
            if rawdata is None:
                continue

            result = self._json_loads(rawdata)
            if result is None:
                continue

            if self._userinfo_query(result):
                continue

            self._handle_warnings(result)

            if 'error' not in result:
                return result

            error = result['error'].copy()
            for key in result:
                if key in ('error', 'warnings'):
                    continue
                assert key not in error
                assert isinstance(result[key], UnicodeType), \
                    'Unexpected %s: %r' % (key, result[key])
                error[key] = result[key]

            if '*' in result['error']:
                # help text returned
                result['error']['help'] = result['error'].pop('*')
            code = result['error'].setdefault('code', 'Unknown')
            info = result['error'].setdefault('info', None)

            if not self._logged_in(code):
                continue

            if code == 'maxlag':
                retries += 1
                if retries > max(5, pywikibot.config.max_retries):
                    break
                pywikibot.log('Pausing due to database lag: ' + info)

                try:
                    lag = result['error']['lag']
                except KeyError:
                    lag = lagpattern.search(info)
                    lag = float(lag.group('lag')) if lag else 0.0

                self.site.throttle.lag(lag * retries)
                continue

            elif code == 'help' and self.action == 'help':
                # The help module returns an error result with the complete
                # API information. As this data was requested, return the
                # data instead of raising an exception.
                return {'help': {'mime': 'text/plain',
                                 'help': result['error']['help']}}

            pywikibot.warning('API error %s: %s' % (code, info))

            if self._internal_api_error(code, error, result):
                continue

            # Phab. tickets T48535, T64126, T68494, T68619
            if code == 'failed-save' and \
               self.action == 'wbeditentity' and \
               self._is_wikibase_error_retryable(result['error']):
                self.wait()
                continue

            # If readapidenied is returned try to login
            if code == 'readapidenied' and self.site._loginstatus in (-3, -1):
                self.site.login()
                continue

            if self._bad_token(code):
                continue

            if 'mwoauth-invalid-authorization' in code:
                if 'Nonce already used' in info:
                    pywikibot.error(
                        'Retrying failed OAuth authentication for {0}: {1}'
                        .format(self.site, info))
                    continue
                raise NoUsername('Failed OAuth authentication for %s: %s'
                                 % (self.site, info))
            if code == 'cirrussearch-too-busy-error':  # T170647
                self.wait()
                continue

            if code == 'urlshortener-blocked':  # T244062
                # add additional informations to result['error']
                result['error']['current site'] = self.site
                if self.site.user():
                    result['error']['current user'] = self.site.user()
                else:  # not logged in; show the IP
                    uinfo = self.site.userinfo
                    result['error']['current user'] = uinfo['name']

            # raise error
            try:
                # Due to bug T66958, Page's repr may return non ASCII bytes
                # Get as bytes in PY2 and decode with the console encoding as
                # the rest should be ASCII anyway.
                param_repr = str(self._params)
                if PY2:
                    param_repr = param_repr.decode(config.console_encoding)
                pywikibot.log('API Error: query=\n%s'
                              % pprint.pformat(param_repr))
                pywikibot.log('           response=\n%s'
                              % result)

                raise APIError(**result['error'])
            except TypeError:
                raise RuntimeError(result)

        msg = 'Maximum retries attempted due to maxlag without success.'
        if os.environ.get('PYWIKIBOT_TESTS_RUNNING', '0') == '1':
            import unittest
            raise unittest.SkipTest(msg)

        raise MaxlagTimeoutError(msg)

    def wait(self):
        """Determine how long to wait after a failed request."""
        self.max_retries -= 1
        if self.max_retries < 0:
            raise TimeoutError('Maximum retries attempted without success.')
        pywikibot.warning('Waiting %s seconds before retrying.'
                          % self.retry_wait)
        pywikibot.sleep(self.retry_wait)
        # double the next wait, but do not exceed config.retry_max seconds
        self.retry_wait = min(config.retry_max, self.retry_wait * 2)


class CachedRequest(Request):

    """Cached request."""

    def __init__(self, expiry, *args, **kwargs):
        """Initialize a CachedRequest object.

        @param expiry: either a number of days or a datetime.timedelta object
        """
        assert expiry is not None
        super(CachedRequest, self).__init__(*args, **kwargs)
        if not isinstance(expiry, datetime.timedelta):
            expiry = datetime.timedelta(expiry)
        self.expiry = min(expiry, datetime.timedelta(config.API_config_expiry))
        self._data = None
        self._cachetime = None

    @classmethod
    def create_simple(cls, site, **kwargs):
        """Unsupported as it requires at least two parameters."""
        raise NotImplementedError('CachedRequest cannot be created simply.')

    @classmethod
    def _get_cache_dir(cls):
        """
        Return the base directory path for cache entries.

        The directory will be created if it does not already exist.

        @return: base directory path for cache entries
        @rtype: basestring
        """
        path = os.path.join(pywikibot.config2.base_dir,
                            'apicache-py{0:d}'.format(PYTHON_VERSION[0]))
        cls._make_dir(path)
        cls._get_cache_dir = classmethod(lambda c: path)  # cache the result
        return path

    @staticmethod
    def _make_dir(dir):
        """
        Create directory if it does not exist already.

        The directory name (dir) is returned unmodified.

        @param dir: directory path
        @type dir: basestring

        @return: directory name
        @rtype: basestring
        """
        try:
            os.makedirs(dir)
        except OSError:
            # directory already exists
            pass
        return dir

    def _uniquedescriptionstr(self):
        """Return unique description for the cache entry.

        If this is modified, please also update
        scripts/maintenance/cache.py to support
        the new key and all previous keys.

        @rtype: str
        """
        login_status = self.site._loginstatus

        if login_status >= pywikibot.site.LoginStatus.AS_USER:
            # This uses the format of Page.__repr__, without performing
            # config.console_encoding as done by Page.__repr__.
            # The returned value can't be encoded to anything other than
            # ascii otherwise it creates an exception when _create_file_name()
            # tries to encode it as utf-8.
            user_key = 'User(User:{})'.format(self.site.userinfo['name'])
        else:
            user_key = repr(pywikibot.site.LoginStatus(
                pywikibot.site.LoginStatus.NOT_LOGGED_IN))

        request_key = repr(sorted(self._encoded_items().items()))
        return repr(self.site) + user_key + request_key

    def _create_file_name(self):
        """
        Return a unique ascii identifier for the cache entry.

        @rtype: str (hexadecimal; i.e. characters 0-9 and a-f only)
        """
        return hashlib.sha256(
            self._uniquedescriptionstr().encode('utf-8')
        ).hexdigest()

    def _cachefile_path(self):
        return os.path.join(CachedRequest._get_cache_dir(),
                            self._create_file_name())

    def _expired(self, dt):
        return dt + self.expiry < datetime.datetime.utcnow()

    def _load_cache(self):
        """Load cache entry for request, if available.

        @return: Whether the request was loaded from the cache
        @rtype: bool
        """
        self._add_defaults()
        try:
            filename = self._cachefile_path()
            with open(filename, 'rb') as f:
                uniquedescr, self._data, self._cachetime = pickle.load(f)
            assert(uniquedescr == self._uniquedescriptionstr())
            if self._expired(self._cachetime):
                self._data = None
                return False
            pywikibot.debug('%s: cache hit (%s) for API request: %s'
                            % (self.__class__.__name__, filename, uniquedescr),
                            _logger)
            return True
        except IOError:
            # file not found
            return False
        except Exception as e:
            pywikibot.output('Could not load cache: %r' % e)
            return False

    def _write_cache(self, data):
        """Write data to self._cachefile_path()."""
        data = (self._uniquedescriptionstr(), data, datetime.datetime.utcnow())
        with open(self._cachefile_path(), 'wb') as f:
            pickle.dump(data, f, protocol=config.pickle_protocol)

    def submit(self):
        """Submit cached request."""
        cached_available = self._load_cache()
        if not cached_available:
            self._data = super(CachedRequest, self).submit()
            self._write_cache(self._data)
        else:
            self._handle_warnings(self._data)
        return self._data


class _RequestWrapper(object):

    """A wrapper class to handle the usage of the C{parameters} parameter."""

    def _clean_kwargs(self, kwargs, **mw_api_args):
        """Clean kwargs, define site and request class."""
        if 'site' not in kwargs:
            warn('{0} invoked without a site'.format(self.__class__.__name__),
                 RuntimeWarning, 3)
            kwargs['site'] = pywikibot.Site()
        assert(not hasattr(self, 'site') or self.site == kwargs['site'])
        self.site = kwargs['site']
        self.request_class = kwargs['site']._request_class(kwargs)
        kwargs = self.request_class.clean_kwargs(kwargs)
        kwargs['parameters'].update(mw_api_args)
        return kwargs


class APIGenerator(_RequestWrapper):

    """
    Iterator that handle API responses containing lists.

    The iterator will iterate each item in the query response and use the
    continue request parameter to retrieve the next portion of items
    automatically. If the limit attribute is set, the iterator will stop
    after iterating that many values.
    """

    def __init__(self, action, continue_name='continue', limit_name='limit',
                 data_name='data', **kwargs):
        """
        Initialize an APIGenerator object.

        kwargs are used to create a Request object; see that object's
        documentation for values.

        @param action: API action name.
        @type action: str
        @param continue_name: Name of the continue API parameter.
        @type continue_name: str
        @param limit_name: Name of the limit API parameter.
        @type limit_name: str
        @param data_name: Name of the data in API response.
        @type data_name: str
        """
        kwargs = self._clean_kwargs(kwargs, action=action)

        self.continue_name = continue_name
        self.limit_name = limit_name
        self.data_name = data_name

        if config.step > 0:
            self.query_increment = config.step
        else:
            self.query_increment = None
        self.limit = None
        self.starting_offset = kwargs['parameters'].pop(self.continue_name, 0)
        self.request = self.request_class(**kwargs)
        self.request[self.limit_name] = self.query_increment

    def set_query_increment(self, value):
        """
        Set the maximum number of items to be retrieved per API query.

        If not called, the default is config.step.

        @param value: The value of maximum number of items to be retrieved
            per API request to set.
        @type value: int
        """
        self.query_increment = int(value)
        self.request[self.limit_name] = self.query_increment
        pywikibot.debug('%s: Set query_increment to %i.'
                        % (self.__class__.__name__, self.query_increment),
                        _logger)

    def set_maximum_items(self, value):
        """
        Set the maximum number of items to be retrieved from the wiki.

        If not called, most queries will continue as long as there is
        more data to be retrieved from the API.

        @param value: The value of maximum number of items to be retrieved
            in total to set. Ignores None value.
        @type value: int or str or None
        """
        if value is not None and int(value) > 0:
            self.limit = int(value)
            if self.query_increment and self.limit < self.query_increment:
                self.request[self.limit_name] = self.limit
                pywikibot.debug('{0}: Set request item limit to {1}'
                                .format(self.__class__.__name__, self.limit),
                                _logger)
            pywikibot.debug('{0}: Set limit (maximum_items) to {1}.'
                            .format(self.__class__.__name__, self.limit),
                            _logger)

    def __iter__(self):
        """
        Submit request and iterate the response.

        Continues response as needed until limit (if defined) is reached.
        """
        offset = self.starting_offset
        n = 0
        while True:
            self.request[self.continue_name] = offset
            pywikibot.debug('%s: Request: %s' % (
                self.__class__.__name__, self.request), _logger)
            data = self.request.submit()

            n_items = len(data[self.data_name])
            pywikibot.debug('%s: Retrieved %d items' % (
                self.__class__.__name__, n_items), _logger)
            if n_items > 0:
                for item in data[self.data_name]:
                    yield item
                    n += 1
                    if self.limit is not None and n >= self.limit:
                        pywikibot.debug('%s: Stopped iterating due to '
                                        'exceeding item limit.' %
                                        self.__class__.__name__, _logger)
                        return
                offset += n_items
            else:
                pywikibot.debug('{}: Stopped iterating due to empty list in '
                                'response.'.format(self.__class__.__name__),
                                _logger)
                break


class QueryGenerator(_RequestWrapper):

    """
    Base class for iterators that handle responses to API action=query.

    By default, the iterator will iterate each item in the query response,
    and use the (query-)continue element, if present, to continue iterating as
    long as the wiki returns additional values. However, if the iterator's
    limit attribute is set to a positive int, the iterator will stop after
    iterating that many values. If limit is negative, the limit parameter
    will not be passed to the API at all.

    Most common query types are more efficiently handled by subclasses, but
    this class can be used directly for custom queries and miscellaneous
    types (such as "meta=...") that don't return the usual list of pages or
    links. See the API documentation for specific query options.

    """

    # Should results be filtered during iteration according to set_namespace?
    # Used if the API module does not support multiple namespaces.
    # Override in subclasses by defining a function that returns True if
    # the result's namespace is in self._namespaces.
    _check_result_namespace = NotImplemented

    # Set of allowed namespaces will be assigned to _namespaces during
    # set_namespace call. Only to be used by _check_result_namespace.
    _namespaces = None

    def __init__(self, **kwargs):
        """
        Initialize a QueryGenerator object.

        kwargs are used to create a Request object; see that object's
        documentation for values. 'action'='query' is assumed.

        """
        if not hasattr(self, 'site'):
            kwargs = self._clean_kwargs(kwargs)  # hasn't been called yet
        parameters = kwargs['parameters']
        if 'action' in parameters and parameters['action'] != 'query':
            raise Error("%s: 'action' must be 'query', not %s"
                        % (self.__class__.__name__, kwargs['action']))
        else:
            parameters['action'] = 'query'
        # make sure request type is valid, and get limit key if any
        for modtype in ('generator', 'list', 'prop', 'meta'):
            if modtype in parameters:
                self.modules = parameters[modtype].split('|')
                break
        else:
            raise Error('%s: No query module name found in arguments.'
                        % self.__class__.__name__)

        parameters['indexpageids'] = True  # always ask for list of pageids
        if self.site.mw_version < '1.21':
            self.continue_name = 'query-continue'
            self.continue_update = self._query_continue
        else:
            self.continue_name = 'continue'
            self.continue_update = self._continue
            # Explicitly enable the simplified continuation
            parameters['continue'] = True
        self.request = self.request_class(**kwargs)

        self.site._paraminfo.fetch('query+' + mod for mod in self.modules)

        limited_modules = {mod for mod in self.modules
                           if self.site._paraminfo.parameter('query+' + mod,
                                                             'limit')}

        if not limited_modules:
            self.limited_module = None
        elif len(limited_modules) == 1:
            self.limited_module = limited_modules.pop()
        else:
            # Select the first limited module in the request.
            # Query will continue as needed until limit (if any) for this
            # module is reached.
            for module in self.modules:
                if module in limited_modules:
                    self.limited_module = module
                    limited_modules.remove(module)
                    break
            pywikibot.log('%s: multiple requested query modules support limits'
                          "; using the first such module '%s' of %r"
                          % (self.__class__.__name__, self.limited_module,
                             self.modules))

            # Set limits for all remaining limited modules to max value.
            # Default values will only cause more requests and make the query
            # slower.
            for module in limited_modules:
                param = self.site._paraminfo.parameter('query+' + module,
                                                       'limit')
                prefix = self.site._paraminfo['query+' + module]['prefix']
                if self.site.logged_in() \
                   and self.site.has_right('apihighlimits'):
                    self.request[prefix + 'limit'] = int(param['highmax'])
                else:
                    self.request[prefix + 'limit'] = int(param['max'])

        if config.step > 0:
            self.api_limit = config.step
        else:
            self.api_limit = None

        if self.limited_module:
            self.prefix = self.site._paraminfo['query+'
                                               + self.limited_module]['prefix']
            self._update_limit()

        if self.api_limit is not None and 'generator' in parameters:
            self.prefix = 'g' + self.prefix

        self.limit = None
        self.query_limit = self.api_limit
        if 'generator' in parameters:
            # name of the "query" subelement key to look for when iterating
            self.resultkey = 'pages'
        else:
            self.resultkey = self.modules[0]

        # usually the (query-)continue key is the same as the querymodule,
        # but not always
        # API can return more than one query-continue key, if multiple
        # properties are requested by the query, e.g.
        # "query-continue":{
        #     "langlinks":{"llcontinue":"12188973|pt"},
        #     "templates":{"tlcontinue":"310820|828|Namespace_detect"}}
        # self.continuekey is a list
        self.continuekey = self.modules
        self._add_slots()

    def _add_slots(self):
        """Add slots to params if the site supports multi-content revisions.

        On MW 1.32+ the following query parameters require slots to be given
        when content or contentmodel is requested.

        * prop=revisions
        * prop=deletedrevisions or
        * list=allrevisions
        * list=alldeletedrevisions

        More info:
        https://lists.wikimedia.org/pipermail/mediawiki-api-announce/2018-August/000140.html
        """
        if self.site.mw_version < '1.32':
            return
        request = self.request
        # If using any deprecated_params, do not add slots. Usage of
        # these parameters together with slots is forbidden and the user will
        # get an API warning anyway.
        props = request.get('prop')
        if props:
            if 'revisions' in props:
                deprecated_params = {
                    'rvexpandtemplates', 'rvparse', 'rvdiffto', 'rvdifftotext',
                    'rvdifftotextpst', 'rvcontentformat', 'parsetree'}
                if not set(request) & deprecated_params:
                    request['rvslots'] = '*'
            if 'deletedrevisions' in props:
                deprecated_params = {
                    'drvexpandtemplates', 'drvparse', 'drvdiffto',
                    'drvdifftotext', 'drvdifftotextpst', 'drvcontentformat',
                    'parsetree'}
                if not set(request) & deprecated_params:
                    request['drvslots'] = '*'
        lists = request.get('list')
        if lists:
            if 'allrevisions' in lists:
                deprecated_params = {
                    'arvexpandtemplates', 'arvparse', 'arvdiffto',
                    'arvdifftotext', 'arvdifftotextpst', 'arvcontentformat',
                    'parsetree'}
                if not set(request) & deprecated_params:
                    request['arvslots'] = '*'
            if 'alldeletedrevisions' in lists:
                deprecated_params = {
                    'adrexpandtemplates', 'adrparse', 'adrdiffto',
                    'adrdifftotext', 'adrdifftotextpst', 'adrcontentformat',
                    'parsetree'}
                if not set(request) & deprecated_params:
                    request['adrslots'] = '*'

    def set_query_increment(self, value):
        """Set the maximum number of items to be retrieved per API query.

        If not called, the default is to ask for "max" items and let the
        API decide how many to send.

        """
        limit = int(value)

        # don't update if limit is greater than maximum allowed by API
        if self.api_limit is None:
            self.query_limit = limit
        else:
            self.query_limit = min(self.api_limit, limit)
        pywikibot.debug('%s: Set query_limit to %i.'
                        % (self.__class__.__name__, self.query_limit),
                        _logger)

    def set_maximum_items(self, value):
        """Set the maximum number of items to be retrieved from the wiki.

        If not called, most queries will continue as long as there is
        more data to be retrieved from the API.

        If set to -1 (or any negative value), the "limit" parameter will be
        omitted from the request. For some request types (such as
        prop=revisions), this is necessary to signal that only current
        revision is to be returned.

        @param value: The value of maximum number of items to be retrieved
            in total to set. Ignores None value.
        @type value: int or str or None
        """
        if value is not None:
            self.limit = int(value)

    def _update_limit(self):
        """Set query limit for self.module based on api response."""
        param = self.site._paraminfo.parameter('query+' + self.limited_module,
                                               'limit')
        if self.site.logged_in() and self.site.has_right('apihighlimits'):
            limit = int(param['highmax'])
        else:
            limit = int(param['max'])
        if self.api_limit is None or limit < self.api_limit:
            self.api_limit = limit
            pywikibot.debug(
                '{0}: Set query_limit to {1}.'.format(self.__class__.__name__,
                                                      self.api_limit),
                _logger)

    def support_namespace(self):
        """Check if namespace is a supported parameter on this query.

        Note: this function will be removed when self.set_namespace() will
              throw TypeError() instead of just giving a warning.
              See T196619.

        @return: True if yes, False otherwise
        @rtype: bool
        """
        assert(self.limited_module)  # some modules do not have a prefix
        return bool(
            self.site._paraminfo.parameter('query+' + self.limited_module,
                                           'namespace'))

    def set_namespace(self, namespaces):
        """Set a namespace filter on this query.

        @param namespaces: namespace identifiers to limit query results
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers. An empty iterator clears any
            namespace restriction.
        @raises KeyError: a namespace identifier was not resolved

        # TODO: T196619
        # @raises TypeError: module does not support a namespace parameter
        #    or a namespace identifier has an inappropriate
        #    type such as NoneType or bool, or more than one namespace
        #    if the API module does not support multiple namespaces
        """
        assert(self.limited_module)  # some modules do not have a prefix
        param = self.site._paraminfo.parameter('query+' + self.limited_module,
                                               'namespace')
        if not param:
            pywikibot.warning('{0} module does not support a namespace '
                              'parameter'.format(self.limited_module))
            warn('set_namespace() will be modified to raise TypeError '
                 'when namespace parameter is not supported. '
                 'It will be a Breaking Change, please update your code '
                 'ASAP, due date July, 31st 2019.', FutureWarning, 2)

            # TODO: T196619
            # raise TypeError('{0} module does not support a namespace '
            #                 'parameter'.format(self.limited_module))

            return False

        if isinstance(namespaces, UnicodeType):
            namespaces = namespaces.split('|')

        # Use Namespace id (int) here; Request will cast int to str
        namespaces = [ns.id for ns in
                      self.site.namespaces.resolve(namespaces)]

        if 'multi' not in param and len(namespaces) != 1:
            if self._check_result_namespace is NotImplemented:
                raise TypeError('{0} module does not support multiple '
                                'namespaces'.format(self.limited_module))
            else:
                self._namespaces = set(namespaces)
                namespaces = None

        if namespaces:
            self.request[self.prefix + 'namespace'] = namespaces
        elif self.prefix + 'namespace' in self.request:
            del self.request[self.prefix + 'namespace']

        return None

    def _query_continue(self):
        if all(key not in self.data[self.continue_name]
               for key in self.continuekey):
            pywikibot.log(
                "Missing '%s' key(s) in ['%s'] value."
                % (self.continuekey, self.continue_name))
            return True
        for query_continue_pair in self.data['query-continue'].values():
            self._add_continues(query_continue_pair)

    def _continue(self):
        self._add_continues(self.data['continue'])

    def _add_continues(self, continue_pair):
        for key, value in continue_pair.items():
            # query-continue can return ints (continue too?)
            if isinstance(value, int):
                value = str(value)
            self.request[key] = value

    def _handle_query_limit(self, prev_limit, new_limit, had_data):
        """Handle query limit."""
        if self.query_limit is None:
            return prev_limit, new_limit

        prev_limit = new_limit
        if self.limit is None:
            new_limit = self.query_limit
        elif self.limit > 0:
            if had_data:
                # self.resultkey in data in last request.submit()
                new_limit = min(self.query_limit, self.limit - self._count)
            else:
                # only "(query-)continue" returned. See Bug T74209.
                # increase new_limit to advance faster until new
                # useful data are found again.
                new_limit = min(new_limit * 2, self.query_limit)
        else:
            new_limit = None

        if new_limit and 'rvprop' in self.request \
                and 'content' in self.request['rvprop']:
            # queries that retrieve page content have lower limits
            # Note: although API allows up to 500 pages for content
            #       queries, these sometimes result in server-side errors
            #       so use 250 as a safer limit
            new_limit = min(new_limit, self.api_limit // 10, 250)

        if new_limit is not None:
            self.request[self.prefix + 'limit'] = str(new_limit)

        if prev_limit != new_limit:
            pywikibot.debug(
                '{name}: query_limit: {query}, api_limit: {api}, '
                'limit: {limit}, new_limit: {new}, count: {count}\n'
                '{name}: {prefix}limit: {value}'
                .format(name=self.__class__.__name__,
                        query=self.query_limit,
                        api=self.api_limit,
                        limit=self.limit,
                        new=new_limit,
                        count=self._count,
                        prefix=self.prefix,
                        value=self.request[self.prefix + 'limit']),
                _logger)
        return prev_limit, new_limit

    def _get_resultdata(self):
        """Get resultdata and verify result."""
        resultdata = keys = self.data['query'][self.resultkey]
        if isinstance(resultdata, dict):
            keys = list(resultdata.keys())
            if 'results' in resultdata:
                resultdata = resultdata['results']
            elif 'pageids' in self.data['query']:
                # this ensures that page data will be iterated
                # in the same order as received from server
                resultdata = [resultdata[k]
                              for k in self.data['query']['pageids']]
            else:
                resultdata = [resultdata[k]
                              for k in sorted(resultdata.keys())]
        pywikibot.debug('{name} received {keys}; limit={limit}'
                        .format(name=self.__class__.__name__,
                                keys=keys, limit=self.limit),
                        _logger)
        return resultdata

    def _extract_results(self, resultdata):
        """Extract results from resultdata."""
        for item in resultdata:
            result = self.result(item)
            if self._namespaces:
                if not self._check_result_namespace(result):
                    continue
            yield result
            if isinstance(item, dict) \
                    and set(self.continuekey) & set(item.keys()):
                # if we need to count elements contained in items in
                # self.data["query"]["pages"], we want to count
                # item[self.continuekey] (e.g. 'revisions') and not
                # self.resultkey (i.e. 'pages')
                for key in set(self.continuekey) & set(item.keys()):
                    self._count += len(item[key])
            # otherwise we proceed as usual
            else:
                self._count += 1
            # note: self.limit could be -1
            if self.limit and 0 < self.limit <= self._count:
                raise RuntimeError(
                    'QueryGenerator._extract_results reached the limit')

    def __iter__(self):
        """Submit request and iterate the response based on self.resultkey.

        Continues response as needed until limit (if any) is reached.

        """
        previous_result_had_data = True
        prev_limit = new_limit = None

        self._count = 0
        while True:
            prev_limit, new_limit = self._handle_query_limit(
                prev_limit, new_limit, previous_result_had_data)
            if not hasattr(self, 'data'):
                self.data = self.request.submit()
            if not self.data or not isinstance(self.data, dict):
                pywikibot.debug(
                    '{}: stopped iteration because no dict retrieved from api.'
                    .format(self.__class__.__name__),
                    _logger)
                return
            if 'query' in self.data and self.resultkey in self.data['query']:
                resultdata = self._get_resultdata()
                if 'normalized' in self.data['query']:
                    self.normalized = {
                        item['to']: item['from']
                        for item in self.data['query']['normalized']}
                else:
                    self.normalized = {}
                try:
                    for result in self._extract_results(resultdata):
                        yield result
                except RuntimeError:
                    return
                # self.resultkey in data in last request.submit()
                previous_result_had_data = True
            else:
                if 'query' not in self.data:
                    pywikibot.log("%s: 'query' not found in api response." %
                                  self.__class__.__name__)
                    pywikibot.log(UnicodeType(self.data))
                # if (query-)continue is present, self.resultkey might not have
                # been fetched yet
                if self.continue_name not in self.data:
                    # No results.
                    return
                # self.resultkey not in data in last request.submit()
                # only "(query-)continue" was retrieved.
                previous_result_had_data = False
            if self.modules[0] == 'random':
                # "random" module does not return "(query-)continue"
                # now we loop for a new random query
                del self.data  # a new request is needed
                continue
            if self.continue_name not in self.data:
                return
            if self.continue_update():
                return

            del self.data  # a new request with (query-)continue is needed

    def result(self, data):
        """Process result data as needed for particular subclass."""
        return data


class PageGenerator(QueryGenerator):

    """Iterator for response to a request of type action=query&generator=foo.

    This class can be used for any of the query types that are listed in the
    API documentation as being able to be used as a generator. Instances of
    this class iterate Page objects.

    """

    def __init__(self, generator, g_content=False, **kwargs):
        """
        Initializer.

        Required and optional parameters are as for C{Request}, except that
        action=query is assumed and generator is required.

        @param generator: the "generator=" type from api.php
        @type generator: str
        @param g_content: if True, retrieve the contents of the current
            version of each Page (default False)

        """
        # If possible, use self.request after __init__ instead of appendParams
        def appendParams(params, key, value):
            if key in params:
                params[key] += '|' + value
            else:
                params[key] = value
        kwargs = self._clean_kwargs(kwargs)
        parameters = kwargs['parameters']
        # get some basic information about every page generated
        appendParams(parameters, 'prop', 'info|imageinfo|categoryinfo')
        if g_content:
            # retrieve the current revision
            appendParams(parameters, 'prop', 'revisions')
            appendParams(parameters, 'rvprop',
                         'ids|timestamp|flags|comment|user|content')
        if not ('inprop' in parameters
                and 'protection' in parameters['inprop']):
            appendParams(parameters, 'inprop', 'protection')
        appendParams(parameters, 'iiprop',
                     'timestamp|user|comment|url|size|sha1|metadata')
        appendParams(parameters, 'iilimit', 'max')  # T194233
        parameters['generator'] = generator
        QueryGenerator.__init__(self, **kwargs)
        self.resultkey = 'pages'  # element to look for in result
        self.props = self.request['prop']

    def result(self, pagedata):
        """Convert page dict entry from api to Page object.

        This can be overridden in subclasses to return a different type
        of object.

        """
        p = pywikibot.Page(self.site, pagedata['title'], pagedata['ns'])
        ns = pagedata['ns']
        # Upcast to proper Page subclass.
        if ns == 2:
            p = pywikibot.User(p)
        elif ns == 6:
            p = pywikibot.FilePage(p)
        elif ns == 14:
            p = pywikibot.Category(p)
        update_page(p, pagedata, self.props)
        return p


@deprecated('PageGenerator', since='20141106')
class CategoryPageGenerator(PageGenerator):

    """Like PageGenerator, but yields Category objects instead of Pages."""

    pass


@deprecated('PageGenerator', since='20141106')
class ImagePageGenerator(PageGenerator):

    """Like PageGenerator, but yields FilePage objects instead of Pages."""

    pass


class PropertyGenerator(QueryGenerator):

    """Iterator for queries of type action=query&prop=foo.

    See the API documentation for types of page properties that can be
    queried.

    This iterator yields one or more dict object(s) corresponding
    to each "page" item(s) from the API response; the calling module has to
    decide what to do with the contents of the dict. There will be one
    dict for each page queried via a titles= or ids= parameter (which must
    be supplied when instantiating this class).

    """

    def __init__(self, prop, **kwargs):
        """
        Initializer.

        Required and optional parameters are as for C{Request}, except that
        action=query is assumed and prop is required.

        @param prop: the "prop=" type from api.php
        @type prop: str

        """
        kwargs = self._clean_kwargs(kwargs, prop=prop)
        QueryGenerator.__init__(self, **kwargs)
        self._props = frozenset(prop.split('|'))
        self.resultkey = 'pages'

    @property
    def props(self):
        """The requested property names."""
        return self._props

    def __iter__(self):
        """Yield results."""
        self._previous_dicts = {}
        for result in super(PropertyGenerator, self).__iter__():
            yield result
        for result in self._previous_dicts.values():
            yield result

    def _extract_results(self, resultdata):
        """Yield completed page_data of consecutive API requests."""
        for d in self._fully_retrieved_data_dicts(resultdata):
            yield d
        for data_dict in super(PropertyGenerator, self)._extract_results(
            resultdata
        ):
            d = self._previous_dicts.setdefault(data_dict['title'], data_dict)
            if d is not data_dict:
                self._update_old_result_dict(d, data_dict)

    def _fully_retrieved_data_dicts(self, resultdata):
        """Yield items of self._previous_dicts that are not in resultdata."""
        resuldata_titles = {d['title'] for d in resultdata}
        for prev_title, prev_dict in self._previous_dicts.copy().items():
            if prev_title not in resuldata_titles:
                yield prev_dict
                del self._previous_dicts[prev_title]

    @staticmethod
    def _update_old_result_dict(old_dict, new_dict):
        """Update old result dict with new_dict."""
        for k, v in new_dict.items():
            if k not in old_dict:
                old_dict[k] = v
                continue
            if isinstance(v, list):
                old_dict[k].extend(v)
                continue
            assert isinstance(v, (UnicodeType, int)), (
                'continued API result had an unexpected type: %s' % type(v))


class ListGenerator(QueryGenerator):

    """Iterator for queries of type action=query&list=foo.

    See the API documentation for types of lists that can be queried. Lists
    include both site-wide information (such as 'allpages') and page-specific
    information (such as 'backlinks').

    This iterator yields a dict object for each member of the list returned
    by the API, with the format of the dict depending on the particular list
    command used. For those lists that contain page information, it may be
    easier to use the PageGenerator class instead, as that will convert the
    returned information into a Page object.

    """

    def __init__(self, listaction, **kwargs):
        """
        Initializer.

        Required and optional parameters are as for C{Request}, except that
        action=query is assumed and listaction is required.

        @param listaction: the "list=" type from api.php
        @type listaction: str

        """
        kwargs = self._clean_kwargs(kwargs, list=listaction)
        QueryGenerator.__init__(self, **kwargs)


class LogEntryListGenerator(ListGenerator):

    """
    Iterator for queries of list 'logevents'.

    Yields LogEntry objects instead of dicts.
    """

    def __init__(self, logtype=None, **kwargs):
        """Initializer."""
        ListGenerator.__init__(self, 'logevents', **kwargs)

        from pywikibot import logentries
        self.entryFactory = logentries.LogEntryFactory(self.site, logtype)

    def result(self, pagedata):
        """Instantiate LogEntry from data from api."""
        return self.entryFactory.create(pagedata)

    def _check_result_namespace(self, result):
        """Return True if result.ns() is in self._namespaces."""
        return result.ns() in self._namespaces


class LoginManager(login.LoginManager):

    """Supply getCookie() method to use API interface."""

    # API login parameters mapping
    mapping = {
        'user': ('lgname', 'username'),
        'password': ('lgpassword', 'password'),
        'ldap': ('lgdomain', 'domain'),
        'token': ('lgtoken', 'logintoken'),
        'result': ('result', 'status'),
        'success': ('Success', 'PASS'),
        'fail': ('Failed', 'FAIL'),
        'reason': ('reason', 'message')
    }

    def keyword(self, key):
        """Get API keyword from mapping."""
        index = 0 if self.action == 'login' else 1
        return self.mapping[key][index]

    @remove_last_args(arg_names=['remember, captchaId, captchaAnswer'])
    def getCookie(self):
        """Login to the site.

        Note, this doesn't actually return or do anything with cookies.
        The threadedhttp module takes care of all the cookie stuff,
        this just has a legacy name for now and should be renamed in the
        future.

        @return: empty string if successful, throws exception on failure

        """
        if hasattr(self, '_waituntil'):
            if datetime.datetime.now() < self._waituntil:
                diff = self._waituntil - datetime.datetime.now()
                pywikibot.warning(
                    'Too many tries, waiting {} seconds before retrying.'
                    .format(diff.seconds))
                pywikibot.sleep(diff.seconds)

        below_mw_1_27 = self.site.mw_version < '1.27'

        if '@' in self.login_name or '@' in self.password or below_mw_1_27:
            # Since MW 1.27 only for bot passwords.
            # Bot passwords username contains @,
            # otherwise @ is not allowed in usernames.
            # @ in bot password is deprecated,
            # but we don't want to break bots using it.
            self.action = 'login'
        else:
            # Standard login request since MW 1.27
            self.action = 'clientlogin'

        # prepare default login parameters
        parameters = {'action': self.action,
                      self.keyword('user'): self.login_name,
                      self.keyword('password'): self.password}

        if self.action == 'clientlogin':
            # clientlogin requires non-empty loginreturnurl
            parameters['loginreturnurl'] = 'https://example.com'
            parameters['rememberMe'] = '1'

        # base login request
        login_request = self.site._request(use_get=False,
                                           parameters=parameters)

        if self.site.family.ldapDomain:
            login_request[self.keyword('ldap')] = self.site.family.ldapDomain

        self.site._loginstatus = -2  # IN_PROGRESS
        while True:
            # get token using meta=tokens if supported
            if not below_mw_1_27:
                login_request[self.keyword('token')] = self.get_login_token()

            # try to login
            try:
                login_result = login_request.submit()
            except APIError as e:
                login_result = {'error': e.__dict__}

            # clientlogin response can be clientlogin or error
            if self.action in login_result:
                response = login_result[self.action]
                result_key = self.keyword('result')
            elif 'error' in login_result:
                response = login_result['error']
                result_key = 'code'
            else:
                raise RuntimeError('Unexpected API login response key.')

            status = response[result_key]
            fail_reason = response.get(self.keyword('reason'), '')
            if status == self.keyword('success'):
                return ''
            elif status in ('NeedToken', 'WrongToken', 'badtoken'):
                token = response.get('token')
                if token and below_mw_1_27:
                    # fetched token using action=login
                    login_request['lgtoken'] = token
                    pywikibot.log('Received login token, '
                                  'proceed with login.')
                else:
                    # if incorrect login token was used,
                    # force relogin and generate fresh one
                    pywikibot.error('Received incorrect login token. '
                                    'Forcing re-login.')
                    # invalidate superior wiki cookies (T224712)
                    _invalidate_superior_cookies(self.site.family)
                continue
            elif (status == 'Throttled' or status == self.keyword('fail')
                  and (response['messagecode'] == 'login-throttled'
                  or 'wait' in fail_reason)):
                match = re.search(r'(\d+) (seconds|minutes)', fail_reason)
                if match:
                    delta = datetime.timedelta(
                        **{match.group(2): int(match.group(1))})
                wait = response.get('wait')
                if wait:
                    delta = datetime.timedelta(seconds=int(wait))
                self._waituntil = datetime.datetime.now() + delta
                break
            else:
                break
        if 'error' in login_result:
            raise APIError(**response)
        info = fail_reason
        raise APIError(code=status, info=info)

    def storecookiedata(self, data):
        """Ignore data; cookies are set by threadedhttp module."""
        http.cookie_jar.save()

    def get_login_token(self):
        """Fetch login token from action=query&meta=tokens.

        Requires MediaWiki >= 1.27.

        @return: login token
        @rtype: str
        """
        if self.site.mw_version < '1.27':
            raise NotImplementedError('The method get_login_token() requires '
                                      'at least MediaWiki version 1.27.')
        login_token_request = self.site._request(
            use_get=False,
            parameters={'action': 'query', 'meta': 'tokens', 'type': 'login'},
        )
        login_token_result = login_token_request.submit()
        return login_token_result['query']['tokens'].get('logintoken')


def encode_url(query):
    """
    Encode parameters to pass with a url.

    Reorder parameters so that token parameters go last and call wraps
    L{urlencode}. Return an HTTP URL query fragment which complies with
    https://www.mediawiki.org/wiki/API:Edit#Parameters
    (See the 'token' bullet.)

    @param query: keys and values to be uncoded for passing with a url
    @type query: mapping object or a sequence of two-element tuples
    @return: encoded parameters with token parameters at the end
    @rtype: str
    """
    if hasattr(query, 'items'):
        query = list(query.items())

    if PY2:
        def _encode(x):
            if isinstance(x, UnicodeType):
                return x.encode('utf-8')
            else:
                return x
        query = [(pair[0], _encode(pair[1])) for pair in query]

    # parameters ending on 'token' should go last
    # wpEditToken should go very last
    query.sort(key=lambda x: x[0].lower().endswith('token')
               + (x[0] == 'wpEditToken'))
    return urlencode(query)


def _update_pageid(page, pagedict):
    """Update pageid."""
    if 'pageid' in pagedict:
        page._pageid = int(pagedict['pageid'])
    elif 'missing' in pagedict:
        page._pageid = 0  # Non-existent page
    else:
        # Something is wrong.
        if page.site.sametitle(page.title(), pagedict['title']):
            if 'invalid' in pagedict:
                raise InvalidTitle('{}: {}'.format(page,
                                                   pagedict['invalidreason']))
        if int(pagedict['ns']) < 0:
            raise UnsupportedPage(page)
        raise RuntimeError(
            "Page {} has neither 'pageid' nor 'missing' attribute"
            .format(pagedict['title']))


def _update_contentmodel(page, pagedict):
    """Update page content model."""
    page._contentmodel = pagedict.get('contentmodel')  # can be None

    if (page._contentmodel
            and page._contentmodel == 'proofread-page'
            and 'proofread' in pagedict):
        page._quality = pagedict['proofread']['quality']
        page._quality_text = pagedict['proofread']['quality_text']


def _update_protection(page, pagedict):
    """Update page protection."""
    if 'restrictiontypes' in pagedict:
        page._applicable_protections = set(pagedict['restrictiontypes'])
    else:
        page._applicable_protections = None
    page._protection = {item['type']: (item['level'], item['expiry'])
                        for item in pagedict['protection']}


def _update_revisions(page, revisions):
    """Update page revisions."""
    # TODO: T102735: Use the page content model for <1.21
    for rev in revisions:
        revision = pywikibot.page.Revision(
            revid=rev['revid'],
            timestamp=pywikibot.Timestamp.fromISOformat(rev['timestamp']),
            user=rev.get('user', ''),
            anon='anon' in rev,
            comment=rev.get('comment', ''),
            minor='minor' in rev,
            slots=rev.get('slots'),  # MW 1.32+
            text=rev.get('*'),  # b/c
            rollbacktoken=rev.get('rollbacktoken'),
            parentid=rev.get('parentid'),
            contentmodel=rev.get('contentmodel'),  # b/c
            sha1=rev.get('sha1')
        )
        page._revisions[revision.revid] = revision


def _update_templates(page, templates):
    """Update page templates."""
    templ_pages = [pywikibot.Page(page.site, tl['title']) for tl in templates]
    if hasattr(page, '_templates'):
        page._templates.extend(templ_pages)
    else:
        page._templates = templ_pages


def _update_langlinks(page, langlinks):
    """Update page langlinks."""
    links = [pywikibot.Link.langlinkUnsafe(link['lang'], link['*'],
                                           source=page.site)
             for link in langlinks]

    if hasattr(page, '_langlinks'):
        page._langlinks.extend(links)
    else:
        page._langlinks = links


def _update_coordinates(page, coordinates):
    """Update page coordinates."""
    coords = []
    for co in coordinates:
        coord = pywikibot.Coordinate(lat=co['lat'],
                                     lon=co['lon'],
                                     typ=co.get('type', ''),
                                     name=co.get('name', ''),
                                     dim=int(co.get('dim', 0)) or None,
                                     globe=co['globe'],  # See [[gerrit:67886]]
                                     primary='primary' in co
                                     )
        coords.append(coord)
    page._coords = coords


def update_page(page, pagedict, props=[]):
    """Update attributes of Page object page, based on query data in pagedict.

    @param page: object to be updated
    @type page: pywikibot.page.Page
    @param pagedict: the contents of a "page" element of a query response
    @type pagedict: dict
    @param props: the property names which resulted in pagedict. If a missing
        value in pagedict can indicate both 'false' and 'not present' the
        property which would make the value present must be in the props
        parameter.
    @type props: iterable of string
    @raises pywikibot.exceptions.InvalidTitle: Page title is invalid
    @raises pywikibot.exceptions.UnsupportedPage: Page with namespace < 0
        is not supported yet
    """
    _update_pageid(page, pagedict)
    _update_contentmodel(page, pagedict)

    if 'info' in props:
        page._isredir = 'redirect' in pagedict

    if 'touched' in pagedict:
        page._timestamp = pagedict['touched']

    if 'protection' in pagedict:
        _update_protection(page, pagedict)

    if 'revisions' in pagedict:
        _update_revisions(page, pagedict['revisions'])

    if 'lastrevid' in pagedict:
        page.latest_revision_id = pagedict['lastrevid']
        del page.text

    if 'imageinfo' in pagedict:
        assert(isinstance(page, pywikibot.FilePage))
        page._load_file_revisions(pagedict['imageinfo'])

    if 'categoryinfo' in pagedict:
        page._catinfo = pagedict['categoryinfo']

    if 'templates' in pagedict:
        _update_templates(page, pagedict['templates'])
    elif 'templates' in props:
        page._templates = []

    if 'langlinks' in pagedict:
        _update_langlinks(page, pagedict['langlinks'])
    elif 'langlinks' in props:
        page._langlinks = []

    if 'coordinates' in pagedict:
        _update_coordinates(page, pagedict['coordinates'])

    if 'pageimage' in pagedict:
        page._pageimage = pywikibot.FilePage(page.site, pagedict['pageimage'])

    if 'pageprops' in pagedict:
        page._pageprops = pagedict['pageprops']

    if 'preload' in pagedict:
        page._preloadedtext = pagedict['preload']

    if 'flowinfo' in pagedict:
        page._flowinfo = pagedict['flowinfo']['flow']

    if 'lintId' in pagedict:
        page._lintinfo = pagedict
        page._lintinfo.pop('pageid')
        page._lintinfo.pop('title')
        page._lintinfo.pop('ns')
