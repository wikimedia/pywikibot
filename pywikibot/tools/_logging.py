# -*- coding: utf-8 -*-
"""Logging tools."""
#
# (C) Pywikibot team, 2009-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import logging
import os

from pywikibot.tools import PY2


# Logging module configuration
class RotatingFileHandler(logging.handlers.RotatingFileHandler):

    """Modified RotatingFileHandler supporting unlimited amount of backups."""

    def doRollover(self):
        """
        Modified naming system for logging files.

        Overwrites the default Rollover renaming by inserting the count number
        between file name root and extension. If backupCount is >= 1, the
        system will successively create new files with the same pathname as the
        base file, but with inserting ".1", ".2" etc. in front of the filename
        suffix. For example, with a backupCount of 5 and a base file name of
        "app.log", you would get "app.log", "app.1.log", "app.2.log", ...
        through to "app.5.log". The file being written to is always "app.log" -
        when it gets filled up, it is closed and renamed to "app.1.log", and if
        files "app.1.log", "app.2.log" etc. already exist, then they are
        renamed to "app.2.log", "app.3.log" etc. respectively.
        If backupCount is == -1 do not rotate but create new numbered
        filenames. The newest file has the highest number except some older
        numbered files where deleted and the bot was restarted. In this case
        the ordering starts from the lowest available (unused) number.
        """
        if self.stream:
            self.stream.close()
            self.stream = None
        root, ext = os.path.splitext(self.baseFilename)
        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = '%s.%d%s' % (root, i, ext)
                dfn = '%s.%d%s' % (root, i + 1, ext)
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = '%s.1%s' % (root, ext)
            if os.path.exists(dfn):
                os.remove(dfn)
            os.rename(self.baseFilename, dfn)
        elif self.backupCount == -1:
            if not hasattr(self, '_lastNo'):
                self._lastNo = 1
            while True:
                fn = '%s.%d%s' % (root, self._lastNo, ext)
                self._lastNo += 1
                if not os.path.exists(fn):
                    break
            os.rename(self.baseFilename, fn)
        self.mode = 'w'
        self.stream = self._open()

    def format(self, record):
        """Strip trailing newlines before outputting text to file."""
        # Warnings captured from the warnings system are not processed by
        # logoutput(), so the 'context' variables are missing.
        if record.name == 'py.warnings' \
           and 'caller_file' not in record.__dict__:
            assert len(record.args) == 1, \
                'Arguments for record is not correctly set'
            msg = record.args[0]

            record.__dict__['caller_file'] = record.pathname
            record.__dict__['caller_name'] = record.module
            record.__dict__['caller_line'] = record.lineno

            record.args = (msg,)

        text = logging.handlers.RotatingFileHandler.format(self, record)
        return text.rstrip()


class LoggingFormatter(logging.Formatter):

    """Format LogRecords for output to file.

    This formatter *ignores* the 'newline' key of the LogRecord, because
    every record written to a file must end with a newline, regardless of
    whether the output to the user's console does.

    """

    def __init__(self, fmt=None, datefmt=None, encoding=None):
        """Initializer with additional encoding parameter."""
        logging.Formatter.__init__(self, fmt, datefmt)
        self._encoding = encoding

    def formatException(self, ei):
        r"""
        Convert exception trace to unicode if necessary.

        Make sure that the exception trace is converted to unicode.

        L{exceptions.Error} traces are encoded in our console encoding, which
        is needed for plainly printing them. However, when logging them
        using logging.exception, the Python logging module will try to use
        these traces, and it will fail if they are console encoded strings.

        Formatter.formatException also strips the trailing \n, which we need.
        """
        exception_string = logging.Formatter.formatException(self, ei)

        if PY2 and isinstance(exception_string, bytes):
            return exception_string.decode(self._encoding) + '\n'
        else:
            return exception_string + '\n'
