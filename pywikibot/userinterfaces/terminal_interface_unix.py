# -*- coding: utf-8 -*-
"""User interface for unix terminals."""
#
# (C) Pywikibot team, 2003-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import re

from pywikibot.tools import PY2

from pywikibot.userinterfaces import terminal_interface_base

unixColors = {
    'default':     chr(27) + '[0m',   # Unix end tag to switch back to default
    'black':       chr(27) + '[30m',  # Black start tag
    'red':         chr(27) + '[31m',  # Red start tag
    'green':       chr(27) + '[32m',  # Green start tag
    'yellow':      chr(27) + '[33m',  # Yellow start tag
    'blue':        chr(27) + '[34m',  # Blue start tag
    'purple':      chr(27) + '[35m',  # Purple start tag (Magenta)
    'aqua':        chr(27) + '[36m',  # Aqua start tag (Cyan)
    'lightgray':   chr(27) + '[37m',  # Light gray start tag (White)
    'gray':        chr(27) + '[90m',  # Gray start tag
    'lightred':    chr(27) + '[91m',  # Light Red tag
    'lightgreen':  chr(27) + '[92m',  # Light Green tag
    'lightyellow': chr(27) + '[93m',  # Light Yellow tag
    'lightblue':   chr(27) + '[94m',  # Light Blue tag
    'lightpurple': chr(27) + '[95m',  # Light Purple tag (Magenta)
    'lightaqua':   chr(27) + '[96m',  # Light Aqua tag (Cyan)
    'white':       chr(27) + '[97m',  # White start tag (Bright White)
}


class UnixUI(terminal_interface_base.UI):

    """User interface for unix terminals."""

    def support_color(self, target_stream):
        """Return that the target stream supports colors."""
        return True

    def make_unix_bg_color(self, color):
        """Obtain background color from foreground color."""
        code = re.search(r'(?<=\[)\d+', color).group()
        return chr(27) + '[' + str(int(code) + 10) + 'm'

    def encounter_color(self, color, target_stream):
        """Write the unix color directly to the stream."""
        fg, bg = self.divide_color(color)
        fg = unixColors[fg]
        self._write(fg, target_stream)
        if bg is not None:
            bg = unixColors[bg]
            self._write(self.make_unix_bg_color(bg), target_stream)

    def _write(self, text, target_stream):
        """Optionally encode and write the text to the target stream."""
        if PY2:
            encoding = getattr(target_stream, 'encoding', None)
            if encoding:
                text = text.encode(encoding, 'replace').decode(encoding)
            else:
                text = text.encode(self.encoding, 'replace')
        target_stream.write(text)
