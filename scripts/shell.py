#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Spawns an interactive Python shell.

Usage:
    python pwb.py shell

"""
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

if __name__ == "__main__":
    import code
    code.interact("""Welcome to the Pywikibot interactive shell!""")
