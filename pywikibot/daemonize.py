# -*- coding: utf-8  -*-
"""Module to daemonize the current process on Unix."""
#
# (C) Pywikibot team, 2007-2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import os
import sys
import codecs

is_daemon = False


def daemonize(close_fd=True, chdir=True, write_pid=False, redirect_std=None):
    """
    Daemonize the current process.

    Only works on POSIX compatible operating systems.
    The process will fork to the background and return control to terminal.

    @param close_fd: Close the standard streams and replace them by /dev/null
    @type close_fd: bool
    @param chdir: Change the current working directory to /
    @type chdir: bool
    @param write_pid: Write the pid to sys.argv[0] + '.pid'
    @type write_pid: bool
    @param redirect_std: Filename to redirect stdout and stdin to
    @type redirect_std: str
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
                    os.open(redirect_std,
                            os.O_WRONLY | os.O_APPEND | os.O_CREAT)
                else:
                    os.dup2(0, 1)
                os.dup2(1, 2)
            if chdir:
                os.chdir('/')
            return
        else:
            # Write out the pid
            path = os.path.basename(sys.argv[0]) + '.pid'
            with codecs.open(path, 'w', 'utf-8') as f:
                f.write(str(pid))
            os._exit(0)
    else:
        # Exit to return control to the terminal
        # os._exit to prevent the cleanup to run
        os._exit(0)
