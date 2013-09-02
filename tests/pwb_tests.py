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

pypath = sys.executable
basepath = os.path.split(os.path.split(__file__)[0])[0]
pwbpath  = os.path.join(basepath, 'pwb.py')
testbasepath = os.path.join(basepath, 'tests', 'pwb')

class TestPwb(unittest.TestCase):
    def testScriptEnvironment(self):
        """Make sure the environment is not contaminated, and is the same as
           the environment we get when directly running a script."""
        test = os.path.join(testbasepath, 'print_locals.py')

        direct = subprocess.check_output([pypath, test])
        vpwb   = subprocess.check_output([pypath, pwbpath, test])
        self.assertEqual(direct, vpwb)

if __name__=="__main__":
    unittest.main(verbosity=10)
