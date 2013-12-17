# -*- coding: utf-8  -*-
"""
Installer script for Pywikibot 2.0 framework
"""
#
# (C) Pywikibot team, 2009-2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import sys
import os

from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
from setuptools.command import install

test_deps = []
testcollector = "tests"

if sys.version_info[0] == 2:
    if sys.version_info[1] < 6:
        raise RuntimeError("ERROR: Pywikipediabot only runs under Python 2.6 or higher")
    elif sys.version_info[1] == 6:
        test_deps = ['unittest2']
        testcollector = "tests.utils.collector"

if sys.version_info[0] == 3:
    if not os.environ.get('PY3', False):
        # use setup.py test --python3ok  to run tests
        print("ERROR: Pywikipediabot only runs under Python 2")
        sys.exit(1)
    if sys.version_info[1] < 3:
        print("ERROR: Python 3.3 or higher is required!")
        sys.exit(1)


class pwb_install(install.install):
    """
    Setuptools' install command subclassed to automatically call
    `generate_user_files.py` after installing the package.
    """
    def run(self):
        install.install.do_egg_install(self)

        if sys.stdin.isatty():
            import subprocess
            python = sys.executable
            python = python.replace("pythonw.exe", "python.exe")  # for Windows
            subprocess.call([python, "generate_user_files.py"])

setup(
    name='Pywikipediabot',
    version='2.0b1',
    description='Python Wikipedia Bot Framework',
    license='MIT License',
    packages=[package
              for package in find_packages()
              if package.startswith('pywikibot.')],
    install_requires=[
        'httplib2>=0.6.0'
    ],
    dependency_links=[
        'https://git.wikimedia.org/zip/?r=pywikibot/externals/httplib2.git&format=gz#egg=httplib2-0.8-pywikibot1'
    ],
    test_suite=testcollector,
    tests_require=test_deps,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta'
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7'
    ],
    cmdclass={
        'install': pwb_install
    },
    use_2to3=False
)
