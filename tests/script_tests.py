# -*- coding: utf-8  -*-
"""Test that each script can be compiled and executed."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import print_function
__version__ = '$Id$'

import os
import sys
import time
import subprocess
import pywikibot
from pywikibot import config
from tests.aspects import unittest, DefaultSiteTestCase, MetaTestCaseClass, PwbTestCase


base_path = os.path.split(os.path.split(__file__)[0])[0]
pwb_path = os.path.join(base_path, 'pwb.py')
scripts_path = os.path.join(base_path, 'scripts')


script_deps = {
    'script_wui': ['crontab', 'lua'],
    # Note: package 'lunatic-python' provides module 'lua'

    'flickrripper': ['ImageTk', 'flickrapi'],
    # Note: 'PIL' is not available via pip2.7 on MS Windows,
    #       however it is available with setuptools.
}
if sys.version_info < (2, 7):
    script_deps['replicate_wiki'] = ['argparse']


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
    'script_wui',   # depends on lua compiling
    'editarticle',  # requires a X DISPLAY
]

deadlock_script_list = [
    'makecat',      # bug 69781
]

script_list = (['login'] +
               [name[0:-3] for name in os.listdir(scripts_path)  # strip '.py'
                if name.endswith('.py')
                and not name.startswith('_')  # skip __init__.py and _*
                and name != 'login.py'        # this is moved to be first
                ]
               )

runnable_script_list = (['login'] +
                        sorted(set(script_list) -
                               set(['login']) -
                               set(unrunnable_script_list)))

script_input = {
    'catall': 'q\n',  # q for quit
    'editarticle': 'Test page\n',
    'interwiki': 'Test page\n',
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
    'clean_sandbox',
    'disambredir',
    'imagerecat',
    'login',
    'lonelypages',
    'misspelling',
    'revertbot',
    'noreferences',
    'nowcommons',
    'script_wui',
    'shell',
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
    'imageuncat': 'You have to specify the generator ',
    'interwiki': 'does not exist. Skipping.',  # 'Test page' does not exist
    'login': 'Logged in on ',
    'pagefromfile': 'Please enter the file name',
    'replace': 'Press Enter to use this default message',
    'script_wui': 'Pre-loading all relevant page contents',
    'shell': 'Welcome to the',
    'spamremove': 'No spam site specified',
    'transferbot': 'Target site not different from source site',  # Bug 68662
    'version': 'unicode test: ',
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


def collector(loader=unittest.loader.defaultTestLoader):
    """Load the default tests."""
    # Note: Raising SkipTest during load_tests will
    # cause the loader to fallback to its own
    # discover() ordering of unit tests.

    enable_autorun_tests = (
        os.environ.get('PYWIKIBOT2_TEST_AUTORUN', '0') == '1')

    if deadlock_script_list:
        print('Skipping deadlock scripts:\n  %s'
              % ', '.join(deadlock_script_list))

    if unrunnable_script_list:
        print('Skipping execution of unrunnable scripts:\n  %r'
              % unrunnable_script_list)

    if not enable_autorun_tests:
        print('Skipping execution of auto-run scripts '
              '(set PYWIKIBOT2_TEST_AUTORUN=1 to enable):\n  %r'
              % auto_run_script_list)

    tests = (['test__login_help'] +
             ['test_' + name + '_help'
              for name in sorted(script_list)
              if name != 'login'
              and name not in deadlock_script_list] +
             ['test__login_simulate'])

    tests += ['test_' + name + '_simulate'
              for name in sorted(script_list)
              if name != 'login'
              and name not in deadlock_script_list
              and name not in failed_dep_script_list
              and name not in unrunnable_script_list
              and (enable_autorun_tests or name not in auto_run_script_list)]

    test_list = ['tests.script_tests.TestScript.' + name
                 for name in tests]

    tests = loader.loadTestsFromNames(test_list)
    suite = unittest.TestSuite()
    suite.addTests(tests)
    return suite


def load_tests(loader=unittest.loader.defaultTestLoader,
               tests=None, pattern=None):
    """Load the default modules."""
    return collector(loader)


def execute(command, data_in=None, timeout=0, error=None):
    """Execute a command and capture outputs."""
    def decode(stream):
        if sys.version_info[0] > 2:
            return stream.decode(config.console_encoding)
        else:
            return stream
    options = {
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE
    }
    if data_in is not None:
        options['stdin'] = subprocess.PIPE

    p = subprocess.Popen(command, **options)

    if data_in is not None:
        if sys.version_info[0] > 2:
            data_in = data_in.encode(config.console_encoding)
        p.stdin.write(data_in)
        p.stdin.flush()  # _communicate() otherwise has a broken pipe

    stderr_lines = b''
    waited = 0
    while (error or (waited < timeout)) and p.poll() is None:
        # In order to kill 'shell' and others early, read only a single
        # line per second, and kill the process as soon as the expected
        # output has been seen.
        # Additional lines will be collected later with p.communicate()
        if error:
            line = p.stderr.readline()
            stderr_lines += line
            if error in decode(line):
                break
        time.sleep(1)
        waited += 1

    if (timeout or error) and p.poll() is None:
        p.kill()

    if p.poll() is not None:
        stderr_lines += p.stderr.read()

    data_out = p.communicate()
    return {'exit_code': p.returncode,
            'stdout': decode(data_out[0]),
            'stderr': decode(stderr_lines + data_out[1])}


class TestScriptMeta(MetaTestCaseClass):

    """Test meta class."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def test_execution(script_name, args=[], expected_results=None):
            def testScript(self):
                cmd = [sys.executable, pwb_path, script_name]

                if args:
                    cmd += args

                data_in = script_input.get(script_name)

                timeout = 0
                if '-help' not in args and script_name in auto_run_script_list:
                    timeout = 5

                if expected_results and script_name in expected_results:
                    error = expected_results[script_name]
                else:
                    error = None

                result = execute(cmd, data_in, timeout=timeout, error=error)

                stderr = result['stderr'].split('\n')
                stderr_sleep = [l for l in stderr
                                if l.startswith('Sleeping for ')]
                stderr_other = [l for l in stderr
                                if not l.startswith('Sleeping for ')]
                if stderr_sleep:
                    print(u'\n'.join(stderr_sleep))

                if result['exit_code'] == -9:
                    print(' killed', end='  ')

                if '-help' in args or error or \
                        script_name not in auto_run_script_list:

                    if error:
                        self.assertIn(error, result['stderr'])

                        self.assertIn(result['exit_code'], [0, -9])
                    else:
                        if stderr_other == ['']:
                            stderr_other = None
                        self.assertIsNone(stderr_other)
                        self.assertIn('Global arguments available for all',
                                      result['stdout'])

                        self.assertEqual(result['exit_code'], 0)
                else:
                    # auto-run
                    self.assertIn(result['exit_code'], [0, -9])

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
                    # But also complain if there is any stdout
                    if result['stdout'] == '':
                        result['stdout'] = None
                    self.assertIsNone(result['stdout'])

                sys.stdout.flush()

            return testScript

        for script_name in script_list:
            # force login to be the first, alphabetically, so the login
            # message does not unexpectedly occur during execution of
            # another script.
            # unrunnable script tests are disabled by default in load_tests()

            if script_name == 'login':
                test_name = 'test__' + script_name + '_help'
            else:
                test_name = 'test_' + script_name + '_help'
            dct[test_name] = test_execution(script_name, ['-help'])
            if script_name in ['shell', 'version',
                               'data_ingestion',  # bug 68611
                               'replicate_wiki',  # bug 68664
                               'script_wui',      # Failing on travis-ci
                               ] + failed_dep_script_list:
                dct[test_name] = unittest.expectedFailure(dct[test_name])
            dct[test_name].__doc__ = 'Test running ' + script_name + ' -help'
            dct[test_name].__name__ = test_name

            # Ideally all scripts should execute -help without
            # connecting to a site.  However pywikibot always
            # logs site.version() from live wiki.
            # TODO: make logging version() optional, then set
            #         dct[test_name].site = True
            #       for only the tests which dont respond to -help

            if script_name in deadlock_script_list:
                dct[test_name].__test__ = False

            if script_name == 'login':
                test_name = 'test__' + script_name + '_simulate'
            else:
                test_name = 'test_' + script_name + '_simulate'
            dct[test_name] = test_execution(script_name, ['-simulate'],
                                            no_args_expected_results)
            if script_name in ['catall',          # stdout user interaction
                               'checkimages',     # bug 68613
                               'data_ingestion',  # bug 68611
                               'flickrripper',    # Requires a flickr api key
                               'lonelypages',     # custom return codes
                               'nowcommons',      # deprecation warning
                               'replicate_wiki',  # custom return codes
                               'script_wui',      # Error on any user except DrTrigonBot
                               'upload',          # raises custom ValueError
                               ] + failed_dep_script_list or (
                    ((config.family != 'wikipedia' or config.mylang != 'en') and script_name == 'cfd') or
                    (config.family == 'wikipedia' and script_name == 'disambredir') or
                    (config.family == 'wikipedia' and config.mylang != 'en' and script_name == 'misspelling')):
                dct[test_name] = unittest.expectedFailure(dct[test_name])
            dct[test_name].__doc__ = \
                'Test running ' + script_name + ' -simulate.'
            dct[test_name].__name__ = test_name

            # Disable test by default in nosetests
            if script_name in unrunnable_script_list + deadlock_script_list:
                dct[test_name].__test__ = False

            # TODO: Ideally any script not on the auto_run_script_list
            # can be set as 'not a site' test, but that will require
            # auditing all code in main() to ensure it exits without
            # connecting to a site.  There are outstanding bugs about
            # connections during initialisation.
            #
            # dct[test_name].site = True

        return type.__new__(cls, name, bases, dct)


class TestScript(DefaultSiteTestCase, PwbTestCase):

    """Test cases for scripts.

    This class sets the nose 'site' attribute on each test
    depending on whether it is in the auto_run_script_list.
    """

    __metaclass__ = TestScriptMeta

    def setUp(self):
        super(TestScript, self).setUp()
        """Prepare the environment for running the pwb.py script."""
        self.old_pywikibot_dir = None
        if 'PYWIKIBOT2_DIR' in os.environ:
            self.old_pywikibot_dir = os.environ['PYWIKIBOT2_DIR']
        os.environ['PYWIKIBOT2_DIR'] = pywikibot.config.base_dir

    def tearDown(self):
        """Restore the environment after running the pwb.py script."""
        super(TestScript, self).tearDown()
        del os.environ['PYWIKIBOT2_DIR']
        if self.old_pywikibot_dir:
            os.environ['PYWIKIBOT2_DIR'] = self.old_pywikibot_dir


if sys.version_info[0] > 2:
    import six
    TestScript = six.add_metaclass(TestScriptMeta)(TestScript)

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
