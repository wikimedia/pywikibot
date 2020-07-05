#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Spawns an interactive Python shell and imports the pywikibot library.

The following local option is supported:

-noimport Do not import the pywikibot library. All other arguments are
          ignored in this case.

Usage:

    python pwb.py shell [args]

If no arguments are given, the pywikibot library will not be loaded.
"""
# (C) Pywikibot team, 2014-2020
#
# Distributed under the terms of the MIT license.
#
import code
import sys


def main(*args):
    """Script entry point."""
    args = list(args)
    if '-noimport' in args:
        args.remove('-noimport')
        env = None
        warn_type = 'Ignoring'
    else:
        import pywikibot
        args = pywikibot.handle_args(args)
        env = {'pywikibot': pywikibot}
        warn_type = 'Unknown'

    if args:
        print('{} arguments: {}\n'  # noqa: T001
              .format(warn_type, ', '.join(args)))

    # Various stuffs in Python 3.4+, such as history file.
    # This is defined in the site module of the Python Standard Library,
    # and usually called by the built-in CPython interactive shell.
    if hasattr(sys, '__interactivehook__'):
        sys.__interactivehook__()

    code.interact("""Welcome to the Pywikibot interactive shell!""", local=env)


if __name__ == '__main__':
    if sys.platform == 'win32':
        import subprocess
        subprocess.run('title Python {} Shell'
                       .format(*sys.version.split(' ', 1)), shell=True)
        del subprocess
    args = []
    if sys.argv and sys.argv[0].endswith(('shell', 'shell.py')):
        args = sys.argv[1:]
    main(*args)
