# -*- coding: utf-8  -*-
"""
Test pwb.py.

If pwb.py does not load python files as expected, more tests from coverage
should be added locally.
https://bitbucket.org/ned/coveragepy/src/default/tests/test_execfile.py
"""
#
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import os
import sys

from tests import _tests_dir
from tests.utils import execute, execute_pwb
from tests.aspects import unittest, PwbTestCase

_pwb_tests_dir = os.path.join(_tests_dir, 'pwb')


class TestPwb(PwbTestCase):

    """
    Test pwb.py functionality.

    This is registered as a Site test because it will not run
    without a user-config.py
    """

    # site must be explicitly set for pwb tests. This test does not require
    # network access, because tests/pwb/print_locals.py does not use
    # handle_args, etc. so version.py doesnt talk on the network.
    site = False
    net = False

    def _do_check(self, name):
        package_name = 'tests.pwb.' + name
        script_path = os.path.join(_pwb_tests_dir, name + '.py')

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


if __name__ == "__main__":
    unittest.main(verbosity=10)
