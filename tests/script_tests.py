# -*- coding: utf-8  -*-
"""Test that each script can be compiled and executed."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import print_function, unicode_literals
__version__ = '$Id$'

import os
import sys

from tests import _root_dir
from tests.aspects import unittest, DefaultSiteTestCase, MetaTestCaseClass, PwbTestCase
from tests.utils import allowed_failure, execute_pwb, add_metaclass

if sys.version_info[0] > 2:
    basestring = (str, )

scripts_path = os.path.join(_root_dir, 'scripts')

# These dependencies are not always the package name which is in setup.py.
# e.g. 'PIL.ImageTk' is a object provided by several different pypi packages,
# and setup.py requests that 'Pillow' is installed to provide 'PIL.ImageTk'.
# Here, it doesnt matter which pypi package was requested and installed.
# Here, the name given to the module which will be imported is required.
script_deps = {
    'script_wui': ['crontab', 'lua'],
    # Note: package 'lunatic-python' provides module 'lua'

    'flickrripper': ['flickrapi'],
    'match_images': ['PIL.ImageTk'],
    'states_redirect': ['pycountry'],
    'patrol': ['mwlib'],
}

if sys.version_info < (2, 7):
    script_deps['replicate_wiki'] = ['argparse']
    script_deps['editarticle'] = ['argparse']

if sys.version_info < (3, 0):
    script_deps['data_ingestion'] = ['unicodecsv']


def check_script_deps(script_name):
    """Detect whether all dependencies are installed."""
    if script_name in script_deps:
        for package_name in script_deps[script_name]:
            try:
                __import__(package_name)
            except ImportError as e:
                print('%s depends on %s, which isnt available:\n%s'
                      % (script_name, package_name, e))
                return False
    return True


failed_dep_script_list = [name
                          for name in script_deps
                          if not check_script_deps(name)]

unrunnable_script_list = [
    'version',  # does not use global args
    'script_wui',   # depends on lua compiling
]

script_list = (['login'] +
               [name[0:-3] for name in os.listdir(scripts_path)  # strip '.py'
                if name.endswith('.py') and
                not name.startswith('_') and  # skip __init__.py and _*
                name != 'login.py'        # this is moved to be first
                ]
               )

runnable_script_list = (['login'] +
                        sorted(set(script_list) -
                               set(['login']) -
                               set(unrunnable_script_list)))

script_input = {
    'catall': 'q\n',  # q for quit
    'editarticle': 'Test page\n',
    'imageuncat': 'q\n',
    'interwiki': 'Test page that should not exist\n',
    'misspelling': 'q\n',
    'pagefromfile': 'q\n',
    'replace': 'foo\nbar\n\n\n',  # match, replacement,
                                  # Enter to begin, Enter for default summary.
    'shell': '\n',  # exits on end of stdin
    'solve_disambiguation': 'Test page\nq\n',
    'upload': 'https://upload.wikimedia.org/wikipedia/commons/8/80/Wikipedia-logo-v2.svg\n\n\n',
}

auto_run_script_list = [
    'blockpageschecker',
    'blockreview',
    'casechecker',
    'catall',
    'category_redirect',
    'cfd',
    'checkimages',
    'clean_sandbox',
    'disambredir',
    'imagerecat',
    'login',
    'lonelypages',
    'misspelling',
    'revertbot',
    'noreferences',
    'nowcommons',
    'patrol',
    'script_wui',
    'shell',
    'states_redirect',
    'unusedfiles',
    'upload',
    'watchlist',
    'welcome',
]

# Expected result for no arguments
# Some of these are not pretty, but at least they are informative
# and not backtraces starting deep in the pywikibot package.
no_args_expected_results = {
    'archivebot': 'NOTE: you must specify a template to run the bot',
    'create_categories': 'No pages to work on',
    # TODO: until done here, remember to set editor = None in user_config.py
    'editarticle': 'Nothing changed',  # This masks related bug 68645 but that
                                       # bug is more broadly about config
                                       # rather than editarticle.
    'freebasemappingupload': 'Cannot find ',
    'harvest_template': 'ERROR: Please specify',
    'illustrate_wikidata': 'I need a generator with pages to work on',
    'imageuncat': 'WARNING: This script is primarily written for Wikimedia Commons',
    # script_input['interwiki'] above lists a title that should not exist
    'interwiki': 'does not exist. Skipping.',
    'login': 'Logged in on ',
    'match_images': 'Require two images to work on.',
    'pagefromfile': 'Please enter the file name',
    'replace': 'Press Enter to use this automatic message',
    'script_wui': 'Pre-loading all relevant page contents',
    'shell': ('>>> ', 'Welcome to the'),
    'spamremove': 'No spam site specified',
    'transferbot': 'Target site not different from source site',  # Bug 68662
    'unusedfiles': ('Working on', None),
    'watchlist': 'Retrieving watchlist',

    # The following auto-run and typically cant be validated,
    # however these strings are very likely to exist within
    # the timeout of 5 seconds.
    'revertbot': 'Fetching new batch of contributions',
    'upload': 'ERROR: Upload error',
}

if sys.version_info[0] > 2:
    no_args_expected_results['replicate_wiki'] = 'error: the following arguments are required: destination'
else:
    no_args_expected_results['replicate_wiki'] = 'error: too few arguments'


enable_autorun_tests = (
    os.environ.get('PYWIKIBOT2_TEST_AUTORUN', '0') == '1')


def collector(loader=unittest.loader.defaultTestLoader):
    """Load the default tests."""
    # Note: Raising SkipTest during load_tests will
    # cause the loader to fallback to its own
    # discover() ordering of unit tests.

    if unrunnable_script_list:
        print('Skipping execution of unrunnable scripts:\n  %r'
              % unrunnable_script_list)

    if not enable_autorun_tests:
        print('Skipping execution of auto-run scripts '
              '(set PYWIKIBOT2_TEST_AUTORUN=1 to enable):\n  %r'
              % auto_run_script_list)

    tests = (['test__login'] +
             ['test_' + name
              for name in sorted(script_list)
              if name != 'login' and
              name not in unrunnable_script_list
              ])

    test_list = ['tests.script_tests.TestScriptHelp.' + name
                 for name in tests]

    tests = (['test__login'] +
             ['test_' + name
              for name in sorted(script_list)
              if name != 'login' and
              name not in failed_dep_script_list and
              name not in unrunnable_script_list and
              (enable_autorun_tests or name not in auto_run_script_list)
              ])

    test_list += ['tests.script_tests.TestScriptSimulate.' + name
                  for name in tests]

    tests = loader.loadTestsFromNames(test_list)
    suite = unittest.TestSuite()
    suite.addTests(tests)
    return suite


def load_tests(loader=unittest.loader.defaultTestLoader,
               tests=None, pattern=None):
    """Load the default modules."""
    return collector(loader)


class TestScriptMeta(MetaTestCaseClass):

    """Test meta class."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def test_execution(script_name, args=[]):
            is_autorun = '-help' not in args and script_name in auto_run_script_list

            def test_skip_script(self):
                raise unittest.SkipTest(
                    'Skipping execution of auto-run scripts (set '
                    'PYWIKIBOT2_TEST_AUTORUN=1 to enable) "{0}"'.format(script_name))

            def testScript(self):
                cmd = [script_name]

                if args:
                    cmd += args

                data_in = script_input.get(script_name)

                timeout = 0
                if is_autorun:
                    timeout = 5

                if self._results and script_name in self._results:
                    error = self._results[script_name]
                    if isinstance(error, basestring):
                        stdout = None
                    else:
                        stdout, error = error
                else:
                    stdout = None
                    error = None

                test_overrides = {}
                if not hasattr(self, 'net') or not self.net:
                    test_overrides['pywikibot.Site'] = 'None'

                result = execute_pwb(cmd, data_in, timeout=timeout, error=error,
                                     overrides=test_overrides)

                stderr = result['stderr'].split('\n')
                stderr_sleep = [l for l in stderr
                                if l.startswith('Sleeping for ')]
                stderr_other = [l for l in stderr
                                if not l.startswith('Sleeping for ')]
                if stderr_sleep:
                    print(u'\n'.join(stderr_sleep))

                if result['exit_code'] == -9:
                    print(' killed', end='  ')

                if error:
                    self.assertIn(error, result['stderr'])

                    exit_codes = [0, 1, 2, -9]
                elif not is_autorun:
                    if stderr_other == ['']:
                        stderr_other = None
                    self.assertIsNone(stderr_other)
                    self.assertIn('Global arguments available for all',
                                  result['stdout'])

                    exit_codes = [0]
                else:
                    # auto-run
                    exit_codes = [0, -9]

                    if (not result['stdout'] and not result['stderr']):
                        print(' auto-run script unresponsive after %d seconds'
                              % timeout, end=' ')
                    elif 'SIMULATION: edit action blocked' in result['stderr']:
                        print(' auto-run script simulated edit blocked',
                              end='  ')
                    else:
                        print(' auto-run script stderr within %d seconds: %r'
                              % (timeout, result['stderr']), end='  ')

                self.assertNotIn('Traceback (most recent call last)',
                                 result['stderr'])
                self.assertNotIn('deprecated', result['stderr'].lower())

                # If stdout doesnt include global help..
                if 'Global arguments available for all' not in result['stdout']:
                    # Specifically look for deprecated
                    self.assertNotIn('deprecated', result['stdout'].lower())
                    if result['stdout'] == '':
                        result['stdout'] = None
                    # But also complain if there is any stdout
                    if stdout is not None and result['stdout'] is not None:
                        self.assertIn(stdout, result['stdout'])
                    else:
                        self.assertIsNone(result['stdout'])

                self.assertIn(result['exit_code'], exit_codes)

                sys.stdout.flush()

            if not enable_autorun_tests and is_autorun:
                return test_skip_script
            return testScript

        argument = dct['_argument']

        for script_name in script_list:
            # force login to be the first, alphabetically, so the login
            # message does not unexpectedly occur during execution of
            # another script.
            # unrunnable script tests are disabled by default in load_tests()

            if script_name == 'login':
                test_name = 'test__login'
            else:
                test_name = 'test_' + script_name

            # it's explicitly using str() because __name__ must be str
            test_name = str(test_name)
            dct[test_name] = test_execution(script_name, ['-' + argument])

            if script_name in dct['_expected_failures']:
                dct[test_name] = unittest.expectedFailure(dct[test_name])
            elif script_name in dct['_allowed_failures']:
                dct[test_name] = allowed_failure(dct[test_name])

            dct[test_name].__doc__ = 'Test running %s -%s.' % (script_name,
                                                               argument)
            dct[test_name].__name__ = test_name

            # Disable test by default in nosetests
            if script_name in unrunnable_script_list:
                dct[test_name].__test__ = False

        return super(TestScriptMeta, cls).__new__(cls, name, bases, dct)


@add_metaclass
class TestScriptHelp(PwbTestCase):

    """Test cases for running scripts with -help.

    All scripts should not create a Site for -help, so net = False.
    """

    __metaclass__ = TestScriptMeta

    net = False

    _expected_failures = failed_dep_script_list
    _allowed_failures = []

    _argument = 'help'
    _results = None


@add_metaclass
class TestScriptSimulate(DefaultSiteTestCase, PwbTestCase):

    """Test cases for scripts.

    This class sets the nose 'user' attribute on every test, thereby ensuring
    that the test runner has a username for the default site, and so that
    Site.login() is called in the test runner, which means that the scripts
    run in pwb can automatically login using the saved cookies.
    """

    __metaclass__ = TestScriptMeta

    user = True

    _expected_failures = [
        'catall',          # stdout user interaction
        'flickrripper',    # Requires a flickr api key
        'upload',          # raises custom ValueError
    ] + failed_dep_script_list

    _allowed_failures = [
        'checkimages',
        'disambredir',
        # T94681
        'misspelling',
        # T77965
        'watchlist',
        # T94680: uses exit code 1
        'lonelypages',
    ]

    _argument = 'simulate'
    _results = no_args_expected_results


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
