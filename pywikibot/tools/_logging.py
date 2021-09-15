"""Logging tools."""
#
# (C) Pywikibot team, 2009-2021
#
# Distributed under the terms of the MIT license.
#
import logging


class LoggingFormatter(logging.Formatter):

    """Format LogRecords for output to file."""

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
