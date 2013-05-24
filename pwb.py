# -*- coding: utf-8  -*-
"""wrapper script to use rewrite in 'directory' mode - run scripts using
python pwb.py <name_of_script> <options>

and it will use the package directory to store all user files, will fix up
search paths so the package does not need to be installed, etc.
"""
# (C) Pywikipedia team, 2012
#
__version__ = '$Id$'
#
# Distributed under the terms of the MIT license.
#

import sys,os

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

if not os.path.exists(os.path.join(os.environ["PYWIKIBOT2_DIR"], "user-config.py")):
    execfile('generate_user_files.py')

sys.argv.pop(0)
if len(sys.argv) > 0:
    if not os.path.exists(sys.argv[0]):
        testpath = os.path.join(os.path.split(__file__)[0], 'scripts', sys.argv[0])
        if os.path.exists(testpath):
            sys.argv[0] = testpath
        else:
            testpath = testpath + '.py'
            if os.path.exists(testpath):
                sys.argv[0] = testpath
            else:
                raise Exception("%s not found!" % sys.argv[0]) 
    sys.path.append(os.path.split(sys.argv[0])[0])
    execfile(sys.argv[0])
else:
    sys.argv.append('')
