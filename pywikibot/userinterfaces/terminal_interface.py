# -*- coding: utf-8 -*-
#
# (C) Pywikipedia bot team, 2003-2012
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import sys

if sys.platform == 'win32':
    from terminal_interface_win32 import Win32UI as UI
else:
    from terminal_interface_unix import UnixUI as UI
