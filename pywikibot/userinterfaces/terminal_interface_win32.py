# -*- coding: utf-8 -*-
"""User interface for Win32 terminals."""
#
# (C) Pywikibot team, 2003-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot.tools import ModuleDeprecationWrapper

from pywikibot.userinterfaces import (
    terminal_interface_base,
    win32_unicode,
)

import ctypes

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


class Win32BaseUI(terminal_interface_base.UI):

    """DEPRECATED. User interface for Win32 terminals without ctypes."""

    def __init__(self):
        """Initializer."""
        super(Win32BaseUI, self).__init__()
        self.encoding = 'ascii'


class Win32UI(terminal_interface_base.UI):

    """User interface for Win32 terminals using ctypes."""

    def __init__(self):
        """Initializer."""
        super(Win32CtypesUI, self).__init__()
        (stdin, stdout, stderr, argv) = win32_unicode.get_unicode_console()
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
        fg, bg = self.divide_color(color)
        windows_color = windowsColors[fg]
        # Merge foreground/backgroung color if needed.
        if bg is not None:
            windows_color = windowsColors[bg] << 4 | windows_color
        ctypes.windll.kernel32.SetConsoleTextAttribute(
            target_stream._hConsole, windows_color)

    def _raw_input(self):
        data = self.stdin.readline()
        # data is in both Python versions str but '\x1a' is unicode in Python 2
        # so explicitly convert into str as it otherwise tries to decode data
        if str('\x1a') in data:
            raise EOFError()
        return data.strip()


Win32CtypesUI = Win32UI

wrapper = ModuleDeprecationWrapper(__name__)
wrapper._add_deprecated_attr('Win32CtypesUI',
                             replacement_name='Win32UI',
                             since='20190217')
wrapper._add_deprecated_attr('Win32BaseUI',
                             replacement_name='Win32UI',
                             since='20190217')
