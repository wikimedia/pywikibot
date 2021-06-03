#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Wrapper script to invoke pywikibot-based scripts.

Run scripts with pywikibot in directory mode using::

    python pwb.py <pwb options> <name_of_script> <options>

This wrapper script uses the package directory to store all user files,
will fix up search paths so the package does not need to be installed, etc.

Currently `<pwb options>` are global options. This can be used for tests
to set the default site (see T216825)::

    python pwb.py -lang:de bot_tests -v
"""
# (C) Pywikibot team, 2012-2021
#
# Distributed under the terms of the MIT license.
#
# ## KEEP PYTHON 2 SUPPORT FOR THIS SCRIPT ## #
from __future__ import print_function

import os
import pkg_resources
import sys
import types

from difflib import get_close_matches
from importlib import import_module
from time import sleep
from warnings import warn


pwb = None


def check_pwb_versions(package):
    """Validate package version and scripts version.

    Rules:
        - Pywikibot version must not be older than scrips version
        - Scripts version must not be older than previous Pyvikibot version
          due to deprecation policy
    """
    version = pkg_resources.packaging.version
    scripts_version = version.parse(getattr(package,
                                            '__version__',
                                            pwb.__version__))
    wikibot_version = version.parse(pwb.__version__)
    if scripts_version.release > wikibot_version.release:
        print('WARNING: Pywikibot version {} is behind scripts package '
              'version {}.\nYour Pywikibot may need an update or be '
              'misconfigured.\n'.format(wikibot_version, scripts_version))

    # calculate previous minor release
    prev_wikibot = version.parse('{v.major}.{}.{v.micro}'
                                 .format(wikibot_version.minor - 1,
                                         v=wikibot_version,))
    if scripts_version.release < prev_wikibot.release:
        print('WARNING: Scripts package version {} is behind legacy Pywikibot '
              'version {} and current version {}\nYour scripts may need an '
              'update or be misconfigured.\n'
              .format(scripts_version, prev_wikibot, wikibot_version, ))


# The following snippet was developed by Ned Batchelder (and others)
# for coverage [1], with Python 3 support [2] added later,
# and is available under the BSD license (see [3])
# [1]
# https://bitbucket.org/ned/coveragepy/src/b5abcee50dbe/coverage/execfile.py
# [2]
# https://bitbucket.org/ned/coveragepy/src/fd5363090034/coverage/execfile.py
# [3]
# https://bitbucket.org/ned/coveragepy/src/2c5fb3a8b81c/setup.py?at=default#cl-31


def run_python_file(filename, argv, argvu, package=None):
    """Run a python file as if it were the main program on the command line.

    `filename` is the path to the file to execute, it need not be a .py file.
    `args` is the argument array to present as sys.argv, as unicode strings.

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
    global pkg_resources
    del pkg_resources

    # Set sys.argv and the first path element properly.
    old_argv = sys.argv
    old_argvu = pwb.argvu

    sys.argv = argv
    pwb.argvu = argvu
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


def abspath(path):
    """Convert path to absolute path, with uppercase drive letter on win32."""
    path = os.path.abspath(path)
    if path[0] != '/':
        # normalise Windows drive letter
        path = path[0].upper() + path[1:]
    return path


def handle_args(pwb_py, *args):
    """Handle args and get filename.

    :return: filename, script args, local args for pwb.py
    :rtype: tuple
    """
    fname = None
    index = 0
    for arg in args:
        if arg.startswith('-'):
            index += 1
        else:
            fname = arg
            if not fname.endswith('.py'):
                fname += '.py'
            break
    return fname, list(args[index + int(bool(fname)):]), args[:index]


def _print_requirements(requirements, script, variant):
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
        print('    pip install "{}"\n'
              .format(str(requirement).partition(';')[0]))


def check_modules(script=None):
    """Check whether mandatory modules are present.

    This also checks Python version when importing deptendencies from setup.py

    :param script: The script name to be checked for dependencies
    :type script: str or None
    :return: True if all dependencies are installed
    :rtype: bool
    :raise RuntimeError: wrong Python version found in setup.py
    """
    if script:
        from setup import script_deps
        dependencies = script_deps.get(Path(script).name, [])
    else:
        from setup import dependencies

    missing_requirements = []
    version_conflicts = []
    for requirement in pkg_resources.parse_requirements(dependencies):
        if requirement.marker is None \
           or pkg_resources.evaluate_marker(str(requirement.marker)):
            try:
                pkg_resources.resource_exists(requirement, requirement.name)
            except pkg_resources.DistributionNotFound as e:
                missing_requirements.append(requirement)
                print(e)
            except pkg_resources.VersionConflict as e:
                version_conflicts.append(requirement)
                print(e)

    del dependencies

    _print_requirements(missing_requirements, script, 'missing')
    _print_requirements(version_conflicts, script, 'outdated')

    if version_conflicts and not missing_requirements:
        print('\nYou may continue on your own risk; type CTRL-C to stop.')
        try:
            sleep(5)
        except KeyboardInterrupt:
            return False

    return not missing_requirements


try:
    if not check_modules():
        raise RuntimeError('')  # no further output needed
except RuntimeError as e:  # setup.py may also raise RuntimeError
    sys.exit(e)

from pathlib import Path  # noqa: E402


filename, script_args, global_args = handle_args(*sys.argv)

# Search for user-config.py before creating one.
# If successful, user-config.py already exists in one of the candidate
# directories. See config.py for details on search order.
# Use env var to communicate to config.py pwb.py location (bug T74918).
_pwb_dir = os.path.split(__file__)[0]
os.environ['PYWIKIBOT_DIR_PWB'] = _pwb_dir
try:
    import pywikibot as pwb
except RuntimeError:
    os.environ['PYWIKIBOT_NO_USER_CONFIG'] = '2'
    import pywikibot as pwb

    # user-config.py to be created
    if filename is not None and not (filename.startswith('generate_')
                                     or filename == 'version.py'):
        print("NOTE: 'user-config.py' was not found!")
        print('Please follow the prompts to create it:')
        run_python_file(os.path.join(_pwb_dir, 'generate_user_files.py'),
                        ['generate_user_files.py'],
                        ['generate_user_files.py'])
        # because we have loaded pywikibot without user-config.py loaded,
        # we need to re-start the entire process. Ask the user to do so.
        print('Now, you have to re-execute the command to start your script.')
        sys.exit(1)
except ImportError as e:  # raised in textlib
    sys.exit(e)


def find_alternates(filename, script_paths):
    """Search for similar filenames in the given script paths."""
    from pywikibot import config, input_choice, output
    from pywikibot.bot import QuitKeyboardInterrupt, ShowingListOption
    from pywikibot.tools.formatter import color_format

    assert config.pwb_close_matches > 0, \
        'config.pwb_close_matches must be greater than 0'
    assert 0.0 < config.pwb_cut_off < 1.0, \
        'config.pwb_cut_off must be a float in range [0, 1]'

    print('ERROR: {} not found! Misspelling?'.format(filename),
          file=sys.stderr)

    scripts = {}

    script_paths = [['.']] + script_paths  # add current directory
    for path in script_paths:
        for script_name in os.listdir(os.path.join(*path)):
            # remove .py for better matching
            name, _, suffix = script_name.rpartition('.')
            if suffix == 'py' and not name.startswith('__'):
                scripts[name] = os.path.join(*(path + [script_name]))

    filename = filename[:-3]
    similar_scripts = get_close_matches(filename, scripts,
                                        config.pwb_close_matches,
                                        config.pwb_cut_off)
    if not similar_scripts:
        return None

    if len(similar_scripts) == 1:
        script = similar_scripts[0]
        wait_time = config.pwb_autostart_waittime
        output(color_format(
            'NOTE: Starting the most similar script '
            '{lightyellow}{0}.py{default}\n'
            '      in {1} seconds; type CTRL-C to stop.',
            script, wait_time))
        try:
            sleep(wait_time)  # Wait a bit to let it be cancelled
        except KeyboardInterrupt:
            return None
    else:
        msg = '\nThe most similar scripts are:'
        alternatives = ShowingListOption(similar_scripts, pre=msg, post='')
        try:
            prefix, script = input_choice('Which script to be run:',
                                          alternatives, default='1')
        except QuitKeyboardInterrupt:
            return None
        print()
    return scripts[script]


def find_filename(filename):
    """Search for the filename in the given script paths."""
    from pywikibot import config

    script_paths = ['scripts.userscripts',
                    'scripts',
                    'scripts.maintenance']

    if config.user_script_paths:
        if isinstance(config.user_script_paths, list):
            script_paths = config.user_script_paths + script_paths
        else:
            warn("'user_script_paths' must be a list,\n"
                 'found: {}. Ignoring this setting.'
                 .format(type(config.user_script_paths)))

    path_list = []
    for file_package in script_paths:
        package = file_package.split('.')
        paths = package + [filename]
        testpath = os.path.join(_pwb_dir, *paths)
        if os.path.exists(testpath):
            filename = testpath
            break
        path_list.append(package)
    else:
        filename = find_alternates(filename, path_list)
    return filename


def main():
    """Command line entry point."""
    global filename

    if global_args:  # don't use sys.argv
        unknown_args = pwb.handle_args(global_args)
        if unknown_args:
            print('ERROR: unknown pwb.py argument{}: {}\n'
                  .format('' if len(unknown_args) == 1 else 's',
                          ', '.join(unknown_args)))
            return False

    if not filename:
        return False

    file_package = None
    argvu = pwb.argvu[1:]

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
    cwd = abspath(os.getcwd())
    absolute_path = abspath(os.path.dirname(sys.argv[0]))
    if absolute_path == cwd:
        absolute_filename = abspath(filename)[:len(cwd)]
        if absolute_filename == cwd:
            relative_filename = os.path.relpath(filename)
            # remove the filename, and use '.' instead of path separator.
            file_package = os.path.dirname(
                relative_filename).replace(os.sep, '.')
            filename = os.path.join(os.curdir, relative_filename)

    module = None
    if file_package and file_package not in sys.modules:
        try:
            module = import_module(file_package)
        except ImportError as e:
            warn('Parent module {} not found: {}'
                 .format(file_package, e), ImportWarning)

    help_option = any(arg.startswith('-help:') or arg == '-help'
                      for arg in script_args)
    if check_modules(filename) or help_option:
        run_python_file(filename,
                        [filename] + script_args,
                        [Path(filename).stem] + argvu[1:],
                        module)
    return True


if __name__ == '__main__':
    if not main():
        print(__doc__)
