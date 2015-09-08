# -*- coding: utf-8 -*-
"""User interface for Win32 terminals."""
#
# (C) Pywikibot team, 2003-2013
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import re

from pywikibot.userinterfaces import terminal_interface_base

try:
    import ctypes
    ctypes_found = True
except ImportError:
    ctypes_found = False

windowsColors = {
    'default':     7,
    'black':       0,
    'blue':        1,
    'green':       2,
    'aqua':        3,
    'red':         4,
    'purple':      5,
    'yellow':      6,
    'lightgray':   7,
    'gray':        8,
    'lightblue':   9,
    'lightgreen':  10,
    'lightaqua':   11,
    'lightred':    12,
    'lightpurple': 13,
    'lightyellow': 14,
    'white':       15,
}

colorTagR = re.compile('\03{(?P<name>%s)}' % '|'.join(list(windowsColors.keys())))


# Compat for python <= 2.5
class Win32BaseUI(terminal_interface_base.UI):

    """User interface for Win32 terminals without ctypes."""

    def __init__(self):
        """Constructor."""
        terminal_interface_base.UI.__init__(self)
        self.encoding = 'ascii'


class Win32CtypesUI(Win32BaseUI):

    """User interface for Win32 terminals using ctypes."""

    def __init__(self):
        """Constructor."""
        Win32BaseUI.__init__(self)
        from .win32_unicode import stdin, stdout, stderr, argv
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.argv = argv
        self.encoding = 'utf-8'

    def support_color(self, target_stream):
        """Return whether the target stream supports actually color."""
        return getattr(target_stream, '_hConsole', None) is not None

    def encounter_color(self, color, target_stream):
        """Set the new color."""
        ctypes.windll.kernel32.SetConsoleTextAttribute(
            target_stream._hConsole, windowsColors[color])

    def _raw_input(self):
        data = self.stdin.readline()
        # data is in both Python versions str but '\x1a' is unicode in Python 2
        # so explicitly convert into str as it otherwise tries to decode data
        if str('\x1a') in data:
            raise EOFError()
        return data.strip()

if ctypes_found:
    Win32UI = Win32CtypesUI
else:
    Win32UI = Win32BaseUI
