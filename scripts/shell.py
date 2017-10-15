#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Spawns an interactive Python shell.

Usage:

    python pwb.py shell [args]

If no arguments are given, the pywikibot library will not be loaded.
"""
# (C) Pywikibot team, 2014-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals


def main(*args):
    """Script entry point."""
    env = None
    if args:
        import pywikibot
        pywikibot.handle_args(args)
        env = locals()

    import code
    code.interact("""Welcome to the Pywikibot interactive shell!""", local=env)


if __name__ == "__main__":
    import sys
    args = []
    if set(sys.argv) - set(['shell', 'shell.py']):
        args = sys.argv
    del sys
    main(*args)
