# -*- coding: utf-8 -*-
"""Installer script for Pywikibot framework."""
#
# (C) Pywikibot team, 2009-2020
#
# Distributed under the terms of the MIT license.
#
import os
import sys

from setuptools import setup

PYTHON_VERSION = sys.version_info[:3]

versions_required_message = """
Pywikibot is not available on:
{version}

This version of Pywikibot only supports Python 3.5+.
"""


def python_is_supported():
    """Check that Python is supported."""
    # Any change to this must be copied to pwb.py
    return PYTHON_VERSION >= (3, 5, 0)


if not python_is_supported():
    raise RuntimeError(versions_required_message.format(version=sys.version))

# ------- setup extra_requires ------- #
extra_deps = {
    # Core library dependencies
    'eventstreams': ['sseclient!=0.0.23,!=0.0.24,>=0.0.18'],
    'isbn': ['python-stdnum>=1.13'],
    'Graphviz': ['pydot>=1.2'],
    'Google': ['google>=1.7'],
    'mwparserfromhell': ['mwparserfromhell>=0.3.3'],
    'Tkinter': [  # vulnerability found in Pillow<6.2.2
        'Pillow>=6.2.2',
    ],
    'mwoauth': ['mwoauth!=0.3.1,>=0.2.4'],
    'html': ['BeautifulSoup4'],
    'http': ['fake_useragent'],
    'flake8': [  # Due to incompatibilities between packages the order matters.
        'flake8>=3.7.5',
        'pydocstyle>=4.0.0',
        'hacking',
        'flake8-coding',
        'flake8-comprehensions>=3.1.4;python_version>="3.8"',
        'flake8-comprehensions>=2.2.0',
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
}


# ------- setup extra_requires for scripts ------- #
script_deps = {
    'flickrripper.py': [
        'flickrapi>=2.2',
    ] + extra_deps['Tkinter'],
    'imageharvest.py': extra_deps['html'],
    'isbn.py': extra_deps['isbn'],
    'match_images.py': extra_deps['Tkinter'],
    'patrol.py': extra_deps['mwparserfromhell'],
    'states_redirect.py': ['pycountry'],
    'weblinkchecker.py': ['memento_client!=0.6.0,>=0.5.1'],
}

extra_deps.update(script_deps)
extra_deps.update({'scripts': [i for k, v in script_deps.items() for i in v]})

# ------- setup install_requires ------- #
# packages which are mandatory
dependencies = ['requests>=2.20.1']

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
if os.name == 'nt' and os.environ.get('PYSETUP_TEST_NO_UI', '0') != '1':
    test_deps += [
        'pywinauto>0.6.4',
        'pywin32>220',
    ]

# Add all dependencies as test dependencies,
# so all scripts can be compiled for script_tests, etc.
if 'PYSETUP_TEST_EXTRAS' in os.environ:
    test_deps += [i for k, v in extra_deps.items() if k != 'flake8' for i in v]

# These extra dependencies are needed other unittest fails to load tests.
test_deps += extra_deps['eventstreams']
test_deps += ['six']


def get_version(name):
    """Get a valid pywikibot module version string.

    Either create a timebased version number for the package
    or read the version number from the package.

    @return: pywikibot module version string
    @rtype: str
    """
    version = '4.0'
    try:
        import subprocess
        date = subprocess.check_output(
            ['git', 'log', '-1', '--format=%ci']).strip()
        date = date.decode().split(' ', 1)[0].replace('-', '')
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


def get_packages(name):
    """Find framework packages."""
    from setuptools import find_namespace_packages
    packages = find_namespace_packages(include=[name + '.*'])
    return [str(name)] + packages


def main():
    """Setup entry point."""
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
        packages=get_packages(name),
        python_requires='>=3.5.0',
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
            'Programming Language :: Python :: 3',
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


if __name__ == '__main__':
    main()
