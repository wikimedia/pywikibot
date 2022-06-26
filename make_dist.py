#!/usr/bin/python3
"""Script to create a new distribution.

The following options are supported:

-help    Print documentation of this file and of setup.py

-local   Install the distribution as a local site-package. If a
         Pywikibot package is already there, it will be uninstalled
         first.

-remote  Upload the package to pypi. This cannot be done if the
         Pywikibot version is a development release.

-upgrade Upgrade distribution packages pip, setuptools, wheel and twine
         first

Usage::

    [pwb] make_dist [options]

.. note:: Requires Python 3.6+.
.. versionadded:: 7.3
.. versionchanged:: 7.4

   - updates pip, setuptools, wheel and twine packages first
   - installs pre-releases over stable versions
   - also creates built distribution together with source distribution
   - `-upgrade` option was added
"""
#
# (C) Pywikibot team, 2022
#
# Distributed under the terms of the MIT license.
#
import shutil
import subprocess
import sys
from pathlib import Path

from pywikibot import __version__, error, info, input_yn, warning
from pywikibot.backports import Tuple
import setup


def copy_files() -> None:
    """Copy code entry point and i18n files to pywikibot.scripts folder.

    pwb.py wrapper script is a console script entry point for the
    site-package. pywikibot i18n files are used for some translations.
    They are copied to the pywikibot scripts folder.
    """
    folder = Path().resolve()
    info(f'directory is {folder}')

    # copy script entry points to pywikibot\scripts
    target = folder / 'pywikibot' / 'scripts'
    filename = 'pwb.py'
    info(f'copy script entry point {filename!r} to {target}... ',
         newline=False)
    shutil.copy(folder / filename, target / filename)
    info('done')

    target = target / 'i18n' / 'pywikibot'
    info(f'copy i18n files to {target} ... ', newline=False)
    target.parent.mkdir()
    filename = '__init__.py'
    shutil.copy(folder / 'scripts' / 'i18n' / filename,
                target.parent / filename)
    shutil.copytree(folder / 'scripts' / 'i18n' / 'pywikibot', target)
    info('done')


def cleanup() -> None:
    """Remove all files which were copied to the pywikibot scripts folder."""
    info('Remove copied files... ', newline=False)
    folder = Path().resolve()
    target = folder / 'pywikibot' / 'scripts' / 'i18n'
    shutil.rmtree(target)
    target = target.parent / 'pwb.py'
    target.unlink()
    info('done')


def handle_args() -> Tuple[bool, bool]:
    """Handle arguments and print documentation if requested.

    Read arguments from `sys.argv` and adjust it passing `sdist` to
    `setuptools.setup`.

    :return: Return whether dist is to be installed locally or to be
        uploaded
    """
    if '-help' in sys.argv:
        info(__doc__)
        info(setup.__doc__)
        sys.exit()

    local = '-local' in sys.argv
    remote = '-remote' in sys.argv
    upgrade = '-upgrade' in sys.argv

    if remote and 'dev' in __version__:
        warning('Distribution must not be a developmental release to upload.')
        remote = False

    sys.argv = [sys.argv[0], 'sdist', 'bdist_wheel']
    return local, remote, upgrade


def main() -> None:
    """Script entry point."""
    local, remote, upgrade = handle_args()

    copy_files()
    if upgrade:
        subprocess.run('python -m pip install --upgrade pip')
        subprocess.run('pip install --upgrade setuptools wheel twine ')

    try:
        setup.main()  # create a new package
    except SystemExit as e:
        error(e)
        return
    finally:
        cleanup()

    if local:
        subprocess.run('pip uninstall pywikibot -y')
        subprocess.run(
            'pip install --no-index --pre --find-links=dist pywikibot')

    if remote and input_yn(
            '<<lightblue>>Upload dist to pypi', automatic_quit=False):
        subprocess.run('twine upload dist/*')


if __name__ == '__main__':
    main()
