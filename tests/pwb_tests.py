#!/usr/bin/env python3
#
# (C) Pywikibot team, 2007-2026
#
# Distributed under the terms of the MIT license.
#
"""Test pwb.py."""
from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path
from platform import python_implementation
from unittest.mock import patch

import pywikibot
from pywikibot import config
from pywikibot.scripts import wrapper
from tests import create_path_func, join_tests_path
from tests.aspects import PwbTestCase
from tests.utils import execute, execute_pwb


join_pwb_tests_path = create_path_func(join_tests_path, 'pwb')


class TestPwb(PwbTestCase):

    """Test pwb.py functionality.

    This is registered as a Site test because it will not run without a
    user config file.

    .. note::
       ``site`` must be explicitly set for pwb tests. This test does not
       require network access, because tests/pwb/print_locals.py does
       not use handle_args, etc. so version.py doesn't talk on the
       network.
    """

    site = False
    net = False

    def _do_check(self, name):
        package_name = 'tests.pwb.' + name
        script_path = join_pwb_tests_path(name + '.py')

        direct = execute([sys.executable, '-m', package_name])
        vpwb = execute_pwb([script_path])

        self.assertIsNone(direct['timeout'])
        self.assertIsNone(vpwb['timeout'])
        self.maxDiff = None
        self.assertEqual(direct['stdout'], vpwb['stdout'])

        return (direct, vpwb)

    def test_env(self) -> None:
        """Test external environment of pywikibot.

        Make sure the environment is not contaminated, and is the same
        as the environment we get when directly running a script.
        """
        self._do_check('print_env')

    def test_locals(self) -> None:
        """Test internal environment of pywikibot.

        Make sure the environment is not contaminated, and is the same
        as the environment we get when directly running a script.
        """
        self._do_check('print_locals')

    def test_unicode(self) -> None:
        """Test printing unicode in pywikibot."""
        (direct, vpwb) = self._do_check('print_unicode')

        self.assertEqual('Häuser', direct['stdout'].strip())
        self.assertEqual('Häuser', direct['stderr'].strip())
        self.assertEqual('Häuser', vpwb['stdout'].strip())
        self.assertEqual('Häuser', vpwb['stderr'].strip())

    def test_argv(self) -> None:
        """Test argv of pywikibot.

        Make sure that argv passed to the script is not contaminated by
        global options given to pwb.py wrapper.
        """
        script_name = 'print_argv'
        script_path = join_pwb_tests_path(script_name + '.py')
        script_opts = ['-help']
        command = [script_path, *script_opts]
        without_global_args = execute_pwb(command)
        with_no_global_args = execute_pwb(['-maxlag:5', *command])
        self.assertEqual(without_global_args['stdout'],
                         with_no_global_args['stdout'])
        self.assertEqual(without_global_args['stdout'].rstrip(),
                         str([script_name, *script_opts]))

    def test_script_found(self) -> None:
        """Test pwb.py script call which is found."""
        stdout = io.StringIO(execute_pwb(['pwb'])['stdout'])
        self.assertEqual(stdout.readline().strip(),
                         'Wrapper script to invoke pywikibot-based scripts.')

    @unittest.skipIf(python_implementation() == 'GraalVM', reason='T413711')
    def test_script_not_found(self) -> None:
        """Test pwbot.py script call which is not found."""
        stderr = io.StringIO(execute_pwb(['pywikibot'])['stderr'])
        self.assertEqual(stderr.readline().strip(),
                         'ERROR: pywikibot.py not found! Misspelling?')

    def test_one_similar_script(self) -> None:
        """Test shell.py script call which gives one similar result."""
        wait_time = config.pwb_autostart_waittime
        scripts_path = Path(wrapper.__file__).parent
        shell_path = scripts_path / 'shell.py'

        with (
            patch.object(pywikibot, 'error') as error,
            patch.object(pywikibot, 'info') as info,
            patch.object(wrapper, 'sleep') as sleep,
        ):
            filename = wrapper.find_alternates('hello.py', [scripts_path])

        self.assertEqual(filename, str(shell_path))
        error.assert_called_once_with('hello.py not found! Misspelling?')
        info.assert_called_once_with(
            'NOTE: Starting the most similar script '
            '<<lightyellow>>shell.py<<default>>\n'
            f'      in {wait_time} seconds; type CTRL-C to stop.'
        )
        sleep.assert_called_once_with(wait_time)

    @unittest.skipIf(python_implementation() == 'GraalVM', reason='T413711')
    def test_similar_scripts_found(self) -> None:
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

    def test_console_scripts_entry_point(self) -> None:
        """Test that the pwb console_scripts entry point is registered.

        Verifies the site-package ``pwb`` entry point maps to
        :func:`pywikibot.scripts.wrapper.run` (T420109).
        """
        from importlib.metadata import entry_points

        eps = entry_points()
        try:
            console = eps.select(group='console_scripts')
        except AttributeError:  # Python < 3.10 compatibility path
            console = eps.get('console_scripts', [])

        pwb_eps = [ep for ep in console if ep.name == 'pwb']
        self.assertTrue(pwb_eps, 'console_scripts entry point "pwb" not found')
        self.assertEqual(pwb_eps[0].value, 'pywikibot.scripts.wrapper:run')
        self.assertIs(pwb_eps[0].load(), wrapper.run)

    def test_site_package_run_entry_point(self) -> None:
        """Test wrapper.run() site-package entry point behavior (T420109)."""
        with (
            patch.object(wrapper, 'site_package', False),
            patch.object(wrapper, 'execute', return_value=False) as execute,
            patch('builtins.print') as mock_print,
        ):
            wrapper.run()
            self.assertTrue(wrapper.site_package)
            execute.assert_called_once_with()
            mock_print.assert_called_once_with(wrapper.__doc__)

        with (
            patch.object(wrapper, 'site_package', False),
            patch.object(wrapper, 'execute', return_value=True) as execute,
            patch('builtins.print') as mock_print,
        ):
            wrapper.run()
            self.assertTrue(wrapper.site_package)
            execute.assert_called_once_with()
            mock_print.assert_not_called()


if __name__ == '__main__':
    unittest.main(verbosity=10)
