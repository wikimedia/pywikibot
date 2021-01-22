"""Logging tools."""
#
# (C) Pywikibot team, 2009-2020
#
# Distributed under the terms of the MIT license.
#
import logging
import os


# Logging module configuration
class RotatingFileHandler(logging.handlers.RotatingFileHandler):

    """Modified RotatingFileHandler supporting unlimited amount of backups."""

    def doRollover(self):
        """Modified naming system for logging files.

        Overwrites the default Rollover renaming by inserting the count
        number between file name root and extension. If backupCount is
        >= 1, the system will successively create new files with the
        same pathname as the base file, but with inserting ".1", ".2"
        etc. in front of the filename suffix. For example, with a
        backupCount of 5 and a base file name of "app.log", you would
        get "app.log", "app.1.log", "app.2.log", ... through to
        "app.5.log". The file being written to is always "app.log" -
        when it gets filled up, it is closed and renamed to "app.1.log",
        and if files "app.1.log", "app.2.log" etc. already exist, then
        they are renamed to "app.2.log", "app.3.log" etc. respectively.

        If backupCount is == -1 do not rotate but create new numbered
        filenames. The newest file has the highest number except some
        older numbered files where deleted and the bot was restarted.
        In this case the ordering starts from the lowest available
        (unused) number.
        """
        fmt = '{}.{}{}'

        if self.stream:
            self.stream.close()
            self.stream = None

        root, ext = os.path.splitext(self.baseFilename)

        if self.backupCount > 0:
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(fmt.format(root, i, ext))
                dfn = self.rotation_filename(fmt.format(root, i + 1, ext))
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            dfn = self.rotation_filename(fmt.format(root, 1, ext))
            if os.path.exists(dfn):
                os.remove(dfn)
            self.rotate(self.baseFilename, dfn)

        elif self.backupCount == -1:
            if not hasattr(self, '_last_no'):
                self._last_no = 1
            while True:
                fn = self.rotation_filename(fmt.format(root, self._last_no,
                                                       ext))
                self._last_no += 1
                if not os.path.exists(fn):
                    break
            self.rotate(self.baseFilename, fn)

        self.mode = 'w'

        if not self.delay:
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

        return super().format(record).rstrip()


class LoggingFormatter(logging.Formatter):

    """Format LogRecords for output to file.

    This formatter *ignores* the 'newline' key of the LogRecord, because
    every record written to a file must end with a newline, regardless of
    whether the output to the user's console does.
    """

    def formatException(self, ei):
        """Format and return the specified exception with newline."""
        return super().formatException(ei) + '\n'
