#!/usr/bin/python3
"""
Spawns an interactive Python shell and imports the pywikibot library.

The following local option is supported::

 -noimport Do not import the pywikibot library. All other arguments are
           ignored in this case.

Usage::

    python pwb.py shell [args]

.. versionchanged:: 7.0
   moved to pywikibot.scripts
"""
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import code
import sys


def main(*args: str) -> None:
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
        print('{} arguments: {}\n'  # noqa: T001, T201
              .format(warn_type, ', '.join(args)))

    # Various stuffs in Python 3.4+, such as history file.
    # This is defined in the site module of the Python Standard Library,
    # and usually called by the built-in CPython interactive shell.
    if hasattr(sys, '__interactivehook__'):
        sys.__interactivehook__()

    code.interact("""Welcome to the Pywikibot interactive shell!""", local=env)


if __name__ == '__main__':  # pragma: no cover
    if sys.platform == 'win32':
        import platform
        import subprocess
        subprocess.run('title Python {} Shell'
                       .format(platform.python_version()),
                       shell=True, check=True)
        del subprocess
        del platform
    args = []
    if sys.argv and sys.argv[0].endswith(('shell', 'shell.py')):
        args = sys.argv[1:]
    main(*args)
