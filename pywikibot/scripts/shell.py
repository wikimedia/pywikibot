#!/usr/bin/env python3
"""Spawns an interactive Python shell and imports the pywikibot library.

To exit the shell, type :kbd:`ctrl-D` (Linux) or :kbd:`ctrl-Z` (Windows)
or use the :func:`exit` function.

The following local option is supported:

-noimport  Do not import the pywikibot library. All other arguments are
           ignored in this case.

Usage::

    python pwb.py shell [args]

.. versionchanged:: 7.0
   moved to pywikibot.scripts
"""
# (C) Pywikibot team, 2014-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import code
import sys


def main(*args: str) -> None:  # pragma: no cover
    """Script entry point.

    .. versionchanged:: 8.2
       *exitmsg* was added for :func:`code.interact`.
    """
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
        print('{} arguments: {}\n'  # noqa: T201
              .format(warn_type, ', '.join(args)))

    # Various stuffs in Python 3.4+, such as history file.
    # This is defined in the site module of the Python Standard Library,
    # and usually called by the built-in CPython interactive shell.
    if hasattr(sys, '__interactivehook__'):
        sys.__interactivehook__()

    code.interact('Welcome to the Pywikibot interactive shell!', local=env,
                  exitmsg='Thank you for using Pywikibot; exiting now...\n')


if __name__ == '__main__':
    if sys.platform == 'win32':
        import platform
        import subprocess
        subprocess.run(f'title Python {platform.python_version()} Shell',
                       shell=True, check=True)
        del subprocess
        del platform
    args = []
    if sys.argv and sys.argv[0].endswith(('shell', 'shell.py')):
        args = sys.argv[1:]
    main(*args)
