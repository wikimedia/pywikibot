# -*- coding: utf-8 -*-
"""Installer script for Pywikibot framework.

To create a new distribution:
-----------------------------

- replace the developmental version string in ``pywikibot.__metadata__.py``
  by the corresponing final release
- create the package with::

    python setup.py sdist

- push the change to gerrit and merge it to the repository
- upload the package to pypy by::

    twine upload dist/*

- create a new tag with the version number of the final release
- synchronize the local tags with the remote repositoy
- merge current master branch to stable branch
- push new stable branch to gerrit and merge it the stable repository
- prepare the next master release by increasing the version number in
  ``pywikibot.__metadata__.py`` and adding developmental identifier
- upload this patchset to gerrit and merge it.
"""
#
# (C) Pywikibot team, 2009-2021
#
# Distributed under the terms of the MIT license.
#
# ## KEEP PYTHON 2 SUPPORT FOR THIS SCRIPT ## #
import os
import sys

from pkg_resources import parse_version, safe_version
from setuptools import setup


PYTHON_VERSION = sys.version_info[:3]

VERSIONS_REQUIRED_MESSAGE = """
Pywikibot is not available on:
{version}

This version of Pywikibot only supports Python 3.5+.
"""


def python_is_supported():
    """Check that Python is supported."""
    return PYTHON_VERSION >= (3, 5, 0)


if not python_is_supported():  # pragma: no cover
    # pwb.py checks this exception
    raise RuntimeError(VERSIONS_REQUIRED_MESSAGE.format(version=sys.version))

# ------- setup extra_requires ------- #
extra_deps = {
    # Core library dependencies
    'eventstreams': ['sseclient!=0.0.23,!=0.0.24,>=0.0.18'],
    'isbn': ['python-stdnum>=1.16'],
    'Graphviz': ['pydot>=1.2'],
    'Google': ['google>=1.7'],
    'mwparserfromhell': ['mwparserfromhell>=0.5.0'],
    'wikitextparser': ['wikitextparser>=0.47.5;python_version<"3.6"',
                       'wikitextparser>=0.47.0'],
    'Tkinter': [  # vulnerability found in Pillow<8.1.1
        'Pillow>=8.1.1;python_version>="3.6"',
    ],
    'mwoauth': ['mwoauth!=0.3.1,>=0.2.4'],
    'html': ['BeautifulSoup4'],
    'http': ['fake_useragent'],
    'flake8': [  # Due to incompatibilities between packages the order matters.
        'flake8>=3.7.5',
        'pydocstyle>=4.0.0',
        'hacking',
        'flake8-bugbear!=21.4.1',
        'flake8-coding',
        'flake8-colors>=0.1.9',
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
    'commons_information.py': extra_deps['mwparserfromhell'],
    'patrol.py': extra_deps['mwparserfromhell'],
    'weblinkchecker.py': ['memento_client!=0.6.0,>=0.5.1'],
}

extra_deps.update(script_deps)
extra_deps.update({'scripts': [i for k, v in script_deps.items() for i in v]})

# ------- setup install_requires ------- #
# packages which are mandatory
dependencies = [
    'requests>=2.20.1,<2.26.0;python_version<"3.6"',
    'requests>=2.20.1;python_version>="3.6"',
    # PEP 440
    'setuptools>=20.2, !=50.0.0, <50.2.0 ; python_version < "3.6"',
    'setuptools>=20.2 ; python_version >= "3.6"',
]
# in addition either mwparserfromhell or wikitextparser is required

# ------- setup tests_require ------- #
test_deps = ['mock']

# Add all dependencies as test dependencies,
# so all scripts can be compiled for script_tests, etc.
if 'PYSETUP_TEST_EXTRAS' in os.environ:  # pragma: no cover
    test_deps += [i for k, v in extra_deps.items() if k != 'flake8' for i in v]

# These extra dependencies are needed other unittest fails to load tests.
test_deps += extra_deps['eventstreams']


class _DottedDict(dict):
    __getattr__ = dict.__getitem__


# import metadata
metadata = _DottedDict()
name = 'pywikibot'
path = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(path, name, '__metadata__.py')) as f:
    exec(f.read(), metadata)
assert metadata.__name__ == name


def get_validated_version():  # pragma: no cover
    """Get a validated pywikibot module version string.

    The version number from pywikibot.__metadata__.__version__ is used.
    setup.py with 'sdist' option is used to create a new source distribution.
    In that case the version number is validated: Read tags from git.
    Verify that the new release is higher than the last repository tag
    and is not a developmental release.

    :return: pywikibot module version string
    :rtype: str
    """
    version = metadata.__version__
    if 'sdist' not in sys.argv:
        return version

    # validate version for sdist
    from contextlib import suppress
    from subprocess import PIPE, run
    try:
        tags = run(['git', 'tag'], check=True, stdout=PIPE,
                   universal_newlines=True).stdout.splitlines()
    except Exception as e:
        print(e)
        sys.exit('Creating source distribution canceled.')

    for tag in ('stable', 'python2'):
        with suppress(ValueError):
            tags.remove(tag)

    last_tag = tags[-1]

    warnings = []
    if 'dev' in version:
        warnings.append('Distribution must not be a developmental release.')

    if parse_version(version) < parse_version('0'):
        # any version which is not a valid PEP 440 version will be considered
        # less than any valid PEP 440 version
        warnings.append(
            version + ' is not a valid version string following PEP 440.')
    elif safe_version(version) != version:
        warnings.append(
            '{} does not follow PEP 440. Use {} as version string instead.'
            .format(version, safe_version(version)))

    if parse_version(version) <= parse_version(last_tag):
        warnings.append(
            'New version "{}" is not higher than last version "{}".'
            .format(version, last_tag))

    if warnings:
        print(__doc__)
        print('\n\n'.join(warnings))
        sys.exit('\nBuild of distribution package canceled.')

    return version


def read_desc(filename):  # pragma: no cover
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
                    print('Cannot include {}; file not found'.format(include))
            else:
                desc.append(line)
    return ''.join(desc)


def get_packages(name):  # pragma: no cover
    """Find framework packages."""
    try:
        from setuptools import find_namespace_packages
    except ImportError:
        sys.exit(
            'setuptools >= 40.1.0 is required to create a new distribution.')
    packages = find_namespace_packages(include=[name + '.*'])
    return [str(name)] + packages


def main():
    """Setup entry point."""
    version = get_validated_version()
    setup(
        name=metadata.__name__,
        version=version,
        description=metadata.__description__,
        long_description=read_desc('README.rst'),
        keywords=metadata.__keywords__.split(),
        maintainer=metadata.__maintainer__,
        maintainer_email=metadata.__maintainer_email__,
        license=metadata.__license__,
        packages=get_packages(name),
        python_requires='>=3.5.0',
        install_requires=dependencies,
        extras_require=extra_deps,
        url=metadata.__url__,
        download_url=metadata.__download_url__,
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
            'Programming Language :: Python :: 3 :: Only',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: 3.7',
            'Programming Language :: Python :: 3.8',
            'Programming Language :: Python :: 3.9',
            'Programming Language :: Python :: 3.10',
            'Programming Language :: Python :: Implementation :: CPython',
            'Topic :: Internet :: WWW/HTTP :: Dynamic Content :: Wiki',
            'Topic :: Software Development :: Libraries :: Python Modules',
            'Topic :: Utilities',
        ],
        use_2to3=False
    )

    # Finally show distribution version before uploading
    if 'sdist' in sys.argv:
        print('\nDistribution package created for version {}'.format(version))


if __name__ == '__main__':  # pragma: no cover
    main()
