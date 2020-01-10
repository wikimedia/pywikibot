# -*- coding: utf-8 -*-
"""Installer script for Pywikibot 3.0 framework."""
#
# (C) Pywikibot team, 2009-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import os
import sys

from setuptools import find_packages, setup

PYTHON_VERSION = sys.version_info[:3]
PY2 = (PYTHON_VERSION[0] == 2)

versions_required_message = """
Pywikibot is not available on:
{version}

This version of Pywikibot only supports Python 2.7.4+ or 3.4+.
"""


def python_is_supported():
    """Check that Python is supported."""
    # Any change to this must be copied to pwb.py
    return PYTHON_VERSION >= (3, 4, 0) or PY2 and PYTHON_VERSION >= (2, 7, 4)


if not python_is_supported():
    raise RuntimeError(versions_required_message.format(version=sys.version))

# ------- setup extra_requires ------- #
extra_deps = {
    # Core library dependencies
    'eventstreams': ['sseclient!=0.0.23,!=0.0.24,>=0.0.18'],
    'isbn': ['python-stdnum'],
    'Graphviz': ['pydot>=1.2'],
    'Google': ['google>=1.7'],
    'mwparserfromhell': ['mwparserfromhell>=0.3.3'],
    'Tkinter': [
        'Pillow<7.0.0;python_version<"3"',
        'Pillow<6.0.0;python_version=="3.4"',
        'Pillow;python_version>="3.5"',
    ],
    'security': [
        'requests[security]'
        ';python_full_version=="2.7.7" or python_full_version=="2.7.8"',
        'pycparser!=2.14',
    ],
    'mwoauth': ['mwoauth!=0.3.1,>=0.2.4'],
    'html': ['BeautifulSoup4'],
    'http': ['fake_useragent'],
    'flake8': [  # Due to incompatibilities between packages the order matters.
        'flake8>=3.7.5',
        'pydocstyle<=3.0.0;python_version<"3"',
        'pydocstyle>=4.0.0;python_version>="3.4"',
        'hacking',
        'flake8-coding',
        'flake8-comprehensions',
        'flake8-docstrings>=1.3.1',
        'flake8-future-import',
        'flake8-mock>=0.3',
        'flake8-print>=2.0.1',
        'flake8-quotes>=2.0.1',
        'flake8-string-format',
        'flake8-tuple>=0.2.8',
        'flake8-no-u-prefixed-strings>=0.2',
        'pep8-naming>=0.7',
        'pyflakes>=2.1.0',
    ],
    # Additional core library dependencies which are only available on Python 2
    'csv': ['unicodecsv;python_version<"3"'],
}


# ------- setup extra_requires for scripts ------- #
script_deps = {
    'flickrripper.py': [
        'flickrapi',
        'Pillow<7.0.0;python_version<"3"',
        'Pillow<6.0.0;python_version=="3.4"',
        'Pillow;python_version>="3.5"',
    ],
    'states_redirect.py': ['pycountry'],
    'weblinkchecker.py': ['memento_client!=0.6.0,>=0.5.1'],
    'patrol.py': ['mwparserfromhell>=0.3.3'],
}
script_deps['data_ingestion.py'] = extra_deps['csv']

extra_deps.update(script_deps)

# ------- setup install_requires ------- #
dependencies = ['requests>=2.20.1,<2.22.0; python_version == "3.4"',
                'requests>=2.20.1; python_version != "3.4"',
                'enum34>=1.1.6; python_version < "3"']
# tools.ip does not have a hard dependency on an IP address module,
# as it falls back to using regexes if one is not available.
# The functional backport of py3 ipaddress is acceptable:
# https://pypi.org/project/ipaddress
# However the Debian package python-ipaddr is also supported:
# https://pypi.org/project/ipaddr
# Other backports are likely broken.
# ipaddr 2.1.10+ is distributed with Debian and Fedora. See T105443.
dependencies.append('ipaddr>=2.1.10;python_version<"3"')

# version.package_version() uses pathlib which is a python 3 library.
# pathlib2 is required for python 2.7
dependencies.append('pathlib2;python_version<"3"')

# Python versions before 2.7.9 will cause urllib3 to trigger
# InsecurePlatformWarning warnings for all HTTPS requests. By
# installing with security extras, requests will automatically set
# them up and the warnings will stop. See
# <https://urllib3.readthedocs.org/en/latest/security.html#insecureplatformwarning>
# for more details.
# There is no secure version of cryptography for Python 2.7.6 or older.
dependencies += extra_deps['security']


try:
    import bz2
except ImportError:
    # Use bz2file if the python is not compiled with bz2 support.
    dependencies.append('bz2file')
else:
    assert bz2


# ------- setup tests_require ------- #
test_deps = ['bz2file', 'mock']
# Some of the ui_tests depend on accessing the console window's menu
# to set the console font and copy and paste, achieved using pywinauto
# which depends on pywin32.
# These tests may be disabled because pywin32 depends on VC++, is time
# consuming to build, and the console window can't be accessed during appveyor
# builds.
# Microsoft makes available a compiler for Python 2.7
# http://www.microsoft.com/en-au/download/details.aspx?id=44266
if os.name == 'nt' and os.environ.get('PYSETUP_TEST_NO_UI', '0') != '1':
    test_deps += [
        'pywinauto>0.6.4;python_version>="3.5" or python_version<"3"',
        'pywinauto<=0.6.4;python_version=="3.4"',
        'pywin32>220;python_version>="3.5" or python_version<"3"',
        'pywin32<=220;python_version=="3.4"',
    ]

# Add all dependencies as test dependencies,
# so all scripts can be compiled for script_tests, etc.
if 'PYSETUP_TEST_EXTRAS' in os.environ:
    test_deps += [i for k, v in extra_deps.items() if k != 'flake8' for i in v]

    if 'requests[security]' in test_deps:
        # Bug T105767 on Python 2.7 release 9+
        if PY2 and PYTHON_VERSION[2] >= 9:
            test_deps.remove('requests[security]')

# These extra dependencies are needed other unittest fails to load tests.
test_deps += extra_deps['csv']
test_deps += extra_deps['eventstreams']
test_deps += ['six;python_version>="3"']


def get_version(name):
    """Get a valid pywikibot module version string."""
    version = '3.0'
    try:
        import subprocess
        date = subprocess.check_output(
            ['git', 'log', '-1', '--format=%ci']).strip()
        date = date.decode().split(' ')[0].replace('-', '')
        version += '.' + date
        if 'sdist' not in sys.argv:
            version += '.dev0'
    except Exception as e:
        print(e)
        from pkg_resources import get_distribution, DistributionNotFound
        try:
            version = get_distribution(name).version
        except DistributionNotFound as e:
            print(e)
            version += '.dev0'
    return version


def read_desc(filename):
    """Read long description.

    Combine included restructured text files which must be done before
    uploading because the source isn't available after creating the package.
    """
    desc = []
    with open(filename) as f:
        for line in f:
            if line.strip().startswith('.. include::'):
                include = os.path.relpath(line.rsplit('::')[1].strip())
                if os.path.exists(include):
                    with open(include) as g:
                        desc.append(g.read())
                else:
                    print('Cannot include {0}; file not found'.format(include))
            else:
                desc.append(line)
    return ''.join(desc)


name = 'pywikibot'
setup(
    name=name,
    version=get_version(name),
    description='Python MediaWiki Bot Framework',
    long_description=read_desc('README.rst'),
    keywords=['API', 'bot', 'framework', 'mediawiki', 'pwb', 'python',
              'pywikibot', 'pywikipedia', 'pywikipediabot', 'wiki',
              'wikimedia', 'wikipedia'],
    maintainer='The Pywikibot team',
    maintainer_email='pywikibot@lists.wikimedia.org',
    license='MIT License',
    packages=[str(name)] + [package
                            for package in find_packages()
                            if package.startswith('pywikibot.')],
    python_requires='>=2.7.4, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*',
    install_requires=dependencies,
    extras_require=extra_deps,
    url='https://www.mediawiki.org/wiki/Manual:Pywikibot',
    download_url='https://tools.wmflabs.org/pywikibot/',
    test_suite='tests.collector',
    tests_require=test_deps,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Wiki',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    use_2to3=False
)
