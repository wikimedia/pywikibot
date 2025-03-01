#!/usr/bin/env python3
"""Wrapper script to invoke pywikibot-based scripts.

This wrapper script invokes script by its name in this search order:

1. Scripts listed in `user_script_paths` list inside your user config
   settings file (usually `user-config.py`) in the given order. Refer
   :ref:`External Script Path Settings`.
2. User scripts residing in `scripts/userscripts` (directory mode only).
3. Scripts residing in `scripts` folder (directory mode only).
4. Maintenance scripts residing in `scripts/maintenance` (directory mode only).
5. Site-package scripts (site-package only)
6. Framework scripts residing in `pywikibot/scripts`.

This wrapper script is able to invoke scripts even if the script name is
misspelled. In directory mode it also checks package dependencies.

Run scripts with pywikibot in directory mode using::

    python pwb.py <pwb options> <name_of_script> <options>

or run scripts with pywikibot installed as a site package using::

    pwb <pwb options> <name_of_script> <options>

This wrapper script uses the package directory to store all user files,
will fix up search paths so the package does not need to be installed, etc.

Currently, `<pwb options>` are :ref:`global options`. This can be used
for tests to set the default site (see :phab:`T216825`)::

    python pwb.py -lang:de bot_tests -v

.. seealso:: :mod:`pwb` entry point
.. versionchanged:: 7.0
   pwb wrapper was added to the Python site package lib.
.. versionchanged:: 7.7
   pwb wrapper is able to set ``PYWIKIBOT_TEST_...`` environment variables,
   see :ref:`Environment variables`.
.. versionchanged:: 8.0
   renamed to wrapper.py.
.. versionchanged:: 9.4
   enable external scripts via entry points.
"""
#
# (C) Pywikibot team, 2012-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import importlib.metadata
import os
import sys
import types
from difflib import get_close_matches
from importlib import import_module
from pathlib import Path
from time import sleep
from warnings import warn


pwb = None
site_package = False


def check_pwb_versions(package: str):
    """Validate package version and scripts version.

    Rules:
        - Pywikibot version must not be older than scrips version
        - Scripts version must not be older than previous Pywikibot version
          due to deprecation policy
    """
    from packaging.version import Version

    scripts_version = Version(getattr(package, '__version__', pwb.__version__))
    wikibot_version = Version(pwb.__version__)

    if scripts_version.release > wikibot_version.release:  # pragma: no cover
        print(f'WARNING: Pywikibot version {wikibot_version} is behind '
              f'scripts package version {scripts_version}.\n'
              'Your Pywikibot may need an update or be misconfigured.\n')

    # calculate previous minor release
    if wikibot_version.minor > 0:  # pragma: no cover
        prev_wikibot = Version(
            f'{wikibot_version.major}.{wikibot_version.minor - 1}.'
            f'{wikibot_version.micro}'
        )

        if scripts_version.release < prev_wikibot.release:
            print(f'WARNING: Scripts package version {scripts_version} is '
                  f'behind legacy Pywikibot version {prev_wikibot} and '
                  f'current version {wikibot_version}\n'
                  'Your scripts may need an update or be misconfigured.\n')
    elif scripts_version.release < wikibot_version.release:  # pragma: no cover
        print(f'WARNING: Scripts package version {scripts_version} is behind '
              f'current version {wikibot_version}\n'
              'Your scripts may need an update or be misconfigured.\n')

    del Version


# The following snippet was developed by Ned Batchelder (and others)
# for coverage [1], with Python 3 support [2] added later,
# and is available under the BSD license (see [3])
# [1]
# https://bitbucket.org/ned/coveragepy/src/b5abcee50dbe/coverage/execfile.py
# [2]
# https://bitbucket.org/ned/coveragepy/src/fd5363090034/coverage/execfile.py
# [3]
# https://bitbucket.org/ned/coveragepy/src/2c5fb3a8b81c/setup.py?at=default#cl-31


def run_python_file(filename: str, args: list[str], package=None):
    """Run a python file as if it were the main program on the command line.

    .. versionchanged:: 7.7
       Set and restore ``PYWIKIBOT_TEST_...`` environment variables.

    :param filename: The path to the file to execute, it need not be a
        .py file.
    :param args: is the argument list to present as sys.argv, as strings.
    :param package: The package of the script. Used for checks.
    :type package: Optional[module]
    """
    # Create a module to serve as __main__
    old_main_mod = sys.modules['__main__']
    main_mod = types.ModuleType('__main__')
    sys.modules['__main__'] = main_mod
    main_mod.__file__ = filename
    main_mod.__builtins__ = sys.modules['builtins']
    if package:
        main_mod.__package__ = package.__name__
        check_pwb_versions(package)

    # Set sys.argv and the first path element properly.
    old_argv = sys.argv
    old_argvu = pwb.argvu

    # set environment values
    old_env = os.environ.copy()
    for key, value in environ:  # pragma: no cover
        os.environ[key] = value

    sys.argv = [filename, *args]
    pwb.argvu = [Path(filename).stem, *args]
    sys.path.insert(0, os.path.dirname(filename))

    try:
        with open(filename, 'rb') as f:
            source = f.read()
        exec(compile(source, filename, 'exec', dont_inherit=True),
             main_mod.__dict__)
    finally:
        # Restore the old __main__
        sys.modules['__main__'] = old_main_mod

        # Restore the old argv and path
        sys.argv = old_argv
        sys.path.pop(0)
        pwb.argvu = old_argvu

# end of snippet from coverage

        # Restore environment values
        for key, value in environ:  # pragma: no cover
            if key in old_env:
                os.environ[key] = old_env[key]
            else:
                del os.environ[key]


def handle_args(
    _,
    *args: str,
) -> tuple[str, list[str], list[str], list[str]]:
    """Handle args and get filename.

    .. versionchanged:: 7.7
       Catch ``PYWIKIBOT_TEST_...`` environment variables.

    :return: filename, script args, local pwb args, environment variables
    """
    fname = None
    local = []
    env = []
    for index, arg in enumerate(args, start=1):
        if arg in ('-version', '--version'):
            fname = 'version.py'
        elif arg in ('pwb', 'pwb.py', 'wrapper', 'wrapper.py'):
            pass
        elif arg.startswith('-'):
            local.append(arg)
        elif arg.startswith('PYWIKIBOT_TEST_'):
            var, _, val = arg.partition('=')
            env.append((var, val or '1'))
        else:
            fname = arg
            if not fname.endswith('.py'):
                fname += '.py'
        if fname:
            break
    else:
        index = 0

    return fname, list(args[index:]), local, env


def _print_requirements(requirements, script, variant):  # pragma: no cover
    """Print pip command to install requirements."""
    if not requirements:
        return

    if len(requirements) > 1:
        format_string = '\nPackages necessary for {} are {}.'
    else:
        format_string = '\nA package necessary for {} is {}.'
    print(format_string.format(script or 'pywikibot', variant))
    print('Please update required module{} with:\n\n'
          .format('s' if len(requirements) > 1 else ''))

    for requirement in requirements:
        print(f"    pip install \"{str(requirement).partition(';')[0]}\"\n")


def check_modules(script: str | None = None) -> bool:
    """Check whether mandatory modules are present.

    This also checks Python version when importing dependencies from setup.py

    :param script: The script name to be checked for dependencies
    :return: True if all dependencies are installed
    :raise RuntimeError: wrong Python version found in setup.py
    """
    from packaging.requirements import Requirement

    from setup import script_deps

    missing_requirements = []
    version_conflicts = []

    if script:
        dependencies = script_deps.get(Path(script).name, [])
    else:
        from setup import dependencies

    for dependency in dependencies:
        if dependency.startswith('packaging'):
            # Ignore these dependencies because ImportError is raised in an
            # early state when they are imported in backports. They are already
            # used at this point. This is a workaround for toolforge where some
            # modules are not installed as a site-package.
            # TODO: Check imports from external source
            continue

        requirement = Requirement(dependency)
        if requirement.marker is None or requirement.marker.evaluate():
            try:
                instlld_vrsn = importlib.metadata.version(requirement.name)
            except importlib.metadata.PackageNotFoundError as e:
                missing_requirements.append(requirement)
                print(e)
            else:
                if instlld_vrsn not in requirement.specifier:
                    version_conflicts.append(requirement)
                    print(
                        f'{requirement.name} version {instlld_vrsn} is '
                        f'installed but {requirement.specifier} is required'
                    )

    del Requirement
    del script_deps

    _print_requirements(missing_requirements, script, 'missing')
    _print_requirements(version_conflicts, script, 'outdated')

    if version_conflicts and not missing_requirements:  # pragma: no cover
        print('\nYou may continue on your own risk; type CTRL-C to stop.')
        try:
            sleep(5)
        except KeyboardInterrupt:
            return False

    return not missing_requirements


filename, script_args, global_args, environ = handle_args(*sys.argv)

# Search for user config file (user-config.py) before creating one.
# If successful, user config file already exists in one of the candidate
# directories. See config.py for details on search order.
# Use env var to communicate to config.py pwb.py location (bug T74918).
wrapper_dir = Path(__file__).parent
os.environ['PYWIKIBOT_DIR_PWB'] = str(wrapper_dir)

try:
    import pywikibot as pwb
except RuntimeError as e:  # pragma: no cover
    os.environ['PYWIKIBOT_NO_USER_CONFIG'] = '2'
    import pywikibot as pwb

    # user config file to be created
    if filename is not None and not (filename.startswith('generate_')
                                     or filename == 'version.py'):
        from pywikibot.config import user_config_file
        if user_config_file != 'user-config.py':
            # do not create a user config file if name is not default
            sys.exit(e)

        print('NOTE: user-config.py was not found!')
        print('Please follow the prompts to create it:')
        run_python_file(
            str(wrapper_dir.joinpath('generate_user_files.py')), [])
        # because we have loaded pywikibot without user-config.py loaded,
        # we need to re-start the entire process. Ask the user to do so.
        print('Now, you have to re-execute the command to start your script.')
        sys.exit(1)
except ModuleNotFoundError as module:  # raised in textlib or backports
    print(f'\n{module.msg}\nPlease install it with\n\n'
          f'    pip install {module.name}')
    sys.exit()


def find_alternates(filename, script_paths):
    """Search for similar filenames in the given script paths."""
    from pywikibot import config, error, info, input_choice, warning
    from pywikibot.bot import QuitKeyboardInterrupt, ShowingListOption

    assert config.pwb_close_matches > 0, \
        'config.pwb_close_matches must be greater than 0'
    assert 0.0 < config.pwb_cut_off < 1.0, \
        'config.pwb_cut_off must be a float in range [0, 1]'

    error(f'{filename} not found! Misspelling?')

    scripts = {}

    for folder in script_paths:
        if not folder.exists():  # pragma: no cover
            warning(
                f'{folder} does not exists; remove it from user_script_paths')
            continue
        for script_name in folder.iterdir():
            name, suffix = script_name.stem, script_name.suffix
            if suffix == '.py' and not name.startswith('__'):
                scripts[name] = script_name

    # remove .py for better matching
    filename = filename[:-3]
    similar_scripts = get_close_matches(filename, scripts,
                                        config.pwb_close_matches,
                                        config.pwb_cut_off)
    if not similar_scripts:
        return None

    if len(similar_scripts) == 1:
        script = similar_scripts[0]
        wait_time = config.pwb_autostart_waittime
        info('NOTE: Starting the most similar script '
             f'<<lightyellow>>{script}.py<<default>>\n'
             f'      in {wait_time} seconds; type CTRL-C to stop.')
        try:
            sleep(wait_time)  # Wait a bit to let it be cancelled
        except KeyboardInterrupt:
            return None
    else:
        msg = '\nThe most similar scripts are:'
        alternatives = ShowingListOption(similar_scripts, pre=msg, post='')
        try:
            _, script = input_choice('Which script to be run:',
                                     alternatives, default='1')
        except QuitKeyboardInterrupt:
            return None
        print()  # pragma: no cover
    return str(scripts[script])


def find_filename(filename):
    """Search for the filename in the given script paths.

    .. versionchanged:: 7.0
       Search users_scripts_paths in config.base_dir
    .. versionchanged:: 9.0
       Add config.base_dir to search path
    .. versionchanged:: 9.4
       Search in entry point paths
    """
    from pywikibot import config
    path_list = []  # paths to find misspellings

    def test_paths(paths, root: Path):
        """Search for filename in given paths within 'root' base directory."""
        for file_package in paths:
            package = file_package.split('.')
            path = [*package, filename]
            testpath = root.joinpath(*path)
            if testpath.exists():
                return str(testpath)
            path_list.append(testpath.parent)
        return None

    # search through user scripts paths
    user_script_paths = ['']
    if config.user_script_paths:  # pragma: no cover
        if isinstance(config.user_script_paths, list):
            user_script_paths += config.user_script_paths
        else:
            warn("'user_script_paths' must be a list,\n"
                 f'found: {type(config.user_script_paths).__name__}.'
                 ' Ignoring this setting.')

    found = test_paths(user_script_paths, Path(config.base_dir))
    if found:  # pragma: no cover
        return found

    if site_package:  # search for entry points
        import importlib
        from importlib.metadata import entry_points

        from pywikibot.i18n import set_messages_package

        if sys.version_info < (3, 10):
            entry_points_items = [
                ep for ep in entry_points().get('pywikibot', [])
                if ep.name == 'scriptspath'
            ]
        else:
            entry_points_items = entry_points(
                name='scriptspath',
                group='pywikibot',
            )

        for ep in entry_points_items:
            path = ep.load()
            found = test_paths([''], path)
            if found:
                i18n_package = path.stem + '.i18n'
                if importlib.import_module(i18n_package).__file__ is not None:
                    set_messages_package(i18n_package)
                return found

    else:  # search in scripts folder
        script_paths = [
            'scripts.userscripts',
            'scripts',
            'scripts.maintenance',
        ]
        found = test_paths(script_paths, wrapper_dir.parents[1])
        if found:
            return found

    # search for system scripts in pywikibot.scripts directory
    found = test_paths([''], wrapper_dir)
    if found:
        return found

    return find_alternates(filename, path_list)


def execute():
    """Parse arguments, extract filename and run the script.

    .. versionadded:: 7.0
       renamed from :func:`main`
    """
    global filename

    # If -nolog options are in global args, add them to
    # script args.
    if '-nolog' in global_args:
        script_args.append('-nolog')

    if global_args:  # don't use sys.argv
        unknown_args = pwb.handle_args(global_args)
        if unknown_args:  # pragma: no cover
            print('ERROR: unknown pwb.py argument{}: {}\n'
                  .format('' if len(unknown_args) == 1 else 's',
                          ', '.join(unknown_args)))
            return False

    if not filename:
        return False

    file_package = None

    if not os.path.exists(filename):
        filename = find_filename(filename)
        if filename is None:
            return True

    # When both pwb.py and the filename to run are within the current
    # working directory:
    # a) set __package__ as if called using python -m scripts.blah.foo
    # b) set __file__ to be relative, so it can be relative in backtraces,
    #    and __file__ *appears* to be an unstable path to load data from.
    # This is a rough (and quick!) emulation of 'package name' detection.
    # a much more detailed implementation is in coverage's find_module.
    # https://bitbucket.org/ned/coveragepy/src/default/coverage/execfile.py
    cwd = Path.cwd()
    syspath = Path(sys.argv[0])
    absolute_path = syspath.parent
    file_path = Path(filename)
    if absolute_path == cwd and cwd in file_path.parents:
        relative_filename = file_path.relative_to(absolute_path)
        # remove the filename, and use '.' instead of path separator.
        file_package = str(relative_filename.parent).replace(os.sep, '.')
        filename = os.path.join(os.curdir, str(relative_filename))

    module = None
    if file_package:
        try:
            module = sys.modules[file_package]
        except KeyError:
            try:
                module = import_module(file_package)
            except ImportError as e:
                warn(f'Parent module {file_package} not found: {e}',
                     ImportWarning)

    help_option = any(arg.startswith('-help:') or arg == '-help'
                      for arg in script_args)
    if site_package or check_modules(filename) or help_option:
        run_python_file(filename, script_args, module)
    return True


def main():
    """Script entry point. Print doc if necessary.

    .. versionchanged:: 7.0
       previous implementation was renamed to :func:`execute`
    """
    if not check_modules():  # pragma: no cover
        sys.exit()

    if not execute():
        print(__doc__)


def run():  # pragma: no cover
    """Site package entry point. Print doc if necessary.

    .. versionadded:: 7.0
    """
    global site_package
    site_package = True
    if not execute():
        print(__doc__)


if __name__ == '__main__':
    main()
