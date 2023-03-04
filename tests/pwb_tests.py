#!/usr/bin/env python3
"""
Test pwb.py.

If pwb.py does not load python files as expected, more tests from coverage
should be added locally.
https://bitbucket.org/ned/coveragepy/src/default/tests/test_execfile.py
"""
#
# (C) Pywikibot team, 2007-2022
#
# Distributed under the terms of the MIT license.
#
import io
import sys
import unittest

from tests import create_path_func, join_tests_path
from tests.aspects import PwbTestCase
from tests.utils import execute, execute_pwb


join_pwb_tests_path = create_path_func(join_tests_path, 'pwb')


class TestPwb(PwbTestCase):

    """Test pwb.py functionality.

    This is registered as a Site test because it will not run without a
    user config file.
    """

    # site must be explicitly set for pwb tests. This test does not require
    # network access, because tests/pwb/print_locals.py does not use
    # handle_args, etc. so version.py doesn't talk on the network.
    site = False
    net = False

    def _do_check(self, name):
        package_name = 'tests.pwb.' + name
        script_path = join_pwb_tests_path(name + '.py')

        direct = execute([sys.executable, '-m', package_name])
        vpwb = execute_pwb([script_path])
        self.maxDiff = None
        self.assertEqual(direct['stdout'], vpwb['stdout'])

        return (direct, vpwb)

    def test_env(self):
        """
        Test external environment of pywikibot.

        Make sure the environment is not contaminated, and is the same as
        the environment we get when directly running a script.
        """
        self._do_check('print_env')

    def test_locals(self):
        """
        Test internal environment of pywikibot.

        Make sure the environment is not contaminated, and is the same as
        the environment we get when directly running a script.
        """
        self._do_check('print_locals')

    def test_unicode(self):
        """Test printing unicode in pywikibot."""
        (direct, vpwb) = self._do_check('print_unicode')

        self.assertEqual('Häuser', direct['stdout'].strip())
        self.assertEqual('Häuser', direct['stderr'].strip())
        self.assertEqual('Häuser', vpwb['stdout'].strip())
        self.assertEqual('Häuser', vpwb['stderr'].strip())

    def test_argv(self):
        """Test argv of pywikibot.

        Make sure that argv passed to the script is not contaminated by
        global options given to pwb.py wrapper.
        """
        script_name = 'print_argv'
        script_path = join_pwb_tests_path(script_name + '.py')
        script_opts = ['-help']
        command = [script_path] + script_opts
        without_global_args = execute_pwb(command)
        with_no_global_args = execute_pwb(['-maxlag:5'] + command)
        self.assertEqual(without_global_args['stdout'],
                         with_no_global_args['stdout'])
        self.assertEqual(without_global_args['stdout'].rstrip(),
                         str([script_name] + script_opts))

    def test_script_found(self):
        """Test pwb.py script call which is found."""
        stdout = io.StringIO(execute_pwb(['pwb'])['stdout'])
        self.assertEqual(stdout.readline().strip(),
                         'Wrapper script to invoke pywikibot-based scripts.')

    def test_script_not_found(self):
        """Test pwbot.py script call which is not found."""
        stderr = io.StringIO(execute_pwb(['pywikibot'])['stderr'])
        self.assertEqual(stderr.readline().strip(),
                         'ERROR: pywikibot.py not found! Misspelling?')

    def test_one_similar_script(self):
        """Test shell.py script call which gives one similar result."""
        result = [
            'ERROR: hello.py not found! Misspelling?',
            'NOTE: Starting the most similar script shell.py',
            'in 5.0 seconds; type CTRL-C to stop.',
        ]
        stream = execute_pwb(['hello'], data_in=chr(3), timeout=10)
        stderr = io.StringIO(stream['stderr'])
        with self.subTest(line=0):
            self.assertEqual(stderr.readline().strip(), result[0])
        with self.subTest(line=1):
            text = stderr.readline().strip()
            self.assertTrue(
                text.startswith(result[1]),
                msg=f'"{text}" does not start with "{result[1]}"')
        with self.subTest(line=2):
            self.assertEqual(stderr.readline().strip(), result[2])

    def test_similar_scripts_found(self):
        """Test script call which gives multiple similar results."""
        result = [
            'ERROR: inter_wikidata.py not found! Misspelling?',
            '',
            'The most similar scripts are:',
            '1 - interwikidata',
            '2 - interwiki',
            '3 - illustrate_wikidata',
        ]
        stderr = io.StringIO(
            execute_pwb(['inter_wikidata'], data_in='q')['stderr'])
        for line in result:
            with self.subTest(line=line):
                self.assertEqual(stderr.readline().strip(), line)
        remaining = stderr.readlines()
        self.assertLength(remaining, 3)  # always 3 lines remaining after list


if __name__ == '__main__':  # pragma: no cover
    unittest.main(verbosity=10)
