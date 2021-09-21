"""Package tests."""
#
# (C) Pywikibot team, 2007-2021
#
# Distributed under the terms of the MIT license.
#
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
from unittest import mock  # noqa: F401
from unittest.mock import MagicMock, Mock, patch  # noqa: F401

# Verify that the unit tests have a base working environment:
# - requests is mandatory
#   however if unavailable this will fail on use; see pywikibot/tools.py
# - mwparserfromhell or wikitextparser is mandatory but the dependency
#   is checked by textlib already
import requests  # noqa: F401

import pywikibot.data.api
from pywikibot import config
from pywikibot.data.api import CachedRequest
from pywikibot.data.api import Request as _original_Request
from pywikibot.tools import PYTHON_VERSION


_root_dir = os.path.split(os.path.split(__file__)[0])[0]

# common warn() clauses...
#
#   WARN_SITE_CODE is from T234147
#   WARN_SITE_OBJ is from T225594

WARN_SITE_CODE = r'^Site .*:.* instantiated using different code *'
WARN_SITE_OBJ = 'Site objects have been created before arguments were handled'


def join_root_path(*names):
    """Return a path relative to the root directory."""
    return os.path.join(_root_dir, *names)


def create_path_func(base_func, subpath):
    """Return a function returning a path relative to the given directory."""
    func = functools.partial(base_func, subpath)
    func.path = base_func.path + '/' + subpath
    func.__doc__ = 'Return a path relative to `{}/`.'.format(func.path)
    return func


join_root_path.path = 'root'
join_tests_path = create_path_func(join_root_path, 'tests')
join_cache_path = create_path_func(join_tests_path,
                                   'apicache-py{}'
                                   .format(PYTHON_VERSION[0]))
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
    'deprecation',
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
    'flow',
    'flow_edit',
    'flow_thanks',
    'http',
    'i18n',
    'interwiki_graph',
    'interwiki_link',
    'interwikimap',
    'link',
    'linter',
    'logentries',
    'login',
    'mediawikiversion',
    'mysql',
    'namespace',
    'oauth',
    'page',
    'pagegenerators',
    'paraminfo',
    'plural',
    'proofreadpage',
    'site',
    'site_decorators',
    'site_detect',
    'siteinfo',
    'sparql',
    'tests',
    'textlib',
    'thanks',
    'thread',
    'timestamp',
    'timestripper',
    'tk',
    'token',
    'tools',
    'tools_chars',
    'tools_formatter',
    'ui',
    'ui_options',
    'upload',
    'uploadbot',
    'user',
    'wikibase',
    'wikibase_edit',
    'wikistats',
    'xmlreader'
}

script_test_modules = {
    'add_text',
    'archivebot',
    'cache',
    'category_bot',
    'checkimages',
    'deletionbot',
    'fixing_redirects',
    'generate_family_file',
    'generate_user_files',
    'interwikidata',
    'l10n',
    'patrolbot',
    'protectbot',
    'pwb',
    'redirect_bot',
    'reflinks',
    'replacebot',
    'script',
    'template_bot',
    'update_script',
    'uploadscript',
    'weblinkchecker'
}

disabled_test_modules = {
    'tests',  # tests of the tests package
    'l10n',  # pywikibot-i18n repository runs it
}

disabled_tests = {
    'textlib': [
        'test_interwiki_format',  # example; very slow test
    ],
}


def _unknown_test_modules():
    """List tests which are to be executed."""
    dir_list = os.listdir(join_tests_path())
    all_test_set = {name[0:-9] for name in dir_list  # strip '_tests.py'
                    if name.endswith('_tests.py')
                    and not name.startswith('_')}  # skip __init__.py and _*

    return all_test_set - library_test_modules - script_test_modules


extra_test_modules = _unknown_test_modules()

if 'PYWIKIBOT_TEST_MODULES' in os.environ:
    _enabled_test_modules = os.environ['PYWIKIBOT_TEST_MODULES'].split(',')
    disabled_test_modules = (library_test_modules
                             | extra_test_modules
                             | script_test_modules
                             - set(_enabled_test_modules))


def unittest_print(*args, **kwargs):
    """Print information in test log."""
    print(*args, **kwargs)  # noqa: T001


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

    if extra_test_modules:
        unittest_print(
            'Extra test modules (run after library, before scripts):\n  {}'
            .format(', '.join(extra_test_modules)))

    if disabled_tests:
        unittest_print(
            'Skipping tests (to run: python -m unittest ...):\n  {!r}'
            .format(disabled_tests))

    modules = (module
               for module in chain(library_test_modules,
                                   extra_test_modules,
                                   script_test_modules)
               if module not in disabled_test_modules)

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
                            module_class_name + '.'
                            + test_func.__class__.__name__ + '.'
                            + test_func._testMethodName)

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


# Travis-CI builds are set to retry twice, which aims to reduce the number
# of 'red' builds caused by intermittent server problems, while also avoiding
# the builds taking a long time due to retries.
# The following allows builds to retry twice, but higher default values are
# overridden here to restrict retries to only 1, so developer builds fail more
# frequently in code paths resulting from mishandled server problems.
if config.max_retries > 2:
    if 'PYWIKIBOT_TEST_QUIET' not in os.environ:
        unittest_print(
            'tests: max_retries reduced from {} to 1'
            .format(config.max_retries))
    config.max_retries = 1

# Raise CaptchaError if a test requires solving a captcha
config.solve_captcha = False

warnings.filterwarnings('always')


class TestRequest(CachedRequest):

    """Add caching to every Request except logins."""

    def __init__(self, *args, **kwargs):
        """Initializer."""
        super().__init__(0, *args, **kwargs)

    @classmethod
    def create_simple(cls, req_site, **kwargs):
        """Circumvent CachedRequest implementation."""
        return cls(site=req_site, parameters=kwargs)

    def _expired(self, dt):
        """Never invalidate cached data."""
        return False

    def _load_cache(self) -> bool:
        """Return whether the cache can be used."""
        if not super()._load_cache():
            return False

        if 'lgpassword' in self._uniquedescriptionstr():
            self._data = None
            return False

        return True

    def _write_cache(self, data) -> None:
        """Write data except login details."""
        if 'lgpassword' not in self._uniquedescriptionstr():
            super()._write_cache(data)


original_expired = None


def patch_request():
    """Patch Request classes with TestRequest."""
    global original_expired
    pywikibot.data.api.Request = TestRequest
    original_expired = pywikibot.data.api.CachedRequest._expired
    pywikibot.data.api.CachedRequest._expired = lambda *args, **kwargs: False


def unpatch_request():
    """Un-patch Request classes with TestRequest."""
    pywikibot.data.api.Request = _original_Request
    pywikibot.data.api.CachedRequest._expired = original_expired


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
