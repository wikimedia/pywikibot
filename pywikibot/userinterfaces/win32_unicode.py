"""Unicode support for stdout, stderr and argv with Python 3.5.

.. deprecated:: 7.1
   will be removed with Pywikibot 8 when Python 3.5 support is dropped.
"""
#
# (C) Pywikibot team, 2012-2022
#
##############################################
# Support for unicode in Windows cmd.exe
# Posted on Stack Overflow [1], available under CC-BY-SA 3.0 [2]
#
# Question: "Windows cmd encoding change causes Python crash" [3] by Alex [4],
# Answered [5] by David-Sarah Hopwood [6].
#
# [1] https://stackoverflow.com
# [2] https://creativecommons.org/licenses/by-sa/3.0/
# [3] https://stackoverflow.com/questions/878972
# [4] https://stackoverflow.com/users/85185
# [5] https://stackoverflow.com/a/3259271/118671
# [6] https://stackoverflow.com/users/393146
#
################################################
#
# Licensed under both CC-BY-SA and the MIT license.
#
################################################
import sys
from contextlib import suppress
from ctypes import Structure, byref
from ctypes import c_void_p as LPVOID
from ctypes import create_unicode_buffer, sizeof
from io import IOBase, UnsupportedOperation
from typing import IO

from pywikibot.backports import List, Tuple


OSWIN32 = (sys.platform == 'win32')

stdin = sys.stdin
stdout = sys.stdout
stderr = sys.stderr
argv = sys.argv

original_stderr = sys.stderr

if OSWIN32:
    from ctypes import POINTER, WINFUNCTYPE, WinError, windll
    from ctypes.wintypes import (
        BOOL,
        DWORD,
        HANDLE,
        LPWSTR,
        SHORT,
        UINT,
        ULONG,
        WCHAR,
    )

try:
    ReadConsoleW = WINFUNCTYPE(BOOL, HANDLE, LPVOID, DWORD, POINTER(DWORD),
                               LPVOID)(('ReadConsoleW', windll.kernel32))
    WriteConsoleW = WINFUNCTYPE(BOOL, HANDLE, LPWSTR, DWORD, POINTER(DWORD),
                                LPVOID)(('WriteConsoleW', windll.kernel32))
except NameError:
    ReadConsoleW = WriteConsoleW = None


class UnicodeInput(IOBase):

    """Unicode terminal input class."""

    def __init__(self, hConsole, name, bufsize: int = 1024) -> None:
        """Initialize the input stream."""
        self._hConsole = hConsole
        self.bufsize = bufsize
        self.buffer = create_unicode_buffer(bufsize)
        self.name = name
        self.encoding = 'utf-8'

    def readline(self):
        """Read one line from the input."""
        maxnum = DWORD(self.bufsize - 1)
        numrecv = DWORD(0)
        result = ReadConsoleW(self._hConsole, self.buffer, maxnum,
                              byref(numrecv), None)
        if not result:
            raise Exception('stdin failure')
        return self.buffer.value[:numrecv.value]


class UnicodeOutput(IOBase):

    """Unicode terminal output class."""

    def __init__(self, hConsole, stream, fileno, name) -> None:
        """Initialize the output stream."""
        self._hConsole = hConsole
        self._stream = stream
        self._fileno = fileno
        self.softspace = False
        self.mode = 'w'
        self.encoding = 'utf-8'
        self.name = name
        self.flush()

    def fileno(self):
        """Return the fileno."""
        return self._fileno

    def flush(self):
        """Flush the stream."""
        if self._hConsole is None:
            try:
                self._stream.flush()
            except Exception as e:
                _complain('{}.flush: {!r} from {!r}'
                          .format(self.name, e, self._stream))
                raise

    def write(self, text):
        """Write the text to the output."""
        try:
            if self._hConsole is None:
                self._stream.write(text)
            else:
                if not isinstance(text, str):
                    text = bytes(text).decode('utf-8')
                remaining = len(text)
                while remaining > 0:
                    n = DWORD(0)
                    # There is a shorter-than-documented limitation on the
                    # length of the string passed to WriteConsoleW (see
                    # <https://tahoe-lafs.org/trac/tahoe-lafs/ticket/1232>.
                    retval = WriteConsoleW(self._hConsole, text,
                                           min(remaining, 10000),
                                           byref(n), None)
                    if 0 in (retval, n.value):
                        msg = 'WriteConsoleW returned {!r}, n.value = {!r}' \
                              .format(retval, n.value)
                        raise OSError(msg)
                    remaining -= n.value
                    if remaining == 0:
                        break
                    text = text[n.value:]
        except Exception as e:
            _complain('{}.write: {!r}'.format(self.name, e))
            raise

    def writelines(self, lines):
        """Write a list of lines by using write."""
        try:
            for line in lines:
                self.write(line)
        except Exception as e:
            _complain('{}.writelines: {!r}'.format(self.name, e))
            raise

    def isatty(self):
        """Return True if the stream is interactive."""
        return self._hConsole is not None


def old_fileno(std_name):
    """Return the fileno or None if that doesn't work."""
    # some environments like IDLE don't support the fileno operation
    # handle those like std streams which don't have fileno at all
    std = getattr(sys, 'std{}'.format(std_name))
    if hasattr(std, 'fileno'):
        with suppress(UnsupportedOperation):
            return std.fileno()
    return None


# If any exception occurs in this code, try to print it on stderr,
# which makes for frustrating debugging if stderr is directed to our wrapper.
# So be paranoid about catching errors and reporting them to original_stderr,
# so that we can at least see them.
def _complain(message) -> None:
    print(isinstance(message, str) and message or repr(message),
          file=original_stderr)


def force_truetype_console(h_stdout) -> None:
    """Force the console to use a TrueType font (Vista+)."""
    TMPF_TRUETYPE = 0x04
    LF_FACESIZE = 32

    class COORD(Structure):
        _fields_ = [('X', SHORT),
                    ('Y', SHORT)]

    class CONSOLE_FONT_INFOEX(Structure):
        _fields_ = [('cbSize', ULONG),
                    ('nFont', DWORD),
                    ('dwFontSize', COORD),
                    ('FontFamily', UINT),
                    ('FontWeight', UINT),
                    ('FaceName', WCHAR * LF_FACESIZE)]

    try:
        GetCurrentConsoleFontEx = WINFUNCTYPE(
            BOOL,
            HANDLE,  # hConsoleOutput
            BOOL,    # bMaximumWindow
            POINTER(CONSOLE_FONT_INFOEX),  # lpConsoleCurrentFontEx
        )(('GetCurrentConsoleFontEx', windll.kernel32))

        SetCurrentConsoleFontEx = WINFUNCTYPE(
            BOOL,
            HANDLE,  # hConsoleOutput
            BOOL,    # bMaximumWindow
            POINTER(CONSOLE_FONT_INFOEX),  # lpConsoleCurrentFontEx
        )(('SetCurrentConsoleFontEx', windll.kernel32))
    except AttributeError:
        # pre Windows Vista. Return without doing anything.
        return

    current_font = CONSOLE_FONT_INFOEX()
    current_font.cbSize = sizeof(CONSOLE_FONT_INFOEX)

    if not GetCurrentConsoleFontEx(h_stdout, True, byref(current_font)):
        WinError()

    truetype_font = (current_font.FontFamily & TMPF_TRUETYPE)

    if not truetype_font:
        new_font = CONSOLE_FONT_INFOEX()
        new_font.cbSize = sizeof(CONSOLE_FONT_INFOEX)
        new_font.FaceName = 'Lucida Console'

        if not SetCurrentConsoleFontEx(h_stdout, True, byref(new_font)):
            WinError()


def get_unicode_console() -> Tuple[IO, IO, IO, List[str]]:
    """
    Get Unicode console objects.

    :return: stdin, stdout, stderr, argv
    """
    # Make Unicode console output work independently of the current code page.
    # This also fixes https://bugs.python.org/issue1602
    # Credit to Michael Kaplan
    # http://blogs.msdn.com/b/michkap/archive/2010/04/07/9989346.aspx
    # and TZOmegaTZIOY
    # https://stackoverflow.com/questions/878972/windows-cmd-encoding-change-causes-python-crash/1432462#1432462

    global stdin, stdout, stderr

    if not OSWIN32:
        return stdin, stdout, stderr, argv

    try:
        # <https://msdn.microsoft.com/en-us/library/ms683231(VS.85).aspx>
        # HANDLE WINAPI GetStdHandle(DWORD nStdHandle);
        # returns INVALID_HANDLE_VALUE, NULL, or a valid handle
        #
        # <https://msdn.microsoft.com/en-us/library/aa364960(VS.85).aspx>
        # DWORD WINAPI GetFileType(DWORD hFile);
        #
        # <https://msdn.microsoft.com/en-us/library/ms683167(VS.85).aspx>
        # BOOL WINAPI GetConsoleMode(HANDLE hConsole, LPDWORD lpMode);

        GetStdHandle = WINFUNCTYPE(HANDLE, DWORD)(('GetStdHandle',
                                                   windll.kernel32))
        STD_INPUT_HANDLE = DWORD(-10)
        STD_OUTPUT_HANDLE = DWORD(-11)
        STD_ERROR_HANDLE = DWORD(-12)
        GetFileType = WINFUNCTYPE(DWORD, DWORD)(('GetFileType',
                                                 windll.kernel32))
        FILE_TYPE_CHAR = 0x0002
        FILE_TYPE_REMOTE = 0x8000
        GetConsoleMode = (WINFUNCTYPE(BOOL, HANDLE, POINTER(DWORD))
                          (('GetConsoleMode', windll.kernel32)))
        INVALID_HANDLE_VALUE = DWORD(-1).value

        def not_a_console(handle):
            """Return whether the handle is not to a console."""
            if handle == INVALID_HANDLE_VALUE or handle is None:
                return True
            return ((GetFileType(handle) & ~FILE_TYPE_REMOTE) != FILE_TYPE_CHAR
                    or GetConsoleMode(handle, byref(DWORD())) == 0)

        old_stdin_fileno = old_fileno('in')
        old_stdout_fileno = old_fileno('out')
        old_stderr_fileno = old_fileno('err')

        STDIN_FILENO = 0
        STDOUT_FILENO = 1
        STDERR_FILENO = 2
        real_stdin = (old_stdin_fileno == STDIN_FILENO)
        real_stdout = (old_stdout_fileno == STDOUT_FILENO)
        real_stderr = (old_stderr_fileno == STDERR_FILENO)

        if real_stdin:
            hStdin = GetStdHandle(STD_INPUT_HANDLE)
            if not_a_console(hStdin):
                real_stdin = False

        if real_stdout:
            hStdout = GetStdHandle(STD_OUTPUT_HANDLE)
            force_truetype_console(hStdout)
            if not_a_console(hStdout):
                real_stdout = False

        if real_stderr:
            hStderr = GetStdHandle(STD_ERROR_HANDLE)
            force_truetype_console(hStderr)
            if not_a_console(hStderr):
                real_stderr = False

        if real_stdout or real_stderr:
            if real_stdin:
                stdin = UnicodeInput(hStdin, name='<Unicode console stdin>')

            if real_stdout:
                stdout = UnicodeOutput(hStdout, sys.stdout, STDOUT_FILENO,
                                       '<Unicode console stdout>')
            else:
                stdout = UnicodeOutput(None, sys.stdout, old_stdout_fileno,
                                       '<Unicode redirected stdout>')

            if real_stderr:
                stderr = UnicodeOutput(hStderr, sys.stderr, STDERR_FILENO,
                                       '<Unicode console stderr>')
            else:
                stderr = UnicodeOutput(None, sys.stderr, old_stderr_fileno,
                                       '<Unicode redirected stderr>')
    except Exception as e:
        _complain('exception {!r} while fixing up sys.stdout and sys.stderr'
                  .format(e))

    return stdin, stdout, stderr, argv
