"""Module to daemonize the current process on POSIX systems.

This module provides a function :func:`daemonize` to turn the current
Python process into a background daemon process on POSIX-compatible
operating systems (Linux, macOS, FreeBSD) but not on not WASI Android or
iOS. It uses the standard double-fork technique to detach the process
from the controlling terminal and optionally closes or redirects
standard streams.

Double-fork diagram::

    Original process (parent)
    ├── fork()  → creates first child
    │   └─ Parent exits via os._exit() → returns control to terminal
    │
    └── First child
        ├── os.setsid()  → becomes session leader (detaches from terminal)
        ├── fork()  → creates second child (grandchild)
        │   └─ First child exits → ensures grandchild is NOT a session leader
        │
        └── Second child (Daemon)
            ├── is_daemon = True
            ├── Optionally close/redirect standard streams
            ├── Optionally change working directory
            └── # Daemon continues here
                while True:
                    do_background_work()

The "while True" loop represents the main work of the daemon:

- It runs indefinitely in the background
- Performs tasks such as monitoring files, processing data, or logging
- Everything after :func:`daemonize` runs only in the daemon process

Example usage:

    .. code-block:: Python

       import time
       from pywikibot.daemonize import daemonize

       def background_task():
           while True:
               print("Daemon is working...")
               time.sleep(5)

       daemonize()

       # This code only runs in the daemon process
       background_task()
"""
#
# (C) Pywikibot team, 2007-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import os
import platform
import stat
import sys
from contextlib import suppress
from enum import IntEnum
from pathlib import Path

from pywikibot.tools import deprecated_signature


class StandardFD(IntEnum):

    """File descriptors for standard input, output and error."""

    STDIN = 0
    STDOUT = 1
    STDERR = 2


is_daemon = False


@deprecated_signature(since='10.6.0')
def daemonize(*,
              close_fd: bool = True,
              chdir: bool = True,
              redirect_std: str | None = None) -> None:
    """Daemonize the current process.

    Only works on POSIX compatible operating systems. The process will
    fork to the background and return control to terminal.

    .. versionchanged:: 10.6
       raises NotImplementedError instead of AttributeError if daemonize
       is not available for the given platform. Parameters must be given
       as keyword-only arguments.

    .. caution::
       Do not use it in multithreaded scripts or in a subinterpreter.

    :param close_fd: Close the standard streams and replace them by
        /dev/null
    :param chdir: Change the current working directory to /
    :param redirect_std: Filename to redirect stdout and stdin to
    :raises RuntimeError: Must not be run in a subinterpreter
    :raises NotImplementedError: Daemon mode not supported on given
        platform
    """
    # platform check for MyPy
    if not hasattr(os, 'fork') or sys.platform == 'win32':
        msg = f'Daemon mode not supported on {platform.system()}'
        raise NotImplementedError(msg)

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

            # Optionally close and redirect standard streams
            if close_fd:
                for fd in StandardFD:
                    with suppress(OSError):
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

            # Optionally change working directory
            if chdir:
                os.chdir('/')

            return  # Daemon continues here

        # Write out the pid
        path = Path(Path(sys.argv[0]).name).with_suffix('.pid')
        path.write_text(str(pid), encoding='utf-8')

    # Exit to return control to the terminal
    # os._exit to prevent the cleanup to run
    os._exit(os.EX_OK)
