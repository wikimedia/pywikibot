# -*- coding: utf-8  -*-
"""Installer script for Pywikibot 2.0 framework."""
#
# (C) Pywikibot team, 2009-2015
#
# Distributed under the terms of the MIT license.
#

import itertools
import os
import sys

test_deps = []

dependencies = ['httplib2>=0.9']

# the irc module has no Python 2.6 support since 10.0
irc_dep = 'irc==8.9' if sys.version_info < (2, 7) else 'irc'

extra_deps = {
    # Core library dependencies
    'isbn': ['python-stdnum'],
    'Graphviz':  ['pydot>=1.0.28'],
    'Google': ['google'],
    'IRC': [irc_dep],
    'mwparserfromhell': ['mwparserfromhell>=0.3.3'],
    'Tkinter': ['Pillow'],
    # 0.6.1 supports socket.io 1.0, but WMF is using 0.9 (T91393 and T85716)
    'rcstream': ['socketIO-client<0.6.1'],
}

if sys.version_info[0] == 2:
    # Additional core library dependencies which are only available on Python 2
    extra_deps.update({
        'csv': ['unicodecsv'],
        'MySQL': ['oursql'],
        'Yahoo': ['pYsearch'],
    })

script_deps = {
    'flickrripper.py': ['Pillow'],
    'states_redirect.py': ['pycountry'],
}
# flickrapi 1.4.4 installs a root logger in verbose mode; 1.4.5 fixes this.
# The problem doesnt exist in flickrapi 2.x.
# pywikibot accepts flickrapi 1.4.5+ on Python 2, as it has been stable for a
# long time, and only depends on python-requests 1.x, whereas flickrapi 2.x
# depends on python-requests 2.x, which is first packaged in Ubuntu 14.04
# and will be first packaged for Fedora Core 21.
# flickrapi 1.4.x does not run on Python 3, and setuptools can only
# select flickrapi 2.x for Python 3 installs.
script_deps['flickrripper.py'].append('flickrapi' if sys.version_info[0] > 2
                                      else 'flickrapi>=1.4.5')

# lunatic-python is only available for Linux
if sys.platform.startswith('linux'):
    script_deps['script_wui.py'] = [irc_dep, 'lunatic-python', 'crontab']

# The main pywin32 repository contains a Python 2 only setup.py with a small
# wrapper setup3.py for Python 3.
# http://pywin32.hg.sourceforge.net:8000/hgroot/pywin32/pywin32
# The main pywinauto repository doesnt support Python 3.
# The repositories used below have a Python 3 compliant setup.py
dependency_links = [
    'git+https://github.com/AlereDevices/lunatic-python.git#egg=lunatic-python',
    'hg+https://bitbucket.org/TJG/pywin32#egg=pywin32',
    'git+https://github.com/vasily-v-ryabov/pywinauto-64#egg=pywinauto',
    'git+https://github.com/nlhepler/pydot#egg=pydot-1.0.29',
]

if sys.version_info[0] == 2:
    if sys.version_info < (2, 6, 5):
        raise RuntimeError("ERROR: Pywikibot only runs under Python 2.6.5 or higher")
    elif sys.version_info[1] == 6:
        # work around distutils hardcoded unittest dependency
        import unittest  # noqa
        if 'test' in sys.argv and sys.version_info < (2, 7):
            import unittest2
            sys.modules['unittest'] = unittest2

        script_deps['replicate_wiki.py'] = ['argparse']
        dependencies.append('future')  # provides collections backports

    # tools.ip does not depend on an ipaddress module, as it falls back to
    # using regexes if not available, however the pywikibot package should use
    # the functional backport of py3 ipaddress, which is:
    # https://pypi.python.org/pypi/ipaddress
    # Other backports are likely broken.
    dependencies.append('ipaddress')

    script_deps['data_ingestion.py'] = extra_deps['csv']

    # mwlib is not available for py3
    script_deps['patrol'] = ['mwlib']

if sys.version_info[0] == 3:
    if sys.version_info[1] < 3:
        print("ERROR: Python 3.3 or higher is required!")
        sys.exit(1)

if os.name != 'nt':
    # See bug 66010, Windows users will have issues
    # when trying to build the C modules.
    dependencies += extra_deps['mwparserfromhell']

# Some of the ui_tests depend on accessing the console window's menu
# to set the console font and copy and paste, achieved using pywinauto
# which depends on pywin32.
# These tests may be disabled because pywin32 depends on VC++, is time
# comsuming to build, and the console window cant be accessed during appveyor
# builds.
# Microsoft makes available a compiler for Python 2.7
# http://www.microsoft.com/en-au/download/details.aspx?id=44266
# If you set up your own compiler for Python 3, on 3.3 two demo files
# packaged with pywin32 may fail.  Remove com/win32com/demos/ie*.py
if os.name == 'nt' and os.environ.get('PYSETUP_TEST_NO_UI', '0') != '1':
    # FIXME: tests/ui_tests.py suggests pywinauto 0.4.2
    # which isnt provided on pypi.
    test_deps += ['pywin32', 'pywinauto>=0.4.0']

extra_deps.update(script_deps)

# Add all dependencies as test dependencies,
# so all scripts can be compiled for script_tests, etc.
if 'PYSETUP_TEST_EXTRAS' in os.environ:
    test_deps += list(itertools.chain(*(extra_deps.values())))
    # mwlib requires 'pyparsing>=1.4.11,<1.6', which conflicts with
    # pydot's requirement for pyparsing>=2.0.1.
    if 'mwlib' in test_deps:
        test_deps.remove('mwlib')

# These extra dependencies are needed other unittest fails to load tests.
if sys.version_info[0] == 2:
    test_deps += extra_deps['csv']
else:
    test_deps += ['six']

# late import of setuptools due to monkey-patching above
from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup, find_packages

name = 'pywikibot'
version = '2.0b3'
github_url = 'https://github.com/wikimedia/pywikibot-core'
download_url = github_url + '/archive/master.zip#egg=' + name + '-' + version

setup(
    name=name,
    version=version,
    description='Python MediaWiki Bot Framework',
    long_description=open('README.rst').read(),
    maintainer='The Pywikibot team',
    maintainer_email='pywikipedia-l@lists.wikimedia.org',
    license='MIT License',
    packages=['pywikibot'] + [package
                              for package in find_packages()
                              if package.startswith('pywikibot.')],
    install_requires=dependencies,
    dependency_links=dependency_links,
    extras_require=extra_deps,
    url='https://www.mediawiki.org/wiki/Pywikibot',
    download_url=download_url,
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
    use_2to3=False
)
