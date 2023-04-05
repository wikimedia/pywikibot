#!/usr/bin/env python3
"""Script to create a new distribution. Requires Python 3.7+.

The following options are supported:

-help      Print documentation of this file and of setup.py

-local     Install the distribution as a local site-package. If a
           Pywikibot package is already there, it will be uninstalled
           first. Clears old dist folders first.

-remote    Upload the package to pypi. This cannot be done if the
           Pywikibot version is a development release.  Clears old dist
           folders first.

-clear     Clear old dist folders and leave. Does not create a
           distribution.

-upgrade   Upgrade distribution packages pip, setuptools, wheel and
           twine first

Usage::

    [pwb] make_dist [options]

.. versionadded:: 7.3
.. versionchanged:: 7.4

   - updates pip, setuptools, wheel and twine packages first
   - installs pre-releases over stable versions
   - also creates built distribution together with source distribution
   - *-upgrade* option was added

.. versionchanged:: 7.5

   - *clear* option was added
   - *nodist* option was added

.. versionchanged:: 8.1
   Python 3.7+ required because *dataclasses* module is used.
   *nodist* option was removed, *clear* option does not create a
   distribution. *local* and *remote* option clears old distributions
   first.
"""
#
# (C) Pywikibot team, 2022-2023
#
# Distributed under the terms of the MIT license.
#
import abc
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from subprocess import check_call, run

import setup
from pywikibot import __version__, error, info, input_yn, warning
from pywikibot.backports import Tuple


@dataclass
class SetupBase(abc.ABC):

    """Setup distribution base class.

    .. versionadded:: 8.0
    .. versionchanged:: 8.1
       *dataclass* is used.
    """

    local: bool
    remote: bool
    clear: bool
    upgrade: bool
    folder: Path = field(init=False)

    def __post_init__(self) -> None:
        """Post-init initializer."""
        self.folder = Path().resolve()

    def clear_old_dist(self) -> None:  # pragma: no cover
        """Delete old dist folders.

        .. versionadded:: 7.5
        """
        info('Removing old dist folders... ', newline=False)
        shutil.rmtree(self.folder / 'build', ignore_errors=True)
        shutil.rmtree(self.folder / 'dist', ignore_errors=True)
        shutil.rmtree(self.folder / 'pywikibot.egg-info', ignore_errors=True)
        info('done')

    @abc.abstractmethod
    def copy_files(self) -> None:
        """Copy files."""

    @abc.abstractmethod
    def cleanup(self) -> None:
        """Cleanup copied files."""

    def run(self) -> None:  # pragma: no cover
        """Run the installer script."""
        if self.upgrade:
            check_call('python -m pip install --upgrade pip', shell=True)
            check_call(
                'pip install --upgrade setuptools wheel twine ', shell=True)

        if self.local or self.remote or self.clear:
            self.clear_old_dist()
            if self.clear:
                return

        self.copy_files()
        try:
            setup.main()  # create a new package
        except SystemExit as e:
            error(e)
            return
        finally:
            self.cleanup()

        # check description
        if run('twine check dist/*', shell=True).returncode:
            return

        if self.local:
            check_call('pip uninstall pywikibot -y', shell=True)
            check_call(
                'pip install --no-index --pre --find-links=dist pywikibot',
                shell=True)

        if self.remote and input_yn(
                '<<lightblue>>Upload dist to pypi', automatic_quit=False):
            check_call('twine upload dist/*', shell=True)


class SetupPywikibot(SetupBase):

    """Setup for Pywikibot distribution.

    .. versionadded:: 8.0
    """

    def __init__(self, *args) -> None:
        """Set source and target directories."""
        super().__init__(*args)
        source = self.folder / 'scripts' / 'i18n' / 'pywikibot'
        target = self.folder / 'pywikibot' / 'scripts' / 'i18n' / 'pywikibot'
        self.target = target
        self.source = source

    def copy_files(self) -> None:  # pragma: no cover
        """Copy i18n files to pywikibot.scripts folder.

        Pywikibot i18n files are used for some translations. They are copied
        to the pywikibot scripts folder.
        """
        info(f'directory is {self.folder}')
        info(f'clear {self.target} directory')
        shutil.rmtree(self.target, ignore_errors=True)
        info('copy i18n files ... ', newline=False)
        shutil.copytree(self.source, self.target)
        info('done')

    def cleanup(self) -> None:  # pragma: no cover
        """Remove all copied files from pywikibot scripts folder."""
        info('Remove copied files... ', newline=False)
        shutil.rmtree(self.target)
        # restore pywikibot en.json file
        filename = 'en.json'
        self.target.mkdir()
        shutil.copy(self.source / filename, self.target / filename)
        info('done')


def handle_args() -> Tuple[bool, bool, bool, bool, bool]:
    """Handle arguments and print documentation if requested.

    Read arguments from `sys.argv` and adjust it passing `sdist` to
    `setuptools.setup`.

    :return: Return whether dist is to be installed locally or to be
        uploaded
    """
    if '-help' in sys.argv:  # pragma: no cover
        info(__doc__)
        info(setup.__doc__)
        sys.exit()

    local = '-local' in sys.argv
    remote = '-remote' in sys.argv
    clear = '-clear' in sys.argv
    upgrade = '-upgrade' in sys.argv

    if remote and 'dev' in __version__:
        warning('Distribution must not be a developmental release to upload.')
        remote = False

    sys.argv = [sys.argv[0], 'sdist', 'bdist_wheel']
    return local, remote, clear, upgrade


def main() -> None:  # pragma: no cover
    """Script entry point."""
    args = handle_args()
    SetupPywikibot(*args).run()


if __name__ == '__main__':  # pragma: no cover
    main()
