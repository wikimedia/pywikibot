"""
Platform independent terminal interface module.

It imports the appropriate operating system specific implementation.
"""
#
# (C) Pywikibot team, 2003-2020
#
# Distributed under the terms of the MIT license.
#
import sys


if sys.platform == 'win32':
    from pywikibot.userinterfaces.terminal_interface_win32 import Win32UI as UI
else:
    from pywikibot.userinterfaces.terminal_interface_unix import UnixUI as UI

__all__ = ('UI',)
