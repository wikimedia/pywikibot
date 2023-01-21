"""User interface for Win32 terminals."""
#
# (C) Pywikibot team, 2003-2022
#
# Distributed under the terms of the MIT license.
#
import ctypes

from pywikibot.userinterfaces import terminal_interface_base


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


class Win32UI(terminal_interface_base.UI):

    """User interface for Win32 terminals."""

    def support_color(self, target_stream):
        """Return whether the target stream supports actually color."""
        return target_stream.isatty()

    def encounter_color(self, color,
                        target_stream) -> None:  # pragma: no cover
        """Set the new color."""
        fg, bg = self.divide_color(color)
        windows_color = windowsColors[fg]
        # Merge foreground/backgroung color if needed.
        if bg is not None:
            windows_color = windowsColors[bg] << 4 | windows_color

        if target_stream == self.stdin:
            addr = -10
        elif target_stream == self.stdout:
            addr = -11
        elif target_stream == self.stderr:
            addr = -12
        else:
            super().encounter_color(color, target_stream)

        from ctypes.wintypes import DWORD, HANDLE
        get_handle = ctypes.WINFUNCTYPE(HANDLE, DWORD)(
            ('GetStdHandle', ctypes.windll.kernel32))
        handle = get_handle(DWORD(addr))
        ctypes.windll.kernel32.SetConsoleTextAttribute(handle, windows_color)

    def _raw_input(self):  # pragma: no cover
        data = self.stdin.readline()
        if '\x1a' in data:
            raise EOFError()
        return data.strip()
