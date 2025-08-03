"""Module to daemonize the current process on Unix."""
#
# (C) Pywikibot team, 2007-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import os
import stat
import sys
from enum import IntEnum
from pathlib import Path


class StandardFD(IntEnum):

    """File descriptors for standard input, output and error."""

    STDIN = 0
    STDOUT = 1
    STDERR = 2


is_daemon = False


def daemonize(close_fd: bool = True,
              chdir: bool = True,
              redirect_std: str | None = None) -> None:
    """Daemonize the current process.

    Only works on POSIX compatible operating systems. The process will
    fork to the background and return control to terminal.

    :param close_fd: Close the standard streams and replace them by
        /dev/null
    :param chdir: Change the current working directory to /
    :param redirect_std: Filename to redirect stdout and stdin to
    """
    # Fork away
    if not os.fork():
        # Become session leader
        os.setsid()
        # Fork again to prevent the process from acquiring a
        # controlling terminal
        pid = os.fork()

        if not pid:
            global is_daemon
            is_daemon = True

            if close_fd:
                for fd in StandardFD:
                    os.close(fd)
                os.open('/dev/null', os.O_RDWR)

                if redirect_std:
                    # R/W mode without execute flags
                    mode = (stat.S_IRUSR | stat.S_IWUSR
                            | stat.S_IRGRP | stat.S_IWGRP
                            | stat.S_IROTH | stat.S_IWOTH)
                    os.open(redirect_std,
                            os.O_WRONLY | os.O_APPEND | os.O_CREAT,
                            mode)
                else:
                    os.dup2(StandardFD.STDIN, StandardFD.STDOUT)
                os.dup2(StandardFD.STDOUT, StandardFD.STDERR)

            if chdir:
                os.chdir('/')
            return

        # Write out the pid
        path = Path(Path(sys.argv[0]).name).with_suffix('.pid')
        path.write_text(str(pid), encoding='utf-8')

    # Exit to return control to the terminal
    # os._exit to prevent the cleanup to run
    os._exit(os.EX_OK)
