# -*- coding: utf-8  -*-
"""Installer script for Pywikibot 2.0 framework."""
#
# (C) Pywikibot team, 2009-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import itertools
import os
import sys

try:
    # Work around a traceback on Python < 2.7.4 and < 3.3.1
    # http://bugs.python.org/issue15881#msg170215
    import multiprocessing  # noqa: unused
except ImportError:
    pass

PYTHON_VERSION = sys.version_info[:3]
PY2 = (PYTHON_VERSION[0] == 2)
PY26 = (PYTHON_VERSION < (2, 7))

versions_required_message = """
Pywikibot not available on:
%s

Pywikibot is only supported under Python 2.6.5+, 2.7.2+ or 3.3+
"""


def python_is_supported():
    """Check that Python is supported."""
    # Any change to this must be copied to pwb.py
    return (PYTHON_VERSION >= (3, 3, 0) or
            (PY2 and PYTHON_VERSION >= (2, 7, 2)) or
            (PY26 and PYTHON_VERSION >= (2, 6, 5)))


if not python_is_supported():
    raise RuntimeError(versions_required_message % sys.version)

test_deps = ['bz2file']

dependencies = ['requests']

# the irc module has no Python 2.6 support since 10.0
irc_dep = 'irc==8.9' if sys.version_info < (2, 7) else 'irc'
csv_dep = 'unicodecsv!=0.14.0' if PYTHON_VERSION < (2, 7) else 'unicodecsv'

extra_deps = {
    # Core library dependencies
    'isbn': ['python-stdnum'],
    'Graphviz': ['pydot>=1.0.28'],
    'Google': ['google>=1.7'],
    'IRC': [irc_dep],
    'mwparserfromhell': ['mwparserfromhell>=0.3.3'],
    'Tkinter': ['Pillow'],
    # 0.6.1 supports socket.io 1.0, but WMF is using 0.9 (T91393 and T85716)
    'rcstream': ['socketIO-client<0.6.1'],
    'security': ['requests[security]'],
    'mwoauth': ['mwoauth>=0.2.4'],
    'html': ['BeautifulSoup4'],
}

if PY2:
    # Additional core library dependencies which are only available on Python 2
    extra_deps.update({
        'csv': [csv_dep],
        'MySQL': ['oursql'],
        'unicode7': ['unicodedata2>=7.0.0-2'],
    })

script_deps = {
    'flickrripper.py': ['Pillow'],
    'states_redirect.py': ['pycountry'],
    'weblinkchecker.py': ['memento_client>=0.5.1'],
    'patrol.py': ['mwparserfromhell>=0.3.3'],
}
# flickrapi 1.4.4 installs a root logger in verbose mode; 1.4.5 fixes this.
# The problem doesnt exist in flickrapi 2.x.
# pywikibot accepts flickrapi 1.4.5+ on Python 2, as it has been stable for a
# long time, and only depends on python-requests 1.x, whereas flickrapi 2.x
# depends on python-requests 2.x, which is first packaged in Ubuntu 14.04
# and will be first packaged for Fedora Core 21.
# flickrapi 1.4.x does not run on Python 3, and setuptools can only
# select flickrapi 2.x for Python 3 installs.
script_deps['flickrripper.py'].append(
    'flickrapi>=1.4.5,<2' if PY26 else 'flickrapi')

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

if PYTHON_VERSION < (2, 7, 3):
    # work around distutils hardcoded unittest dependency
    # work around T106512
    import unittest  # noqa
    if 'test' in sys.argv:
        import unittest2
        sys.modules['unittest'] = unittest2

if sys.version_info[0] == 2:
    if PY26:
        script_deps['replicate_wiki.py'] = ['argparse']
        dependencies.append('future>=0.15.0')  # provides collections backports

        dependencies += extra_deps['unicode7']  # T102461 workaround

    # tools.ip does not have a hard dependency on an IP address module,
    # as it falls back to using regexes if one is not available.
    # The functional backport of py3 ipaddress is acceptable:
    # https://pypi.python.org/pypi/ipaddress
    # However the Debian package python-ipaddr is also supported:
    # https://pypi.python.org/pypi/ipaddr
    # Other backports are likely broken.
    # ipaddr 2.1.10+ is distributed with Debian and Fedora.  See T105443.
    dependencies.append('ipaddr>=2.1.10')

    if sys.version_info < (2, 7, 9):
        # Python versions before 2.7.9 will cause urllib3 to trigger
        # InsecurePlatformWarning warnings for all HTTPS requests. By
        # installing with security extras, requests will automatically set
        # them up and the warnings will stop. See
        # <https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning>
        # for more details.
        dependencies += extra_deps['security']

    script_deps['data_ingestion.py'] = extra_deps['csv']

try:
    import bz2  # noqa: unused import
except ImportError:
    # Use bz2file if the python is not compiled with bz2 support.
    dependencies.append('bz2file')

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
    if 'oursql' in test_deps and os.name == 'nt':
        test_deps.remove('oursql')  # depends on Cython

    if 'requests[security]' in test_deps:
        # Bug T105767 on Python 2.7 release 9+
        if sys.version_info[:2] == (2, 7) and sys.version_info[2] >= 9:
            test_deps.remove('requests[security]')

# These extra dependencies are needed other unittest fails to load tests.
if sys.version_info[0] == 2:
    test_deps += extra_deps['csv']
else:
    test_deps += ['six']

from setuptools import setup, find_packages

name = 'pywikibot'
version = '3.0-dev'
github_url = 'https://github.com/wikimedia/pywikibot-core'

setup(
    name=name,
    version=version,
    description='Python MediaWiki Bot Framework',
    long_description=open('README.rst').read(),
    maintainer='The Pywikibot team',
    maintainer_email='pywikibot@lists.wikimedia.org',
    license='MIT License',
    packages=[str(name)] + [package
                            for package in find_packages()
                            if package.startswith('pywikibot.')],
    install_requires=dependencies,
    dependency_links=dependency_links,
    extras_require=extra_deps,
    url='https://www.mediawiki.org/wiki/Pywikibot',
    test_suite="tests.collector",
    tests_require=test_deps,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Operating System :: OS Independent',
        'Intended Audience :: Developers',
        'Environment :: Console',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
    ],
    use_2to3=False
)
