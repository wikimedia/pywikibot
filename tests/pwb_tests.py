# -*- coding: utf-8  -*-
#
# (C) Pywikipedia bot team, 2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import os
import sys
import subprocess

import unittest

import pywikibot

pypath = sys.executable
basepath = os.path.split(os.path.split(__file__)[0])[0]
pwbpath = os.path.join(basepath, 'pwb.py')
testbasepath = os.path.join(basepath, 'tests', 'pwb')


class TestPwb(unittest.TestCase):
    def setUp(self):
        self.oldenviron = os.environ.copy()
        os.environ['PYWIKIBOT2_DIR'] = pywikibot.config.base_dir

    def tearDown(self):
        del os.environ['PYWIKIBOT2_DIR']
        if 'PYWIKIBOT2_DIR' in self.oldenviron:
            os.environ['PYWIKIBOT2_DIR'] = self.oldenviron['PYWIKIBOT2_DIR']

    def testScriptEnvironment(self):
        """Make sure the environment is not contaminated, and is the same as
           the environment we get when directly running a script."""
        test = os.path.join(testbasepath, 'print_locals.py')

        direct = subprocess.check_output([pypath, test])
        vpwb = subprocess.check_output([pypath, pwbpath, test])
        self.assertEqual(direct, vpwb)

if __name__ == "__main__":
    unittest.main(verbosity=10)
