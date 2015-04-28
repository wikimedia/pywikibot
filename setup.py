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
    'daemonize': ['daemonize'],
    'Graphviz':  ['pydot'],
    'MySQL': ['oursql'],
    'Yahoo': ['pYsearch'],
    'Google': ['google'],
    'IRC': [irc_dep],
    'mwparserfromhell': ['mwparserfromhell>=0.3.3'],
    'Tkinter': ['Pillow'],
    # 0.6.1 supports socket.io 1.0, but WMF is using 0.9 (T91393 and T85716)
    'rcstream': ['socketIO-client<0.6.1'],
}

if sys.version_info[0] == 2:
    # csv is used by wikistats and script data_ingestion
    extra_deps['csv'] = ['unicodecsv']

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

dependency_links = [
    'git+https://github.com/AlereDevices/lunatic-python.git#egg=lunatic-python',
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

# setup can't detect or install pywin32, which pywinauto depends on.
# appveyor builds do not install pywin32
if os.name == 'nt':
    # FIXME: tests/ui_tests.py suggests pywinauto 0.4.2
    # which isnt provided on pypi.
    test_deps += ['pywinauto>=0.4.0']

extra_deps.update(script_deps)

# Add all script dependencies as test dependencies,
# so all scripts can be compiled for script_tests, etc.
if 'PYSETUP_TEST_EXTRAS' in os.environ:
    test_deps += list(itertools.chain(*(script_deps.values())))

# These extra dependencies enable some tests to run on all builds
if sys.version_info[0] == 2:
    test_deps += extra_deps['csv']
else:
    test_deps += ['six']
test_deps += extra_deps['rcstream']

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
