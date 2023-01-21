"""Module to daemonize the current process on Unix."""
#
# (C) Pywikibot team, 2007-2022
#
# Distributed under the terms of the MIT license.
#
import os
import stat
import sys
from pathlib import Path
from typing import Optional


is_daemon = False


def daemonize(close_fd: bool = True,
              chdir: bool = True,
              redirect_std: Optional[str] = None) -> None:
    """Daemonize the current process.

    Only works on POSIX compatible operating systems.
    The process will fork to the background and return control to terminal.

    :param close_fd: Close the standard streams and replace them by /dev/null
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
                os.close(0)
                os.close(1)
                os.close(2)
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
                    os.dup2(0, 1)
                os.dup2(1, 2)
            if chdir:
                os.chdir('/')
            return

        # Write out the pid
        path = Path(Path(sys.argv[0]).name).with_suffix('.pid')
        path.write_text(str(pid), encoding='uft-8')

    # Exit to return control to the terminal
    # os._exit to prevent the cleanup to run
    os._exit(os.EX_OK)
