# -*- coding: utf-8  -*-
"""wrapper script to use rewrite in 'directory' mode - run scripts using
python pwb.py <name_of_script> <options>

and it will use the package directory to store all user files, will fix up
search paths so the package does not need to be installed, etc.
"""
# (C) Pywikipedia team, 2013
#
__version__ = '$Id$'
#
# Distributed under the terms of the MIT license.
#


# The following snippet was developed by Ned Batchelder (and others)
# for coverage.py [1], and is available under the BSD license (see [2])
# [1] https://bitbucket.org/ned/coveragepy/src/b5abcee50dbe/coverage/execfile.py
# [2] https://bitbucket.org/ned/coveragepy/src/2c5fb3a8b81cc56d8ad57dd1bd83ef7740f0d65d/setup.py?at=default#cl-31

import imp
import os
import sys


def run_python_file(filename, args):
    """Run a python file as if it were the main program on the command line.

    `filename` is the path to the file to execute, it need not be a .py file.
    `args` is the argument array to present as sys.argv, including the first
    element representing the file being executed.

    """
    # Create a module to serve as __main__
    old_main_mod = sys.modules['__main__']
    main_mod = imp.new_module('__main__')
    sys.modules['__main__'] = main_mod
    main_mod.__file__ = filename
    main_mod.__builtins__ = sys.modules['__builtin__']

    # Set sys.argv and the first path element properly.
    old_argv = sys.argv
    old_path0 = sys.path[0]
    sys.argv = args
    sys.path[0] = os.path.dirname(filename)

    try:
        source = open(filename).read()
        exec compile(source, filename, "exec") in main_mod.__dict__
    finally:
        # Restore the old __main__
        sys.modules['__main__'] = old_main_mod

        # Restore the old argv and path
        sys.argv = old_argv
        sys.path[0] = old_path0

#### end of snippet

if sys.version_info[0] != 2:
    raise RuntimeError("ERROR: Pywikipediabot only runs under Python 2")
if sys.version_info[1] < 6:
    raise RuntimeError("ERROR: Pywikipediabot only runs under Python 2.6 or higher")

rewrite_path = os.path.dirname(sys.argv[0])
if not os.path.isabs(rewrite_path):
    rewrite_path = os.path.abspath(os.path.join(os.curdir, rewrite_path))

sys.path.append(rewrite_path)
sys.path.append(os.path.join(rewrite_path, 'externals/httplib2'))
sys.path.append(os.path.join(rewrite_path, 'pywikibot/compat'))
sys.path.append(os.path.join(rewrite_path, 'externals'))

if "PYWIKIBOT2_DIR" not in os.environ:
    os.environ["PYWIKIBOT2_DIR"] = os.path.split(__file__)[0]

for i, x in enumerate(sys.argv):
    if x.startswith("-dir:"):
        os.environ["PYWIKIBOT2_DIR"] = x[5:]
        sys.argv.pop(i)
        break


if not os.path.exists(os.path.join(os.environ["PYWIKIBOT2_DIR"], "user-config.py")):
    run_python_file('generate_user_files.py', ['generate_user_files.py'])

if len(sys.argv) > 1:
    fn = sys.argv[1]
    args = sys.argv[1:]

    if not os.path.exists(fn):
        testpath = os.path.join(os.path.split(__file__)[0], 'scripts', fn)
        if os.path.exists(testpath):
            fn = testpath
        else:
            testpath = testpath + '.py'
            if os.path.exists(testpath):
                fn = testpath
            else:
                raise Exception("%s not found!" % fn)
    run_python_file(fn, args)
