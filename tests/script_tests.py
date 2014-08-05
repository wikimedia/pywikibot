# -*- coding: utf-8  -*-
"""Test that each script can be compiled and executed."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import os
import sys
import time
import subprocess
import pywikibot
from pywikibot import config
from tests.utils import unittest, PywikibotTestCase


base_path = os.path.split(os.path.split(__file__)[0])[0]
pwb_path = os.path.join(base_path, 'pwb.py')
scripts_path = os.path.join(base_path, 'scripts')


script_deps = {
    'script_wui.py': ['crontab', 'lua'],
    # Note: package 'lunatic-python' provides module 'lua'

    'flickrripper.py': ['ImageTk', 'flickrapi'],
    # Note: 'PIL' is not available via pip2.7 on MS Windows,
    #       however it is available with setuptools.
}
if sys.version_info < (2, 7):
    script_deps['replicate_wiki.py'] = ['argparse']


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


def runnable_script_list(scripts_path):
    """List of scripts which may be executed."""
    dir_list = os.listdir(scripts_path)
    script_list = [name[0:-3] for name in dir_list  # strip .py
                   if name.endswith('.py')
                   and not name.startswith('_')  # skip __init__.py and _*
                   and check_script_deps(name)
                   and name != 'login.py'        # this is moved to be first
                   and name != 'imageuncat.py'   # this halts indefinitely
                   and name != 'welcome.py'      # result depends on speed
                   and name != 'script_wui.py'   # depends on lua compiling
                   ]
    return ['login'] + script_list

script_input = {
    'catall': 'q\n',  # q for quit
    'disambredir': '\n',  # prompts for user to choose action to take
    'editarticle': 'Test page\n',
    'imagetransfer': 'Test page\n',
    'interwiki': 'Test page\n',
    'makecat': 'Test page\n\n',
    # 'misspelling': 'q\n',   # pressing 'q' doesnt work. bug 68663
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
    'lonelypages',
    'makecat',
    'misspelling',
    'revertbot',
    'noreferences',
    'nowcommons',
    'script_wui',
    'shell',
    'solve_disambiguation',
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
    'replace': 'Press Enter to use this default message',
    'replicate_wiki': 'error: too few arguments',
    'script_wui': 'Pre-loading all relevant page contents',
    'shell': 'Welcome to the',
    'spamremove': 'No spam site specified',
    'transferbot': 'Target site not different from source site',  # Bug 68662
    'version': 'unicode test: ',
    'watchlist': 'Retrieving watchlist',

    # The following auto-run and typically cant be validated,
    # however these strings are very likely to exist within
    # the timeout of 5 seconds.
    'makecat': '(Default is [[',
    'revertbot': 'Fetching new batch of contributions',
    'upload': 'ERROR: Upload error',
}


def execute(command, data_in=None, timeout=0):
    """Execute a command and capture outputs."""
    options = {
        'stdout': subprocess.PIPE,
        'stderr': subprocess.PIPE
    }
    if data_in is not None:
        options['stdin'] = subprocess.PIPE

    p = subprocess.Popen(command, **options)
    if data_in is not None:
        p.stdin.write(data_in)
    waited = 0
    while waited < timeout and p.poll() is None:
        time.sleep(1)
        waited += 1
    if timeout and p.poll() is None:
        p.kill()
    data_out = p.communicate()
    return {'exit_code': p.returncode,
            'stdout': data_out[0],
            'stderr': data_out[1]}


class TestScriptMeta(type):

    """Test meta class."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def test_execution(script_name, args=None, expected_results=None):
            def testScript(self):
                cmd = [sys.executable, pwb_path, script_name]

                if args:
                    cmd += args

                data_in = script_input.get(script_name)

                timeout = 0
                if script_name in auto_run_script_list:
                    timeout = 5
                result = execute(cmd, data_in, timeout=timeout)

                if expected_results and script_name in expected_results:
                    if expected_results[script_name] is not None:
                        self.assertIn(expected_results[script_name],
                                      result['stderr'])
                elif (args and '-help' in args) or \
                        script_name not in auto_run_script_list:
                    self.assertEqual(result['stderr'], '')
                    self.assertIn('Global arguments available for all',
                                  result['stdout'])
                    self.assertEqual(result['exit_code'], 0)
                self.assertNotIn('Traceback (most recent call last)',
                                 result['stderr'])
            return testScript

        for script_name in runnable_script_list(scripts_path):
            # force login to be the first, alphabetically, so the login
            # message does not unexpectedly occur during execution of
            # another script.
            if script_name == 'login':
                test_name = 'test__' + script_name + '_execution'
            else:
                test_name = 'test_' + script_name + '_execution'
            dct[test_name] = test_execution(script_name, ['-help'])
            if script_name in ['shell', 'version',
                               'checkimages',     # bug 68613
                               'data_ingestion',  # bug 68611
                               'flickrripper',    # bug 68606 (and others)
                               'replicate_wiki',  # bug 68664
                               'script_wui',      # Failing on travis-ci
                               ]:
                dct[test_name] = unittest.expectedFailure(dct[test_name])
            dct[test_name].__doc__ = 'Test running ' + script_name + '.'

            if script_name == 'login':
                test_name = 'test__' + script_name + '_no_args'
            else:
                test_name = 'test_' + script_name + '_no_args'
            dct[test_name] = test_execution(script_name, ['-simulate'],
                                            no_args_expected_results)
            if script_name in ['checkimages',     # bug 68613
                               'data_ingestion',  # bug 68611
                               'disambredir',     # quittable auto-run with
                                                  # highly variable output.
                               'flickrripper',    # bug 68606 (and deps)
                               'imagerecat',      # bug 68658
                               'imagetransfer',   # bug 68659
                               'pagefromfile',    # bug 68660
                               'transferbot',     # raises custom Exception
                               'upload',          # raises custom ValueError
                               ] or \
                    (config.family == 'wikidata' and script_name == 'lonelypages') or \
                    ((config.family != 'wikipedia' or config.mylang != 'en') and script_name == 'cfd') or \
                    (config.family == 'wikipedia' and config.mylang != 'en' and script_name == 'misspelling'):
                dct[test_name] = unittest.expectedFailure(dct[test_name])
            dct[test_name].__doc__ = \
                'Test running ' + script_name + ' without arguments.'

        return type.__new__(cls, name, bases, dct)


class TestScript(PywikibotTestCase):

    """Test cases for scripts."""

    __metaclass__ = TestScriptMeta

    def setUp(self):
        """Prepare the environment for running the pwb.py script."""
        self.old_pywikibot_dir = None
        if 'PYWIKIBOT2_DIR' in os.environ:
            self.old_pywikibot_dir = os.environ['PYWIKIBOT2_DIR']
        os.environ['PYWIKIBOT2_DIR'] = pywikibot.config.base_dir

    def tearDown(self):
        """Restore the environment after running the pwb.py script."""
        del os.environ['PYWIKIBOT2_DIR']
        if self.old_pywikibot_dir:
            os.environ['PYWIKIBOT2_DIR'] = self.old_pywikibot_dir


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
