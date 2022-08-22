#!/usr/bin/python3
"""Script to create a new distribution.

The following options are supported:

-help    Print documentation of this file and of setup.py

-local   Install the distribution as a local site-package. If a
         Pywikibot package is already there, it will be uninstalled
         first.

-remote  Upload the package to pypi. This cannot be done if the
         Pywikibot version is a development release.

-clear   Clear old dist folders

-upgrade Upgrade distribution packages pip, setuptools, wheel and twine
         first

-nodist  Do not create a distribution. Useful to -clear or -upgrade only.

Usage::

    [pwb] make_dist [options]

.. note:: Requires Python 3.6+.
.. versionadded:: 7.3
.. versionchanged:: 7.4

   - updates pip, setuptools, wheel and twine packages first
   - installs pre-releases over stable versions
   - also creates built distribution together with source distribution
   - `-upgrade` option was added

.. versionchanged:: 7.5

   - `clear` option was added
   - `nodist` option was added
"""
#
# (C) Pywikibot team, 2022
#
# Distributed under the terms of the MIT license.
#
import shutil
import sys
from subprocess import check_call
from pathlib import Path

from pywikibot import __version__, error, info, input_yn, warning
from pywikibot.backports import Tuple
import setup


def clear_old_dist() -> None:
    """Delete old dist folders.

    .. versionadded:: 7.5
    """
    info('Removing old dist folders... ', newline=False)
    folder = Path().resolve()
    shutil.rmtree(folder / 'build', ignore_errors=True)
    shutil.rmtree(folder / 'dist', ignore_errors=True)
    shutil.rmtree(folder / 'pywikibot.egg-info', ignore_errors=True)
    info('done')


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
    clear = '-clear' in sys.argv
    upgrade = '-upgrade' in sys.argv
    nodist = '-nodist' in sys.argv

    if nodist:
        local, remote = False, False

    if remote and 'dev' in __version__:
        warning('Distribution must not be a developmental release to upload.')
        remote = False

    sys.argv = [sys.argv[0], 'sdist', 'bdist_wheel']
    return local, remote, clear, upgrade, nodist


def main() -> None:
    """Script entry point."""
    local, remote, clear, upgrade, nodist = handle_args()

    if upgrade:
        check_call('python -m pip install --upgrade pip', shell=True)
        check_call('pip install --upgrade setuptools wheel twine ', shell=True)

    if clear:
        clear_old_dist()

    if nodist:
        return

    copy_files()
    try:
        setup.main()  # create a new package
    except SystemExit as e:
        error(e)
        return
    finally:
        cleanup()

    if local:
        check_call('pip uninstall pywikibot -y', shell=True)
        check_call('pip install --no-index --pre --find-links=dist pywikibot',
                   shell=True)

    if remote and input_yn(
            '<<lightblue>>Upload dist to pypi', automatic_quit=False):
        check_call('twine upload dist/*', shell=True)


if __name__ == '__main__':
    main()
