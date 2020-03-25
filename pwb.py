#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Wrapper script to use Pywikibot in 'directory' mode.

Run scripts using:

    python pwb.py <pwb options> <name_of_script> <options>

and it will use the package directory to store all user files, will fix up
search paths so the package does not need to be installed, etc.

Currently <pwb options> are global options. This can be used for tests
to set the default site like (see T216825):

    python pwb.py -lang:de bot_tests -v
"""
# (C) Pywikibot team, 2012-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from difflib import get_close_matches
from importlib import import_module
import os
import sys
from time import sleep
import types

from warnings import warn

PYTHON_VERSION = sys.version_info[:3]
PY2 = (PYTHON_VERSION[0] == 2)

VERSIONS_REQUIRED_MESSAGE = """
Pywikibot is not available on:
{version}

This version of Pywikibot only supports Python 2.7.4+ or 3.4+.
"""


def python_is_supported():
    """Check that Python is supported."""
    # Any change to this must be copied to setup.py
    return PYTHON_VERSION >= (3, 4, 0) or PY2 and PYTHON_VERSION >= (2, 7, 4)


if not python_is_supported():
    print(VERSIONS_REQUIRED_MESSAGE.format(version=sys.version))
    sys.exit(1)

pwb = None


# The following snippet was developed by Ned Batchelder (and others)
# for coverage [1], with python 3 support [2] added later,
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
    # it's explicitly using str() to bypass unicode_literals in Python 2
    main_mod = types.ModuleType(str('__main__'))
    sys.modules['__main__'] = main_mod
    main_mod.__file__ = filename
    if not PY2:
        main_mod.__builtins__ = sys.modules['builtins']
    else:
        main_mod.__builtins__ = sys.modules['__builtin__']
    if package:
        # it's explicitly using str() to bypass unicode_literals in Python 2
        main_mod.__package__ = str(package)

    # Set sys.argv and the first path element properly.
    old_argv = sys.argv
    old_argvu = pwb.argvu
    old_path0 = sys.path[0]

    sys.argv = argv
    pwb.argvu = argvu
    sys.path[0] = os.path.dirname(filename)

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
        sys.path[0] = old_path0
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

    @return: filename, script args, local args for pwb.py
    @rtype: tuple
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
    """Check whether mandatory modules are present."""
    import pkg_resources
    if script:
        from setup import script_deps
        try:
            from pathlib import Path
        except ImportError:  # Python 2
            from pathlib2 import Path
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

    del pkg_resources
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


# Establish a normalised path for the directory containing pwb.py.
# Either it is '.' if the user's current working directory is the same,
# or it is the absolute path for the directory of pwb.py
absolute_path = abspath(os.path.dirname(sys.argv[0]))

if absolute_path not in sys.path[:2]:
    sys.path.insert(1, absolute_path)

if not check_modules():
    sys.exit()

filename, args, local_args = handle_args(*sys.argv)

# Search for user-config.py before creating one.
# If successful, user-config.py already exists in one of the candidate
# directories. See config2.py for details on search order.
# Use env var to communicate to config2.py pwb.py location (bug T74918).
_pwb_dir = os.path.split(__file__)[0]
if sys.platform == 'win32' and PY2:
    _pwb_dir = str(_pwb_dir)
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

try:
    from pathlib import Path
except ImportError:  # Python 2
    from pathlib2 import Path


def find_alternates(filename, script_paths):
    """Search for similar filenames in the given script paths."""
    from pywikibot import config, input_choice, output
    from pywikibot.bot import ShowingListOption, QuitKeyboardInterrupt
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
                 'found: {0}. Ignoring this setting.'
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
    if not filename:
        return False

    if local_args:  # don't use sys.argv
        pwb_args = pwb.handle_args(local_args)
        if pwb_args:
            print('ERROR: unknown pwb.py argument{}: {}\n'
                  .format('' if len(pwb_args) == 1 else 's',
                          ', '.join(pwb_args)))
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
    if absolute_path == cwd:
        absolute_filename = abspath(filename)[:len(cwd)]
        if absolute_filename == cwd:
            relative_filename = os.path.relpath(filename)
            # remove the filename, and use '.' instead of path separator.
            file_package = os.path.dirname(
                relative_filename).replace(os.sep, '.')
            filename = os.path.join(os.curdir, relative_filename)

    if file_package and file_package not in sys.modules:
        try:
            import_module(file_package)
        except ImportError as e:
            warn('Parent module %s not found: %s'
                 % (file_package, e), ImportWarning)

    if check_modules(filename) or '-help' in args:
        run_python_file(filename,
                        [filename] + args,
                        [Path(filename).stem] + argvu[1:],
                        file_package)
    return True


if __name__ == '__main__':
    if not main():
        print(__doc__)
