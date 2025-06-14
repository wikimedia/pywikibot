"""Package tests."""
#
# (C) Pywikibot team, 2007-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations


__all__ = (
    'create_path_func', 'join_cache_path', 'join_data_path',
    'join_html_data_path', 'join_images_path', 'join_pages_path',
    'join_root_path', 'join_xml_data_path', 'patch_request', 'unittest_print',
    'unpatch_request',
)

import functools
import os
import unittest
import warnings
from contextlib import suppress
from itertools import chain

# Verify that the unit tests have a base working environment:
# - requests is mandatory
#   however if unavailable this will fail on use; see pywikibot/tools.py
# - mwparserfromhell or wikitextparser is mandatory but the dependency
#   is checked by textlib already
import requests  # noqa: F401

import pywikibot.data.api
from pywikibot import config
from pywikibot.backports import removesuffix
from pywikibot.data.api import CachedRequest
from pywikibot.data.api import Request as _original_Request


_root_dir = os.path.split(os.path.split(__file__)[0])[0]

WARN_SITE_CODE = '^Site .*:.* instantiated using different code *'  # T234147


def join_root_path(*names):
    """Return a path relative to the root directory."""
    return os.path.join(_root_dir, *names)


def create_path_func(base_func, subpath):
    """Return a function returning a path relative to the given directory."""
    func = functools.partial(base_func, subpath)
    func.path = base_func.path + '/' + subpath
    func.__doc__ = f'Return a path relative to `{func.path}/`.'
    return func


join_root_path.path = 'root'
join_tests_path = create_path_func(join_root_path, 'tests')
join_cache_path = create_path_func(join_tests_path, 'apicache')
join_data_path = create_path_func(join_tests_path, 'data')
join_pages_path = create_path_func(join_tests_path, 'pages')

join_images_path = create_path_func(join_data_path, 'images')
join_xml_data_path = create_path_func(join_data_path, 'xml')
join_html_data_path = create_path_func(join_data_path, 'html')

# Find the root directory of the checkout
_pwb_py = join_root_path('pwb.py')

library_test_modules = {
    'api',
    'basesite',
    'bot',
    'category',
    'collections',
    'cosmetic_changes',
    'date',
    'datasite',
    'diff',
    'djvu',
    'dry_api',
    'dry_site',
    'echo',
    'edit',
    'edit_failure',
    'eventstreams',
    'family',
    'file',
    'fixes',
    'gui',
    'http',
    'i18n',
    'interwiki_graph',
    'interwiki_link',
    'interwikimap',
    'l10n',  # pywikibot-i18n repository runs it too
    'link',
    'linter',
    'logentries',
    'login',
    'mediawikiversion',
    'memento',
    'mysql',
    'namespace',
    'oauth',
    'page',
    'pagegenerators',
    'paraminfo',
    'plural',
    'proofreadpage',
    'setup',
    'site',
    'site_decorators',
    'site_generators',
    'site_detect',
    'site_login_logout',
    'site_obsoletesites',
    'siteinfo',
    'superset',
    'sparql',
    'tests',
    'textlib',
    'thanks',
    'time',
    'timestripper',
    'titletranslate',
    'token',
    'tools',
    'tools_chars',
    'tools_deprecate',
    'tools_formatter',
    'tools_threading',
    'ui',
    'ui_options',
    'upload',
    'uploadbot',
    'user',
    'version',
    'wbtypes',
    'wikibase',
    'wikibase_edit',
    'wikiblame',
    'wikistats',
    'xmlreader'
}

script_test_modules = {
    'add_text',
    'archivebot',
    'cache',
    'category_bot',
    'checkimages',
    'data_ingestion',
    'deletionbot',
    'fixing_redirects',
    'generate_family_file',
    'generate_user_files',
    'harvest_template',
    'interwikidata',
    'l10n',
    'make_dist',
    'noreferences',
    'patrolbot',
    'protectbot',
    'pwb',
    'redirect_bot',
    'reflinks',
    'replacebot',
    'script',
    'template_bot',
    'uploadscript',
}

disabled_test_modules = {
    'tests',  # tests of the tests package
    'site_login_logout',  # separate Login CI action
}

# remove "# pragma: no cover" below if this set is not empty
disabled_tests: dict[str, list[str]] = {}


def _unknown_test_modules():
    """List tests which are to be executed."""
    dir_list = os.listdir(join_tests_path())
    all_test_set = {removesuffix(name, '_tests.py') for name in dir_list
                    if name.endswith('_tests.py')
                    and not name.startswith('_')}  # skip __init__.py and _*

    return all_test_set - library_test_modules - script_test_modules


extra_test_modules = _unknown_test_modules()

if 'PYWIKIBOT_TEST_MODULES' in os.environ:
    enabled_test_modules = os.environ['PYWIKIBOT_TEST_MODULES'].split(',')
else:
    enabled_test_modules = chain(library_test_modules,
                                 extra_test_modules,
                                 script_test_modules)


def unittest_print(*args, **kwargs) -> None:
    """Print information in test log."""
    print(*args, **kwargs)  # noqa: T201


def collector(loader=unittest.loader.defaultTestLoader):
    """Load the default modules.

    This is the entry point is specified in setup.py
    """
    # Note: Raising SkipTest during load_tests will
    # cause the loader to fallback to its own
    # discover() ordering of unit tests.
    if disabled_test_modules:
        unittest_print(
            'Disabled test modules (to run: python -m unittest ...):\n  {}'
            .format(', '.join(disabled_test_modules)))

    if extra_test_modules:  # pragma: no cover
        unittest_print(
            'Extra test modules (run after library, before scripts):\n  {}'
            .format(', '.join(extra_test_modules)))

    if disabled_tests:  # pragma: no cover
        unittest_print(f'Skipping tests (to run: python -m unittest ...):\n'
                       f'  {disabled_tests!r}')

    modules = (module
               for module in enabled_test_modules
               if module not in disabled_test_modules)

    test_list = []

    for module in modules:
        module_class_name = 'tests.' + module + '_tests'
        if module in disabled_tests:  # pragma: no cover
            discovered = loader.loadTestsFromName(module_class_name)
            enabled_tests = []
            for cls in discovered:
                enabled_tests += [
                    f'{module_class_name}.{type(test_func).__name__}.'
                    f'{test_func._testMethodName}'
                    for test_func in cls
                    if test_func._testMethodName not in disabled_tests[module]
                ]

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


CachedRequest._get_cache_dir = classmethod(
    lambda cls, *args: cls._make_dir(join_cache_path()))


# The following allows builds to retry up to three times, but higher default
# values are overridden here to restrict retries to only 3, so developer builds
# fail more frequently in code paths resulting from mishandled server problems.
# This aims to reduce the number of 'red' builds caused by intermittent server
# problems, while also avoiding the builds taking a long time due to retries.
if config.max_retries > 3:
    if 'PYWIKIBOT_TEST_QUIET' not in os.environ:
        unittest_print(
            f'tests: max_retries reduced from {config.max_retries} to 3')
    config.max_retries = 3

# Raise CaptchaError if a test requires solving a captcha
config.solve_captcha = False

warnings.filterwarnings('always')


class TestRequest(CachedRequest):

    """Add caching to every Request except logins."""

    def __init__(self, *args, **kwargs) -> None:
        """Initializer."""
        super().__init__(0, *args, **kwargs)

    @classmethod
    def create_simple(cls, req_site, **kwargs):
        """Circumvent CachedRequest implementation."""
        return cls(site=req_site, parameters=kwargs)

    def _expired(self, dt) -> bool:
        """Never invalidate cached data."""
        return False

    def _load_cache(self) -> bool:
        """Return whether the cache can be used."""
        if not super()._load_cache():
            return False

        if 'lgpassword' in self._uniquedescriptionstr():  # pragma: no cover
            self._data = None
            return False

        return True

    def _write_cache(self, data) -> None:
        """Write data except login details."""
        if 'lgpassword' not in self._uniquedescriptionstr():
            super()._write_cache(data)


original_expired = None


def patch_request() -> None:
    """Patch Request classes with TestRequest."""
    global original_expired
    pywikibot.data.api.Request = TestRequest
    original_expired = pywikibot.data.api.CachedRequest._expired
    pywikibot.data.api.CachedRequest._expired = lambda *args, **kwargs: False


def unpatch_request() -> None:
    """Un-patch Request classes with TestRequest."""
    pywikibot.data.api.Request = _original_Request
    pywikibot.data.api.CachedRequest._expired = original_expired


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
