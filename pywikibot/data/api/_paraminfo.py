"""Object representing API parameter information."""
#
# (C) Pywikibot team, 2014-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from collections.abc import Container, Sized
from typing import Any

import pywikibot
from pywikibot import config
from pywikibot.backports import Iterable, batched
from pywikibot.tools import classproperty, deprecated, remove_last_args


__all__ = ['ParamInfo']


class ParamInfo(Sized, Container):

    """API parameter information data object.

    Provides cache aware fetching of parameter information.

    .. seealso:: :api:`Parameter information`
    """

    root_modules = frozenset(['main'])
    init_modules = frozenset(['main', 'paraminfo'])
    param_modules = ('list', 'meta', 'prop')

    @remove_last_args(['modules_only_mode'])
    def __init__(self,
                 site,
                 preloaded_modules: set[str] | None = None) -> None:
        """Initializer.

        .. deprecated:: 8.4
           the *modules_only_mode* parameter

        :param preloaded_modules: API modules to preload
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

        self._preloaded_modules = self.init_modules
        if preloaded_modules:
            self._preloaded_modules |= set(preloaded_modules)

    def _add_submodules(self, name: str,
                        modules: set[str] | dict[str, str]) -> None:
        """Add the modules to the internal cache."""
        assert '+' not in name
        if name == 'main':
            # The main module behaves differently as it has no prefix
            if self._action_modules:
                assert modules == self._action_modules
            else:
                self._action_modules = modules
        elif name in self._modules:
            # update required to updates from dict and set
            self._modules[name].update(modules)
        else:
            self._modules[name] = modules

    def _init(self):
        assert ('query' in self._modules) is ('main' in self._paraminfo)

        # Skip if ParamInfo is already initialized
        if 'query' in self._modules:
            return

        # Assume that it will be desirable to prefetch 'query'
        self._preloaded_modules |= {'query'}

        self._fetch(self._preloaded_modules)

        main_modules_param = self.parameter('main', 'action')
        assert main_modules_param
        assert 'type' in main_modules_param
        assert isinstance(main_modules_param['type'], list)
        assert self._action_modules == set(main_modules_param['type'])
        assert 'query' in self._modules
        assert 'query' in self._paraminfo

        # Retrieve all query submodules
        self._limit = 50
        for param in self.param_modules:
            query_modules_param = self.parameter('query', param)
            self._limit = min(query_modules_param['limit'], self._limit)
            self._add_submodules('query', query_modules_param['submodules'])

    @staticmethod
    def _modules_to_set(modules: Iterable | str) -> set[str]:
        """Return modules as a set."""
        if isinstance(modules, str):
            return set(modules.split('|'))
        return set(modules)

    def fetch(self, modules: Iterable | str) -> None:
        """Fetch paraminfo for multiple modules.

        No exception is raised when paraminfo for a module does not
        exist. ``paraminfo[module]`` to cause an exception if a module
        does not exist.

        :param modules: API modules to load
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

    def _fetch(self, modules: set | frozenset) -> None:
        """Get paraminfo for multiple modules without initializing beforehand.

        :param modules: API modules to load and which haven't been loaded yet.
        """
        def module_generator():
            """A generator yielding batches of modules."""
            # T340617: self._limit is not set for the first modules
            # which is frozenset({'paraminfo', 'query', 'main'})
            for batch in batched(sorted(modules), self._limit or 50):
                for failed_module in failed_modules:
                    yield [failed_module]
                failed_modules.clear()
                yield list(batch)

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
        for module_batch in module_generator():
            params = {
                'action': 'paraminfo',
                'modules': module_batch,
            }

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
                pywikibot.warning(
                    f'The module "{normalized_result["name"]}" '
                    f'("{normalized_result["path"]}") was returned as path '
                    f'even though "{missing_modules[0]}" was requested'
                )
                normalized_result['path'] = missing_modules[0]
                normalized_result['name'] = missing_modules[0].rsplit('+')[0]
                normalized_result = {missing_modules[0]: normalized_result}
            elif len(module_batch) > 1 and missing_modules:
                # Rerequest the missing ones separately
                pywikibot.log(f'Inconsistency in batch "{missing_modules}";'
                              ' rerequest separately')
                failed_modules.extend(missing_modules)

            # Remove all modules which weren't requested, we can't be sure that
            # they are valid
            for path in list(normalized_result):
                if path not in module_batch:
                    del normalized_result[path]

            self._paraminfo.update(normalized_result)
            for mod in normalized_result.values():
                self._generate_submodules(mod['path'])

    def _generate_submodules(self, module) -> None:
        """Check and generate submodules for the given module."""
        parameters = self._paraminfo[module].get('parameters', [])
        submodules = set()

        # This is supplying submodules even if they aren't submodules
        # of the given module so skip those
        for param in parameters:
            if module == 'main' and param['name'] == 'format' \
               or 'submodules' not in param:
                continue

            for child, submodule in param['submodules'].items():
                if '+' in submodule:
                    parent = submodule.rsplit('+', 1)[0]
                else:
                    parent = 'main'
                if parent == module:
                    submodules.add(child)

        if submodules:
            self._add_submodules(module, submodules)

        if module == 'query':
            # Verify that submodules from generator are just a subset of the
            # prop/list/meta modules.
            for param in parameters:
                if param['name'] == 'generator':
                    break
            else:
                raise RuntimeError(
                    "'query' module has no 'generator' parameter")

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
        """Convert the modules into module paths.

        Add query+ to any query module name not also in action modules.

        :return: The modules converted into a module paths
        """
        self._init()
        return self._normalize_modules(modules)

    @staticmethod
    def normalize_paraminfo(data: dict[str, Any]) -> dict[str, Any]:
        """Convert API JSON into a new data structure with path as key.

        For duplicate paths, the value will be False.

        .. versionchanged:: 8.4
           ``normalize_paraminfo`` became a staticmethod.
        """
        result_data = {}
        modules_data = data['paraminfo'].get('modules', [])
        for mod_data in modules_data:
            if 'missing' in mod_data:
                continue

            path = mod_data['path']
            if path not in result_data:
                result_data[path] = mod_data
            elif result_data[path] is not False:
                # Only warn first time
                result_data[path] = False
                pywikibot.warning(f'Path "{path}" is ambiguous.')
            else:
                pywikibot.log(f'Found another path "{path}"')

        return result_data

    def __getitem__(self, key):
        """Return a paraminfo module for the module path, caching it.

        Use the module path, such as 'query+x', to obtain the paraminfo
        for submodule 'x' in the query module.

        If the key does not include a '+' and is not present in the top
        level of the API, it will fallback to looking for the key
        'query+x'.
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
    ) -> dict[str, Any] | None:
        """Get details about one modules parameter.

        Returns None if the parameter does not exist.

        :param module: API module name
        :param param_name: parameter name in the module
        :return: metadata that describes how the parameter may be used
        """
        try:
            module = self[module]
        except KeyError:
            raise ValueError(f"paraminfo for '{module}' not loaded")

        try:
            params = module['parameters']
        except KeyError:
            pywikibot.warning(f"module '{module}' has no parameters")
            return None

        param_data = [param for param in params if param['name'] == param_name]

        if not param_data:
            return None

        if len(param_data) != 1:
            raise RuntimeError(f'parameter data length is either empty or not '
                               f'unique.\n{param_data}')
        return param_data[0]

    @property
    def module_paths(self):
        """Set of all modules using their paths."""
        # Load the submodules of all action modules available
        self.fetch(self.action_modules)
        modules = set(self.action_modules)
        for parent_module in self._modules:
            submodules = self.submodules(parent_module, path=True)
            assert not submodules & modules
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

    def submodules(self, name: str, path: bool = False) -> set[str]:
        """Set of all submodules.

        :param name: The name of the parent module.
        :param path: Whether the path and not the name is returned.
        :return: The names or paths of the submodules.
        """
        if name not in self._modules:
            self.fetch([name])
        submodules = self._modules[name]
        if path:
            # prefix submodules
            submodules = {f'{name}+{mod}' for mod in submodules}
        return submodules

    @property
    def prefix_map(self) -> dict[str, str]:
        """Mapping of module to its prefix for all modules with a prefix.

        This loads paraminfo for all modules.
        """
        if not self._prefix_map:
            self._prefix_map = {
                module: prefix
                for module, prefix in self.attributes('prefix').items()
                if prefix
            }
        return self._prefix_map.copy()

    def attributes(self, attribute: str,
                   modules: set | None = None) -> dict[str, Any]:
        """Mapping of modules with an attribute to the attribute value.

        It will include all modules which have that attribute set, also
        if that attribute is empty or set to False.

        :param attribute: attribute name
        :param modules: modules to include. If None (default), it'll
            load all modules including all submodules using the paths.
        :return: dict using modules as keys
        """
        if modules is None:
            modules = self.module_paths
        self.fetch(modules)

        return {mod: self[mod][attribute]
                for mod in modules if attribute in self[mod]}

    @classproperty
    @deprecated(since='8.4.0')
    def paraminfo_keys(cls) -> frozenset[str]:
        """Return module types.

        .. deprecated:: 8.4
        """
        return frozenset(['modules'])

    @property
    @deprecated(since='8.4.0')
    def preloaded_modules(self) -> frozenset[str] | set[str]:
        """Return set of preloaded modules.

        .. deprecated:: 8.4
        """
        return self._preloaded_modules
