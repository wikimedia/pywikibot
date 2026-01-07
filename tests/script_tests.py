#!/usr/bin/env python3
"""Test that each script can be compiled and executed."""
#
# (C) Pywikibot team, 2014-2026
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import sys
import unittest
from collections.abc import Iterator
from contextlib import suppress
from pathlib import Path

from pywikibot.bot import global_args as pwb_args
from pywikibot.tools import has_module
from tests import join_root_path, unittest_print
from tests.aspects import DefaultSiteTestCase, MetaTestCaseClass, PwbTestCase
from tests.utils import execute_pwb


scripts_path = join_root_path('scripts')

# login script should be the first to test
framework_scripts = ['login', 'shell']

# These dependencies are not always the package name which is in setup.py.
# Here, the name given to the module which will be imported is required.
script_deps = {
    'weblinkchecker': ['memento_client'],
}


def check_script_deps(script_name) -> bool:
    """Detect whether all dependencies are installed."""
    if script_name in script_deps:
        for package_name in script_deps[script_name]:
            if not has_module(package_name):
                return False  # pragma: no cover
    return True


failed_dep_script_set = {name for name in script_deps
                         if not check_script_deps(name)}

# scripts which cannot be tested
unrunnable_script_set = set()


def list_scripts(path: str, exclude: str = '') -> list[str]:
    """List script names (without '.py') in a directory.

    :param path: Directory path to search for Python scripts.
    :param exclude: Filename (without '.py' extension) to exclude from
        the result. Defaults to empty string, meaning no exclusion.
    :return: List of script names without the '.py' extension, excluding
        the specified file. Files starting with '_' (e.g. __init__.py)
        are always excluded.
    """
    p = Path(path)
    return [
        f.stem for f in p.iterdir()
        if f.is_file()
        and f.suffix == '.py'
        and not f.name.startswith('_')
        and f.stem != exclude
    ]


script_list = framework_scripts + list_scripts(scripts_path)

script_input = {
    'category_redirect': 'q\nn\n',
    'interwiki': 'Test page that should not exist\n',
    'misspelling': 'q\n',
    'pagefromfile': 'q\n',
    'replace': 'foo\nbar\n\n\n',  # match, replacement,
                                  # Enter to begin, Enter for default summary.
    'shell': '\n',  # exits on end of stdin
    'solve_disambiguation': 'Test page\nq\n',
    'unusedfiles': 'q\n',
    'upload':
        'https://upload.wikimedia.org/wikipedia/commons/'
        '8/80/Wikipedia-logo-v2.svg\n\n\n',
}

#:
auto_run_script_set = {
    'archivebot',
    'blockpageschecker',
    'category_redirect',
    'checkimages',
    'clean_sandbox',
    'commons_information',
    'delinker',
    'login',
    'misspelling',
    'noreferences',
    'nowcommons',
    'parser_function_count',
    'patrol',
    'revertbot',
    'shell',
    'unusedfiles',
    'upload',
    'watchlist',
    'welcome',
}

# Expected result for no arguments
# Some of these are not pretty, but at least they are informative
# and not backtraces starting deep in the pywikibot package.
no_args_expected_results = {
    'archivebot': 'No template was specified, using default',
    # TODO: until done here, remember to set editor = None in user-config.py
    'change_pagelang': 'No -setlang parameter given',
    'checkimages': 'Execution time: 0 seconds',
    'harvest_template': 'ERROR: Please specify',
    # script_input['interwiki'] above lists a title that should not exist
    'interwiki': 'does not exist. Skipping.',
    'login': 'Logged in on ',
    'pagefromfile': 'Please enter the file name',
    'parser_function_count': 'Hold on, this will need some time.',
    'replace': 'Press Enter to use this automatic message',
    'replicate_wiki':
        'error: the following arguments are required: destination',
    'shell': ('>>> ', 'Welcome to the'),
    'speedy_delete': "does not have 'delete' right for site",
    'transferbot': 'Target site not different from source site',
    'unusedfiles': ('Working on', None),
    'version': 'Pywikibot: [',
    'watchlist': 'Retrieving watchlist',

    # The following auto-run and typically can't be validated,
    # however these strings are very likely to exist within
    # the timeout of 5 seconds.
    'revertbot': 'Fetching new batch of contributions',
    'upload': 'ERROR: Upload error',
}

# skip test if result is unexpected in this way
skip_on_results = {
    'speedy_delete': 'No user is logged in on site'  # T301555
}


def collector() -> Iterator[str]:
    """Generate test fully qualified names from test classes."""
    for cls in TestScriptHelp, TestScriptSimulate, TestScriptGenerator:
        for name in cls._script_list:
            name = '_' + name if name == 'login' else name
            yield f'tests.script_tests.{cls.__name__}.test_{name}'


custom_loader = False


def load_tests(loader: unittest.TestLoader = unittest.defaultTestLoader,
               standard_tests: unittest.TestSuite | None = None,
               pattern: str | None = None) -> unittest.TestSuite:
    """Load the default modules and return a TestSuite."""
    global custom_loader
    custom_loader = True
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromNames(collector()))
    return suite


def filter_scripts(excluded: set[str] | None = None, *,
                   exclude_auto_run: bool = False,
                   exclude_failed_dep: bool = True) -> list[str]:
    """Return a filtered list of script names.

    :param excluded: Scripts to exclude explicitly.
    :param exclude_auto_run: If True, remove scripts in
        auto_run_script_set.
    :param exclude_failed_dep: If True, remove scripts in
        failed_dep_script_set.
    :return: A list of valid script names in deterministic order.
    """
    excluded = excluded or set()

    scripts = ['login'] + [
        name for name in sorted(script_list)
        if name != 'login'
        and name not in unrunnable_script_set
        and (not exclude_failed_dep or name not in failed_dep_script_set)
    ]

    if exclude_auto_run:
        scripts = [n for n in scripts if n not in auto_run_script_set]

    return [n for n in scripts if n not in excluded]


class ScriptTestMeta(MetaTestCaseClass):

    """Test meta class."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def test_execution(script_name, args=None):
            if args is None:
                args = []

            is_autorun = ('-help' not in args
                          and script_name in auto_run_script_set)

            def test_script(self) -> None:
                global_args_msg = \
                    'For global options use -help:global or run pwb'
                global_args = (pwb_args or []) + ['-pwb_close_matches:1']

                cmd = [*global_args, script_name, *args]
                data_in = script_input.get(script_name)
                if isinstance(self._timeout, bool):
                    do_timeout = self._timeout
                else:
                    do_timeout = script_name in self._timeout
                timeout = 10 if do_timeout else None

                stdout, error = None, None
                if self._results:
                    if isinstance(self._results, dict):
                        error = self._results.get(script_name)
                    else:
                        error = self._results
                    if isinstance(error, tuple):
                        stdout, error = error

                test_overrides = {}
                if not hasattr(self, 'net') or not self.net:
                    test_overrides['pywikibot.Site'] = 'lambda *a, **k: None'

                # run the script
                result = execute_pwb(cmd, data_in=data_in, timeout=timeout,
                                     overrides=test_overrides)

                err_result = result['stderr']
                out_result = result['stdout']
                stderr_other = err_result.splitlines()

                if result['exit_code'] == -9:
                    unittest_print(' killed', end='  ')

                skip_result = self._skip_results.get(script_name)
                if skip_result and skip_result in err_result:
                    self.skipTest(skip_result)

                if error:
                    self.assertIn(error, err_result)
                    exit_codes = [0, 1, 2, -9]

                elif not is_autorun:
                    if not stderr_other:
                        self.assertIn(global_args_msg, out_result)
                    else:
                        self.assertIn('Use -help for further information.',
                                      stderr_other)
                        self.assertNotIn('-help', args)
                    exit_codes = [0]

                else:
                    # auto-run
                    # returncode is 1 if the process is killed
                    exit_codes = [0, 1, -9]
                    if not out_result and not err_result:
                        unittest_print(' auto-run script unresponsive after '
                                       f'{timeout} seconds', end=' ')
                    elif 'SIMULATION: edit action blocked' in err_result:
                        unittest_print(' auto-run script simulated edit '
                                       'blocked', end=' ')
                    else:
                        unittest_print(' auto-run script stderr within '
                                       f'{timeout} seconds: {err_result!r}',
                                       end='  ')
                    unittest_print(f" exit code: {result['exit_code']}",
                                   end=' ')

                self.assertNotIn('Traceback (most recent call last)',
                                 err_result)
                self.assertNotIn('deprecated', err_result.lower())

                # If stdout doesn't include global help..
                if global_args_msg not in out_result:
                    # Specifically look for deprecated
                    self.assertNotIn('deprecated', out_result.lower())
                    # But also complain if there is any stdout
                    if stdout is not None and out_result:
                        self.assertIn(stdout, out_result)
                    else:
                        self.assertIsEmpty(out_result)

                self.assertIn(result['exit_code'], exit_codes)
                sys.stdout.flush()

            return test_script

        arguments = dct['_arguments']

        if custom_loader:
            collected_scripts = dct['_script_list']
        else:
            collected_scripts = filter_scripts(exclude_failed_dep=False)
        for script in collected_scripts:

            # force login to be the first, alphabetically, so the login
            # message does not unexpectedly occur during execution of
            # another script.
            test = 'test__login' if script == 'login' else 'test_' + script

            cls.add_method(dct, test,
                           test_execution(script, arguments.split()),
                           f'Test running {script} {arguments}.')

            if script in dct['_expected_failures']:
                dct[test] = unittest.expectedFailure(dct[test])
            elif script in dct['_allowed_failures']:
                dct[test] = unittest.skip(
                    f'{script} is in _allowed_failures set'
                )(dct[test])
            elif script in failed_dep_script_set and arguments == '-simulate':
                dct[test] = unittest.skip(
                    f'{script} has dependencies; skipping'
                )(dct[test])

        return super().__new__(cls, name, bases, dct)


class TestScriptHelp(PwbTestCase, metaclass=ScriptTestMeta):

    """Test cases for running scripts with -help.

    All scripts should not create a Site for -help, so net = False.
    """

    net = False

    # Here come scripts requiring and missing dependencies, that haven't been
    # fixed to output -help in that case.
    _expected_failures = {'version'}
    _allowed_failures = set()

    _arguments = '-help'
    _results = None
    _skip_results = {}
    _timeout = False
    _script_list = filter_scripts(exclude_failed_dep=False)


class TestScriptSimulate(DefaultSiteTestCase, PwbTestCase,
                         metaclass=ScriptTestMeta):

    """Test cases for running scripts with -simulate.

    This class sets the 'user' attribute on every test, thereby ensuring
    that the test runner has a username for the default site, and so
    that Site.login() is called in the test runner, which means that the
    scripts run in pwb can automatically login using the saved cookies.
    """

    login = True

    _expected_failures = {
        'catall',          # stdout user interaction
        'checkimages',
        'commons_information',  # no empty out_result
        'revertbot',
        'transwikiimport',
    }

    _allowed_failures = {
        'blockpageschecker',  # not localized for some test sites
        'category_redirect',
        'claimit',
        'clean_sandbox',
        'commons_information',  # T379455
        'coordinate_import',
        'delinker',
        'disambredir',
        'illustrate_wikidata',
        'misspelling',  # T94681
        'noreferences',
        'nowcommons',
        'patrol',
        'shell',
        'speedy_delete',
        'unusedfiles',  # not localized for default sites
        'upload',  # raises custom ValueError
        'watchlist',  # not logged in
    }

    _arguments = '-simulate'
    _results = no_args_expected_results
    _skip_results = skip_on_results
    _timeout = auto_run_script_set
    _script_list = filter_scripts(_allowed_failures)


class TestScriptGenerator(DefaultSiteTestCase, PwbTestCase,
                          metaclass=ScriptTestMeta):

    """Test cases for running scripts with a generator."""

    login = True

    _expected_failures = {
        'add_text',
        'archivebot',
        'blockpageschecker',
        'category',
        'category_graph',
        'category_redirect',
        'change_pagelang',
        'checkimages',
        'claimit',
        'clean_sandbox',
        'data_ingestion',
        'delinker',
        'djvutext',
        'download_dump',
        'harvest_template',
        'image',  # Foobar has no valid extension
        'interwiki',
        'listpages',
        'login',
        'movepages',
        'pagefromfile',
        'parser_function_count',
        'patrol',
        'protect',
        'redirect',
        'reflinks',  # 404-links.txt is required
        'replicate_wiki',
        'revertbot',
        'shell',
        'solve_disambiguation',
        'speedy_delete',
        'template',
        'templatecount',
        'transferbot',
        'transwikiimport',
        'unusedfiles',
        'upload',
        'watchlist',
        'weblinkchecker',
        'welcome',
    }

    _allowed_failures = {
        'basic',
        'delete',  # T368859
        'fixing_redirects',  # T379455
        'illustrate_wikidata',  # T379455
        'imagetransfer',  # T368859
        'newitem',
        'nowcommons',
    }
    _arguments = '-simulate -page:Foobar -always -site:wikipedia:en'
    _results = ("Working on 'Foobar'", 'Script terminated successfully')
    _skip_results = {}
    _timeout = True
    _script_list = filter_scripts(_allowed_failures, exclude_auto_run=True)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
