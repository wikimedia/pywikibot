# -*- coding: utf-8  -*-
"""wrapper script to use rewrite in 'directory' mode - run scripts using
python pwb.py <name_of_script> <options>

and it will use the package directory to store all user files, will fix up
search paths so the package does not need to be installed, etc.
"""
# (C) Pywikibot team, 2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

# The following snippet was developed by Ned Batchelder (and others)
# for coverage.py [1], and is available under the BSD license (see [2])
# [1] https://bitbucket.org/ned/coveragepy/src/b5abcee50dbe/coverage/execfile.py
# [2] https://bitbucket.org/ned/coveragepy/src/2c5fb3a8b81cc56d8ad57dd1bd83ef7740f0d65d/setup.py?at=default#cl-31

import imp
import os
import sys


def tryimport_pwb():
    # See if we can import pywikibot. If so, we need to patch pwb.argvu, too.
    # If pywikibot is not available, we create a mock object to remove the
    # need for if statements further on.
    global pwb
    try:
        import pywikibot
        pwb = pywikibot
    except RuntimeError:
        pwb = lambda: None
        pwb.argvu = []


def run_python_file(filename, argv, argvu):
    """Run a python file as if it were the main program on the command line.

    `filename` is the path to the file to execute, it need not be a .py file.
    `args` is the argument array to present as sys.argv, as unicode strings.

    """
    tryimport_pwb()

    # Create a module to serve as __main__
    old_main_mod = sys.modules['__main__']
    main_mod = imp.new_module('__main__')
    sys.modules['__main__'] = main_mod
    main_mod.__file__ = filename
    if sys.version_info[0] == 2:
        main_mod.__builtins__ = sys.modules['__builtin__']
    else:
        main_mod.builtins = sys.modules['builtins']

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

#### end of snippet

if not os.environ.get("PY3", False):
    if sys.version_info[0] != 2:
        raise RuntimeError("ERROR: Pywikibot only runs under Python 2")
    if sys.version_info < (2, 6, 5):
        raise RuntimeError("ERROR: Pywikibot only runs under Python 2.6.5 "
                           "or higher")
else:
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

rewrite_path = os.path.dirname(sys.argv[0])
if not os.path.isabs(rewrite_path):
    rewrite_path = os.path.abspath(os.path.join(os.curdir, rewrite_path))

sys.path = [sys.path[0], rewrite_path,
            os.path.join(rewrite_path, 'pywikibot', 'compat'),
            os.path.join(rewrite_path, 'externals')
            ] + sys.path[1:]

# try importing the known externals, and raise an error if they are not found
try:
    import httplib2
except ImportError as e:
    print("ImportError: %s" % e)
    print("Python module httplib2 >= 0.6.0 is required.")
    print("Did you clone without --recursive?\n"
          "Try running 'git submodule update --init'.")
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
          "Try running 'git submodule update --init'.")
    sys.exit(1)

if "PYWIKIBOT2_DIR" not in os.environ:
    os.environ["PYWIKIBOT2_DIR"] = os.path.split(__file__)[0]

for i, x in enumerate(sys.argv):
    if x.startswith("-dir:"):
        os.environ["PYWIKIBOT2_DIR"] = x[5:]
        sys.argv.pop(i)
        break

user_config_path = os.path.join(os.environ["PYWIKIBOT2_DIR"], "user-config.py")
if not os.path.exists(user_config_path):
    print("NOTE: %s was not found" % user_config_path)
    print("Please follow the prompts to create it:")
    path = 'generate_user_files.py'
    run_python_file(path, [path], [path.decode('ascii')])

if len(sys.argv) > 1:
    tryimport_pwb()
    fn = sys.argv[1]
    argv = sys.argv[1:]
    argvu = pwb.argvu[1:]
    if not fn.endswith('.py'):
        fn += '.py'
    if not os.path.exists(fn):
        testpath = os.path.join(os.path.split(__file__)[0], 'scripts', fn)
        if os.path.exists(testpath):
            fn = testpath
        else:
            raise OSError("%s not found!" % fn)
    run_python_file(fn, argv, argvu)
elif __name__ == "__main__":
    print(__doc__)
