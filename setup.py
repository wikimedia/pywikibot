# -*- coding: utf-8  -*-
"""installer script for pywikibot 2.0 framework"""
#
# (C) Pywikipedia team, 2009-2012
#
__version__ = '$Id$'
#
# Distributed under the terms of the MIT license.
#
import sys

from distribute_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

if sys.version_info[0] != 2:
    raise RuntimeError("ERROR: Pywikipediabot only runs under Python 2")
if sys.version_info[1] < 6:
    raise RuntimeError("ERROR: Pywikipediabot only runs under Python 2.6 or higher")
else:
    depend = ['httplib2>=0.6.0']

setup(name='Pywikipediabot',
      version ='2.0alpha',
      description ='Python Wikipedia Bot Framework',
      license = 'MIT',
      packages = find_packages(),
      install_requires = depend
     )

# automatically launch generate_user_files.py

import subprocess
python = sys.executable
python = python.replace("pythonw.exe", "python.exe") # for Windows
ignore = subprocess.call([python, "generate_user_files.py"])
