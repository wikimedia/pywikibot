# -*- coding: utf-8  -*-
"""Wrapper script to use Pywikibot in 'directory' mode.

Run scripts using:

    python pwb.py <name_of_script> <options>

and it will use the package directory to store all user files, will fix up
search paths so the package does not need to be installed, etc.
"""
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import print_function
__version__ = '$Id$'

# The following snippet was developed by Ned Batchelder (and others)
# for coverage [1], with python 3 support [2] added later,
# and is available under the BSD license (see [3])
# [1] https://bitbucket.org/ned/coveragepy/src/b5abcee50dbe/coverage/execfile.py
# [2] https://bitbucket.org/ned/coveragepy/src/fd5363090034/coverage/execfile.py
# [3] https://bitbucket.org/ned/coveragepy/src/2c5fb3a8b81c/setup.py?at=default#cl-31

import os
import sys
import types

pwb = None


def tryimport_pwb():
    """Try to import pywikibot.

    If so, we need to patch pwb.argvu, too.
    If pywikibot is not available, we create a mock object to remove the
    need for if statements further on.
    """
    global pwb
    try:
        import pywikibot  # noqa
        pwb = pywikibot
    except RuntimeError:
        pwb = lambda: None
        pwb.argvu = []


def run_python_file(filename, argv, argvu, package=None):
    """Run a python file as if it were the main program on the command line.

    `filename` is the path to the file to execute, it need not be a .py file.
    `args` is the argument array to present as sys.argv, as unicode strings.

    """
    tryimport_pwb()

    # Create a module to serve as __main__
    old_main_mod = sys.modules['__main__']
    main_mod = types.ModuleType('__main__')
    sys.modules['__main__'] = main_mod
    main_mod.__file__ = filename
    if sys.version_info[0] > 2:
        main_mod.__builtins__ = sys.modules['builtins']
    else:
        main_mod.__builtins__ = sys.modules['__builtin__']
    if package:
        main_mod.__package__ = package

    # Set sys.argv and the first path element properly.
    old_argv = sys.argv
    old_argvu = pwb.argvu
    old_path0 = sys.path[0]

    sys.argv = argv
    pwb.argvu = argvu
    sys.path[0] = os.path.dirname(filename)

    try:
        source = open(filename).read()
        exec(compile(source, filename, "exec"), main_mod.__dict__)
    finally:
        # Restore the old __main__
        sys.modules['__main__'] = old_main_mod

        # Restore the old argv and path
        sys.argv = old_argv
        sys.path[0] = old_path0
        pwb.argvu = old_argvu

# end of snippet from coverage

if sys.version_info[0] not in (2, 3):
    raise RuntimeError("ERROR: Pywikibot only runs under Python 2 "
                       "or Python 3")
version = tuple(sys.version_info)[:3]
if version < (2, 6, 5):
    raise RuntimeError("ERROR: Pywikibot only runs under Python 2.6.5 "
                       "or higher")
if version >= (3, ) and version < (3, 3):
    raise RuntimeError("ERROR: Pywikibot only runs under Python 3.3 "
                       "or higher")

# Establish a normalised path for the directory containing pwb.py.
# Either it is '.' if the user's current working directory is the same,
# or it is the absolute path for the directory of pwb.py
absolute_path = os.path.dirname(sys.argv[0])
if not os.path.isabs(absolute_path):
    absolute_path = os.path.abspath(os.path.join(os.curdir, absolute_path))
rewrite_path = absolute_path

sys.path = [sys.path[0], rewrite_path,
            os.path.join(rewrite_path, 'pywikibot', 'compat'),
            os.path.join(rewrite_path, 'externals')
            ] + sys.path[1:]

# try importing the known externals, and raise an error if they are not found
try:
    import httplib2
    if not hasattr(httplib2, '__version__'):
        print("httplib2 import problem: httplib2.__version__ does not exist.")
        if sys.version_info > (3, 3):
            print("Python 3.4+ has probably loaded externals/httplib2 "
                  "although it doesnt have an __init__.py.")
        httplib2 = None
except ImportError as e:
    print("ImportError: %s" % e)
    httplib2 = None

if not httplib2:
    print("Python module httplib2 >= 0.6.0 is required.")
    print("Did you clone without --recursive?\n"
          "Try running 'git submodule update --init' "
          "or 'pip install httplib2'.")
    sys.exit(1)

# httplib2 0.6.0 was released with __version__ as '$Rev$'
#                and no module variable CA_CERTS.
if httplib2.__version__ == '$Rev$' and 'CA_CERTS' not in httplib2.__dict__:
    httplib2.__version__ = '0.6.0'
from distutils.version import StrictVersion
if StrictVersion(httplib2.__version__) < StrictVersion("0.6.0"):
    print("Python module httplib2 (%s) needs to be 0.6.0 or greater." %
          httplib2.__file__)
    print("Did you clone without --recursive?\n"
          "Try running 'git submodule update --init' "
          "or 'pip install --upgrade httplib2'.")
    sys.exit(1)

del httplib2

if sys.version_info[0] == 2 and sys.version_info[1] == 6:
    try:
        import ordereddict
        del ordereddict
    except ImportError as e:
        print("ImportError: %s" % e)
        print("pywikibot depends on module ordereddict in Python 2.6.")
        print("Upgrade to Python 2.7, or run 'pip install ordereddict'")
        sys.exit(1)

# Search for user-config.py before creating one.
try:
    # If successful, user-config.py already exists in one of the candidate
    # directories. See config2.py for details on search order.
    # Use env var to communicate to config2.py pwb.py location (bug 72918).
    os.environ['PYWIKIBOT2_DIR_PWB'] = os.path.split(__file__)[0]
    import pywikibot  # noqa
except RuntimeError as err:
    # user-config.py to be created
    print("NOTE: 'user-config.py' was not found!")
    print("Please follow the prompts to create it:")
    run_python_file('generate_user_files.py',
                    ['generate_user_files.py'] + sys.argv[1:],
                    [])
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        file_package = None
        tryimport_pwb()
        filename = sys.argv[1]
        argv = sys.argv[1:]
        argvu = pwb.argvu[1:]
        if not filename.endswith('.py'):
            filename += '.py'
        if not os.path.exists(filename):
            testpath = os.path.join(os.path.split(__file__)[0],
                                    'scripts',
                                    filename)
            file_package = 'scripts'
            if os.path.exists(testpath):
                filename = testpath
            else:
                raise OSError("%s not found!" % filename)

        # When both pwb.py and the filename to run are within the current
        # working directory:
        # a) set __package__ as if called using python -m scripts.blah.foo
        # b) set __file__ to be relative, so it can be relative in backtraces,
        #    and __file__ *appears* to be an unstable path to load data from.
        # This is a rough (and quick!) emulation of 'package name' detection.
        # a much more detailed implementation is in coverage's find_module.
        # https://bitbucket.org/ned/coveragepy/src/default/coverage/execfile.py
        cwd = os.path.abspath(os.getcwd())
        if absolute_path == cwd:
            absolute_filename = os.path.abspath(filename)
            if absolute_filename.startswith(rewrite_path):
                relative_filename = os.path.relpath(filename)
                # remove the filename, and use '.' instead of path separator.
                file_package = os.path.dirname(
                    relative_filename).replace(os.sep, '.')
                filename = os.path.join(os.curdir, relative_filename)

        if file_package and file_package not in sys.modules:
            try:
                __import__(file_package)
            except ImportError as e:
                print('Parent module %s not found: %s'
                      % (file_package, e), file=sys.stderr)

        run_python_file(filename, argv, argvu, file_package)
    else:
        print(__doc__)
