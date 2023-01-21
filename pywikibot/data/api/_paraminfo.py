"""Object representing API parameter information."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
from collections.abc import Container, Sized
from typing import Any, Optional, Union

import pywikibot
from pywikibot import config
from pywikibot.backports import Dict, removeprefix
from pywikibot.tools.itertools import itergroup


__all__ = ['ParamInfo']


class ParamInfo(Sized, Container):

    """
    API parameter information data object.

    Provides cache aware fetching of parameter information.

    It does not support the format modules.
    """

    paraminfo_keys = frozenset(['modules', 'querymodules', 'formatmodules',
                                'mainmodule', 'pagesetmodule'])

    root_modules = frozenset(['main', 'pageset'])

    init_modules = frozenset(['main', 'paraminfo'])

    def __init__(
        self,
        site,
        preloaded_modules=None,
        modules_only_mode=None
    ) -> None:
        """
        Initializer.

        :param preloaded_modules: API modules to preload
        :type preloaded_modules: set of string
        :param modules_only_mode: use the 'modules' only syntax for API request
        :type modules_only_mode: bool or None to only use default, which True
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

    def _add_submodules(self, name, modules) -> None:
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

        # The paraminfo api deprecated the old request syntax of
        # querymodules='info'; to avoid warnings sites with 1.25wmf4+
        # must only use 'modules' parameter.
        if self.modules_only_mode is None:
            self.modules_only_mode = mw_ver >= '1.25wmf4'
            if self.modules_only_mode:
                self.paraminfo_keys = frozenset(['modules'])

        # Assume that by v1.26, it will be desirable to prefetch 'query'
        if mw_ver > '1.26':
            self.preloaded_modules |= {'query'}

        self._fetch(self.preloaded_modules)

        main_modules_param = self.parameter('main', 'action')
        assert main_modules_param
        assert 'type' in main_modules_param
        assert isinstance(main_modules_param['type'], list)
        assert self._action_modules == set(main_modules_param['type'])

        # While deprecated with warning in 1.25, paraminfo param 'querymodules'
        # provides a list of all query modules. This will likely be removed
        # from the API in the future, in which case the fallback is the use
        # the same data available in the paraminfo for query.
        query_modules_param = self.parameter('paraminfo', 'querymodules')

        if 'limit' not in query_modules_param:
            raise RuntimeError('"limit" not found in query modules')
        self._limit = query_modules_param['limit']

        if query_modules_param and 'type' in query_modules_param:
            # 'type' is the list of modules
            self._add_submodules('query', query_modules_param['type'])

        if 'query' not in self._modules:
            assert 'query' not in self._paraminfo
            self._fetch({'query'})
        assert 'query' in self._modules

    def _emulate_pageset(self) -> None:
        """Emulate the pageset module, which existed until MW 1.24."""
        # pageset isn't a module in the new system, so it is emulated, with
        # the paraminfo from the query module.
        assert 'query' in self._paraminfo

        self._paraminfo['pageset'] = {
            'name': 'pageset',
            'path': 'pageset',
            'classname': 'ApiPageSet',
            'prefix': '',
            'readrights': '',
            'helpurls': [],
            'parameters': self._paraminfo['query']['parameters']
        }

    @staticmethod
    def _modules_to_set(modules) -> set:
        """Return modules as a set.

        :type modules: iterable or str
        """
        if isinstance(modules, str):
            return set(modules.split('|'))
        return set(modules)

    def fetch(self, modules) -> None:
        """
        Fetch paraminfo for multiple modules.

        No exception is raised when paraminfo for a module does not exist.
        Use __getitem__ to cause an exception if a module does not exist.

        :param modules: API modules to load
        :type modules: iterable or str
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

    def _fetch(self, modules: Union[set, frozenset]) -> None:
        """
        Fetch paraminfo for multiple modules without initializing beforehand.

        :param modules: API modules to load and which haven't been loaded yet.
        """
        def module_generator():
            """A generator yielding batches of modules."""
            i = itergroup(sorted(modules), self._limit)
            for batch in i:
                for failed_module in failed_modules:
                    yield [failed_module]
                del failed_modules[:]
                yield batch

        modules -= set(self._paraminfo)
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
                pywikibot.debug('paraminfo fetch: removed pageset')
                module_batch.remove('pageset')
                # If this occurred during initialisation,
                # also record it in the preloaded_modules.
                # (at least so tests know an extra load was intentional)
                if 'query' not in self._paraminfo:
                    pywikibot.debug('paraminfo batch: added query')
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
                params['querymodules'] = [removeprefix(mod, 'query+')
                                          for mod in module_batch
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
                pywikibot.log('Inconsistency in batch "{}"; rerequest '
                              'separately'.format(missing_modules))
                failed_modules.extend(missing_modules)

            # Remove all modules which weren't requested, we can't be sure that
            # they are valid
            for path in list(normalized_result):
                if path not in module_batch:
                    del normalized_result[path]

            self._paraminfo.update(normalized_result)
            for mod in normalized_result.values():
                self._generate_submodules(mod['path'])

        if 'pageset' in modules and 'pageset' not in self._paraminfo:
            self._emulate_pageset()

    def _generate_submodules(self, module) -> None:
        """Check and generate submodules for the given module."""
        parameters = self._paraminfo[module].get('parameters', [])
        submodules = set()
        # Advanced submodule into added to MW API in df80f1ea
        if self.site.mw_version >= '1.26wmf9':
            # This is supplying submodules even if they aren't submodules
            # of the given module so skip those
            for param in parameters:
                if module == 'main' and param['name'] == 'format' \
                   or 'submodules' not in param:
                    continue

                for submodule in param['submodules'].values():
                    if '+' in submodule:
                        parent, child = submodule.rsplit('+', 1)
                    else:
                        parent, child = 'main', submodule
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
                if 'submodules' in param \
                   and (module != 'main' or param['name'] != 'format'):
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
            else:
                param = {}
            assert param['name'] == 'generator' \
                and submodules >= set(param['type'])

    def _normalize_modules(self, modules) -> set:
        """Add query+ to any query module name not also in action modules."""
        # Users will supply the wrong type, and expect it to work.
        modules = self._modules_to_set(modules)

        assert self._action_modules

        return {'query+' + mod
                if '+' not in mod and mod in self.query_modules
                and mod not in self._action_modules
                else mod
                for mod in modules}

    def normalize_modules(self, modules) -> set:
        """
        Convert the modules into module paths.

        Add query+ to any query module name not also in action modules.

        :return: The modules converted into a module paths
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
                    name = removeprefix(php_class, 'Api').lower()
                    if name not in ('main', 'pageset'):
                        pywikibot.warning('Unknown paraminfo module "{}"'
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
                        pywikibot.warning('Path "{}" is ambiguous.'
                                          .format(path))
                    else:
                        pywikibot.log(f'Found another path "{path}"')
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
        if '+' not in key:
            return self._paraminfo['query+' + key]
        raise KeyError(key)

    def __contains__(self, key) -> bool:
        """Return whether the key is valid."""
        try:
            self[key]
            return True
        except KeyError:
            return False

    def __len__(self) -> int:
        """Return number of cached modules."""
        return len(self._paraminfo)

    def parameter(
        self,
        module: str,
        param_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get details about one modules parameter.

        Returns None if the parameter does not exist.

        :param module: API module name
        :param param_name: parameter name in the module
        :return: metadata that describes how the parameter may be used
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
            raise ValueError(f"paraminfo for '{module}' not loaded")

        try:
            params = module['parameters']
        except KeyError:
            pywikibot.warning(f"module '{module}' has no parameters")
            return None

        param_data = [param for param in params
                      if param['name'] == param_name]

        if not param_data:
            return None

        if len(param_data) != 1:
            raise RuntimeError(
                'parameter data length is eiter empty or not unique.\n{}'
                .format(param_data))
        return param_data[0]

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

    def submodules(self, name: str, path: bool = False) -> set:
        """
        Set of all submodules.

        :param name: The name of the parent module.
        :param path: Whether the path and not the name is returned.
        :return: The names or paths of the submodules.
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
        return {f'{prefix}+{mod}' for mod in modules}

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

    def attributes(self, attribute: str, modules: Optional[set] = None):
        """
        Mapping of modules with an attribute to the attribute value.

        It will include all modules which have that attribute set, also if that
        attribute is empty or set to False.

        :param attribute: attribute name
        :param modules: modules to include. If None (default), it'll load all
            modules including all submodules using the paths.
        :rtype: dict using modules as keys
        """
        if modules is None:
            modules = self.module_paths
        self.fetch(modules)

        return {mod: self[mod][attribute]
                for mod in modules if attribute in self[mod]}
