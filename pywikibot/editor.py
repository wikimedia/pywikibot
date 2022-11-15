"""Text editor class for your favourite editor."""
#
# (C) Pywikibot team, 2004-2022
#
# Distributed under the terms of the MIT license.
#
import os
import subprocess
import tempfile
from pathlib import Path
from sys import platform
from textwrap import fill
from typing import Optional

import pywikibot
from pywikibot import config
from pywikibot.backports import List, Sequence


try:
    from pywikibot.userinterfaces import gui  # noqa
    GUI_ERROR = None
except ImportError as e:
    GUI_ERROR = e


OSWIN32 = platform == 'win32'
if OSWIN32:
    import winreg


class TextEditor:

    """Text editor.

    .. versionchanged:: 8.0
       Editor detection functions were moved from :mod:`config`.
    """

    def __init__(self):
        """Setup external Editor."""
        self.editor: str
        if config.editor is True:
            self.editor = ''
        elif config.editor is False:
            self.editor = 'break' if OSWIN32 else 'true'
        elif config.editor is None:
            self.editor = os.environ.get('EDITOR', '')
            if OSWIN32 and not self.editor:
                self.editor = self._detect_win32_editor()
        else:
            self.editor = config.editor

    def _command(self, file_name: str, text: str,
                 jump_index: Optional[int] = None) -> List[str]:
        """Return command of editor selected in user config file."""
        if jump_index:
            # Some editors make it possible to mark occurrences of substrings,
            # or to jump to the line of the first occurrence.
            # TODO: Find a better solution than hardcoding these, e.g. a config
            # option.
            line = text[:jump_index].count('\n')
            column = jump_index - (text[:jump_index].rfind('\n') + 1)
        else:
            line = column = 0

        # Linux editors. We use startswith() because some users might use
        # parameters.
        if self.editor.startswith('kate'):
            command = ['-l', str(line + 1), '-c', str(column + 1)]
        elif self.editor.startswith(('gedit', 'emacs')):
            command = [f'+{line + 1}']  # columns seem unsupported
        elif self.editor.startswith('jedit'):
            command = [f'+line:{line + 1}']  # columns seem unsupported
        elif self.editor.startswith('vim'):
            command = [f'+{line + 1}']  # columns seem unsupported
        elif self.editor.startswith('nano'):
            command = [f'+{line + 1},{column + 1}']
        # Windows editors
        elif self.editor.lower().endswith('notepad++.exe'):
            command = [f'-n{line + 1}']  # seems not to support columns
        else:
            command = []

        # See T102465 for problems relating to using self.editor unparsed.
        command = [self.editor] + command + [file_name]
        pywikibot.log(f'Running editor: {self._concat(command)}')
        return command

    @staticmethod
    def _concat(command: Sequence[str]) -> str:
        return ' '.join(f'{part!r}' if ' ' in part else part
                        for part in command)

    def edit(self, text: str, jumpIndex: Optional[int] = None,
             highlight: Optional[str] = None) -> Optional[str]:
        """
        Call the editor and thus allows the user to change the text.

        Halts the thread's operation until the editor is closed.

        :param text: the text to be edited
        :param jumpIndex: position at which to put the caret
        :param highlight: each occurrence of this substring will be highlighted
        :return: the modified text, or None if the user didn't save the text
            file in his text editor
        """
        if self.editor:
            handle, filename = tempfile.mkstemp(
                suffix=f'.{config.editor_filename_extension}', text=True)
            path = Path(filename)

            try:
                encoding = config.editor_encoding
                path.write_text(text, encoding=encoding)

                creation_date = path.stat().st_mtime
                cmd = self._command(filename, text, jumpIndex)
                subprocess.run(cmd, shell=platform == 'win32', check=True)
                last_change_date = path.stat().st_mtime

                if last_change_date == creation_date:
                    return None  # Nothing changed

                return path.read_text(encoding=encoding)

            finally:
                os.close(handle)
                os.unlink(path)

        if GUI_ERROR:
            raise ImportError(fill(
                f'Could not load GUI modules: {GUI_ERROR}. No editor'
                ' available. Set your favourite editor in user-config.py'
                ' "editor", or install python packages tkinter and idlelib,'
                ' which are typically part of Python but may be packaged'
                ' separately on your platform.') + '\n')

        assert pywikibot.ui is not None
        return pywikibot.ui.editText(text, jumpIndex=jumpIndex,
                                     highlight=highlight)

    @staticmethod
    def _win32_extension_command(extension: str) -> Optional[str]:
        """Get the command from the Win32 registry for an extension."""
        fileexts_key = \
            r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts'
        key_name = fr'{fileexts_key}\.{extension}\OpenWithProgids'
        try:
            key1 = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_name)
            _prog_id = winreg.EnumValue(key1, 0)[0]
            _key2 = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT,
                                   fr'{_prog_id}\shell\open\command')
            _cmd = winreg.QueryValueEx(_key2, '')[0]
            # See T102465 for issues relating to using this value.
            cmd = _cmd
            if cmd.find('%1'):
                cmd = cmd[:cmd.find('%1')]
                # Remove any trailing character, which should be a quote or
                # space and then remove all whitespace.
                return cmd[:-1].strip()
        except OSError as e:
            # Catch any key lookup errors
            pywikibot.info(f'Unable to detect program for file extension '
                           f'{extension!r}: {e!r}')
        return None

    @staticmethod
    def _detect_win32_editor() -> str:
        """Detect the best Win32 editor."""
        # Notepad is even worse than our Tkinter editor.
        unusable_exes = ['notepad.exe',
                         'py.exe',
                         'pyw.exe',
                         'python.exe',
                         'pythonw.exe']

        for ext in ['py', 'txt']:
            editor = TextEditor._win32_extension_command(ext)
            if editor:
                for unusable in unusable_exes:
                    if unusable in editor.lower():
                        break
                else:
                    if set(editor) & set('\a\b\f\n\r\t\v'):
                        # single character string literals from
                        # https://docs.python.org/3/reference/lexical_analysis.html#string-and-bytes-literals
                        # encode('unicode-escape') also changes Unicode
                        # characters
                        pywikibot.warning(fill(
                            'The editor path contains probably invalid '
                            'escaped characters. Make sure to use a '
                            'raw-string (r"..." or r\'...\'), forward slashes '
                            'as a path delimiter or to escape the normal path '
                            'delimiter.'))
                    return editor
        return ''
