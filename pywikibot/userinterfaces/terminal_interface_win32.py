# -*- coding: utf-8 -*-
"""User interface for Win32 terminals."""
#
# (C) Pywikibot team, 2003-2013
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import re
import sys
from . import terminal_interface_base

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
        terminal_interface_base.UI.__init__(self)
        self.encoding = 'ascii'


class Win32CtypesUI(Win32BaseUI):

    """User interface for Win32 terminals using ctypes."""

    def __init__(self):
        Win32BaseUI.__init__(self)
        from .win32_unicode import stdin, stdout, stderr, argv
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.argv = argv
        self.encoding = 'utf-8'

    def printColorized(self, text, targetStream):
        std_out_handle = ctypes.windll.kernel32.GetStdHandle(-11)
        # Color tags might be cascaded, e.g. because of transliteration.
        # Therefore we need this stack.
        colorStack = []
        tagM = True
        while tagM:
            tagM = colorTagR.search(text)
            if tagM:
                # print the text up to the tag.
                text_before_tag = text[:tagM.start()]
                if sys.version_info[0] == 2:
                    text_before_tag = text_before_tag.encode(self.encoding, 'replace')
                targetStream.write(text_before_tag)
                newColor = tagM.group('name')
                if newColor == 'default':
                    if len(colorStack) > 0:
                        colorStack.pop()
                        if len(colorStack) > 0:
                            lastColor = colorStack[-1]
                        else:
                            lastColor = 'default'
                        ctypes.windll.kernel32.SetConsoleTextAttribute(std_out_handle, windowsColors[lastColor])
                else:
                    colorStack.append(newColor)
                    # set the new color
                    ctypes.windll.kernel32.SetConsoleTextAttribute(std_out_handle, windowsColors[newColor])
                text = text[tagM.end():]
        # print the rest of the text
        if sys.version_info[0] == 2:
            text = text.encode(self.encoding, 'replace')
        targetStream.write(text)
        # just to be sure, reset the color
        ctypes.windll.kernel32.SetConsoleTextAttribute(std_out_handle, windowsColors['default'])

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
