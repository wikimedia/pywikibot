#!/usr/bin/env python3
"""Installer script for Pywikibot framework.

**How to create a new distribution:**

- replace the developmental version string in ``pywikibot.__metadata__.py``
  by the corresponding final release
- create the package with::

    make_dist -remote

- create a new tag with the version number of the final release
- synchronize the local tags with the remote repositoy
- merge current master branch to stable branch
- push new stable branch to Gerrit and merge it the stable repository
- prepare the next master release by increasing the version number in
  ``pywikibot.__metadata__.py`` and adding developmental identifier
- upload this patchset to Gerrit and merge it.

.. warning:: do not upload a development release to pypi.
"""
#
# (C) Pywikibot team, 2009-2026
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import configparser
import os
import re
import sys
from contextlib import suppress
from pathlib import Path


# ------- setup extra_requires ------- #
extra_deps = {
    # Core library dependencies
    'eventstreams': ['requests-sse>=0.5.2'],
    'isbn': ['python-stdnum>=2.2'],
    'Graphviz': ['pydot>=4.0.1'],
    'Google': ['googlesearch-python >= 1.3.0'],
    'memento': ['memento_client==0.6.1'],
    'wikitextparser': ['wikitextparser>=0.56.4'],
    'mysql': ['PyMySQL >= 1.1.2'],
    # Pillow cannot be installed with GraalPy
    'Tkinter': [
        'Pillow==10.4.0; platform_python_implementation == "PyPy" '
        'and python_version == "3.9"',
        'Pillow==11.3.0; platform_python_implementation == "PyPy" '
        'and python_version == "3.10"',
        'Pillow==12.1.0; platform_python_implementation == "PyPy" '
        'and python_version >= "3.11"',
        'Pillow==11.3.0; platform_python_implementation == "CPython" '
        'and python_version == "3.9"',
        'Pillow>=12.1.0; platform_python_implementation == "CPython" '
        'and  python_version >= "3.10"',
    ],
    'mwoauth': [
        'PyJWT != 2.10.0, != 2.10.1',  # T380270
        'mwoauth>=0.4.0',
    ],
    'html': ['beautifulsoup4>=4.14.3'],
    'http': [
        'fake-useragent >= 2.2.0',
    ],
}


# ------- setup extra_requires for scripts ------- #
script_deps = {
    'weblinkchecker.py': extra_deps['memento'],
}

extra_deps.update(script_deps)
extra_deps.update({'scripts': [i for k, v in script_deps.items() for i in v]})

# ------- setup install_requires ------- #
# packages which are mandatory
dependencies = [
    'mwparserfromhell>=0.7.2',
    'packaging>=25.0',
    'requests>=2.32.3',
]


class _DottedDict(dict):
    __getattr__ = dict.__getitem__


path = Path(__file__).parent


def read_project() -> str:
    """Read the project name from toml file.

    ``tomllib`` was introduced with Python 3.11. To support earlier versions
    ``configparser`` is used. Therefore the tomlfile must be readable as
    config file until the first comment.

    .. versionadded:: 9.0
    """
    if sys.version_info >= (3, 11):
        import tomllib
        with open(path / 'pyproject.toml', 'rb') as f:
            data = tomllib.load(f)
        return data['project']['name']

    toml = []
    with open(path / 'pyproject.toml') as f:
        for line in f:
            if line.startswith('#'):
                break
            toml.append(line)

    config = configparser.ConfigParser()
    config.read_string(''.join(toml))
    return config['project']['name'].strip('"')


def get_validated_version(name: str) -> str:  # pragma: no cover
    """Get a validated pywikibot module version string.

    The version number from pywikibot.__metadata__.__version__ is used.
    setup.py with 'sdist' option is used to create a new source distribution.
    In that case the version number is validated: Read tags from git.
    Verify that the new release is higher than the last repository tag
    and is not a developmental release.

    :return: pywikibot module version string
    """
    # import metadata
    metadata = _DottedDict()
    with open(path / name / '__metadata__.py') as f:
        exec(f.read(), None, metadata)
    assert metadata.__url__.endswith(
        name.title())  # type: ignore[attr-defined]

    version = metadata.__version__  # type: ignore[attr-defined]
    if 'sdist' not in sys.argv:
        return version

    # validate version for sdist
    from subprocess import PIPE, run

    from packaging.version import InvalidVersion, Version

    try:
        tags = run(['git', 'tag'], check=True, stdout=PIPE,
                   text=True).stdout.splitlines()
    except Exception as e:
        print(e)
        sys.exit('Creating source distribution canceled.')

    last_tag = None
    if tags:
        for tag in ('stable', 'python2'):
            with suppress(ValueError):
                tags.remove(tag)

        last_tag = tags[-1]

    warning = ''
    try:
        vrsn = Version(version)
    except InvalidVersion:
        warning = f'{version} is not a valid version string following PEP 440.'
    else:
        if last_tag and vrsn <= Version(last_tag):
            warning = (
                f'New version {version!r} is not higher than last version '
                f'{last_tag!r}.'
            )

    if warning:
        print(__doc__)
        print(f'\n\n{warning}')
        sys.exit('\nBuild of distribution package canceled.')

    return version


def read_desc(filename) -> str:
    """Read long description.

    Combine included restructured text files which must be done before
    uploading because the source isn't available after creating the
    package.
    """
    pattern = r'(?:\:\w+\:`([^`]+?)(?:<.+>)?` *)', r'\1'
    desc = []
    with open(filename) as f:
        for line in f:
            if line.strip().startswith('.. include::'):
                include = os.path.relpath(line.rsplit('::')[1].strip())
                if os.path.exists(include):
                    with open(include) as g:
                        desc.append(re.sub(pattern[0], pattern[1], g.read()))
                else:  # pragma: no cover
                    print(f'Cannot include {include}; file not found')
            else:
                desc.append(re.sub(pattern[0], pattern[1], line))
    return ''.join(desc)


def get_packages(name: str) -> list[str]:
    """Find framework packages."""
    try:
        from setuptools import find_namespace_packages
    except ImportError:
        sys.exit(
            'setuptools >= 40.1.0 is required to create a new distribution.')
    packages = find_namespace_packages(include=[name + '.*'])
    for cache_variant in ('', '-py3'):
        with suppress(ValueError):
            packages.remove(f'{name}.apicache{cache_variant}')
    return [str(name)] + packages


def main() -> None:  # pragma: no cover
    """Setup entry point."""
    from setuptools import setup

    name = read_project()
    setup(
        version=get_validated_version(name),
        long_description=read_desc('README.rst'),
        long_description_content_type='text/x-rst',
        packages=get_packages(name),
        include_package_data=True,
        install_requires=dependencies,
        extras_require=extra_deps,
    )


if __name__ == '__main__':
    main()
