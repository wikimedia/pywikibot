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
import itertools

test_deps = []

dependencies = ['httplib2>=0.6.0']

extra_deps = {
    # Core library dependencies
    'daemonize': ['daemonize'],
    'Graphviz':  ['pydot'],
    'MySQL': ['oursql'],
    'Yahoo': ['yahoo'],
    'Google': ['google'],
    'IRC': ['irc'],
    'mwparserfromhell': ['mwparserfromhell>=0.3.3']
}

script_deps = {
    'script_wui.py': ['irc', 'lunatic-python', 'crontab'],
    # Note: None of the 'lunatic-python' repos on github support MS Windows.
    'flickrripper.py': ['Pillow', 'flickrapi'],
    # Note: 'PIL' is not available via pip2.7 on MS Windows,
    #       however it is available with setuptools.
}

if sys.version_info[0] == 2:
    if sys.version_info < (2, 6, 5):
        raise RuntimeError("ERROR: Pywikibot only runs under Python 2.6.5 or higher")
    elif sys.version_info[1] == 6:
        # work around distutils hardcoded unittest dependency
        import unittest  # flake8: noqa
        if 'test' in sys.argv and sys.version_info < (2, 7):
            import unittest2
            sys.modules['unittest'] = unittest2

        script_deps['replicate_wiki.py'] = ['argparse']
        dependencies.append('ordereddict')

if sys.version_info[0] == 3:
    if not os.environ.get('PY3', False):
        # use setup.py test --python3ok  to run tests
        print("ERROR: Pywikibot only runs under Python 2")
        sys.exit(1)
    if sys.version_info[1] < 3:
        print("ERROR: Python 3.3 or higher is required!")
        sys.exit(1)

if os.name != 'nt':
    # See bug 66010, Windows users will have issues
    # when trying to build the C modules.
    dependencies += extra_deps['mwparserfromhell']

if os.name == 'nt':
    # FIXME: tests/ui_tests.py suggests pywinauto 0.4.2
    # which isnt provided on pypi.
    test_deps += ['pywin32>=218', 'pywinauto>=0.4.0']

extra_deps.update(script_deps)
# Add script dependencies as test dependencies,
# so scripts can be compiled in test suite.
if 'PYSETUP_TEST_EXTRAS' in os.environ:
    test_deps += list(itertools.chain(*(script_deps.values())))


# late import of setuptools due to monkey-patching above
from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages
from setuptools.command import install


class pwb_install(install.install):

    """
    Setuptools' install command subclassed to automatically call
    `generate_user_files.py` after installing the package.
    """
    def run(self):
        install.install.do_egg_install(self)

        if sys.stdin.isatty() and sys.stdout.isatty():
            import subprocess
            python = sys.executable
            python = python.replace("pythonw.exe", "python.exe")  # for Windows
            subprocess.call([python, "generate_user_files.py"])

setup(
    name='pywikibot',
    version='2.0b1',
    description='Python MediaWiki Bot Framework',
    long_description=open('README.rst').read(),
    maintainer='The pywikibot team',
    maintainer_email='pywikipedia-l@lists.wikimedia.org',
    license='MIT License',
    packages=['pywikibot'] +
             [package
              for package in find_packages()
              if package.startswith('pywikibot.')],
    install_requires=dependencies,
    extras_require=extra_deps,
    dependency_links=[
        'https://git.wikimedia.org/zip/?r=pywikibot/externals/httplib2.git&format=gz#egg=httplib2-0.8-pywikibot1',
        'git+https://github.com/AlereDevices/lunatic-python.git#egg=lunatic-python',
        'git+https://github.com/jayvdb/parse-crontab.git#egg=crontab',
    ],
    url='https://www.mediawiki.org/wiki/Pywikibot',
    download_url='https://github.com/wikimedia/pywikibot-core/archive/master.zip#egg=pywikibot-2.0b1',
    test_suite="tests.collector",
    tests_require=test_deps,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Programming Language :: Python :: 2.7'
    ],
    cmdclass={
        'install': pwb_install
    },
    use_2to3=False
)
