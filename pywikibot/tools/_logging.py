"""Logging tools."""
#
# (C) Pywikibot team, 2009-2022
#
# Distributed under the terms of the MIT license.
#
import logging

from pywikibot.userinterfaces.terminal_interface_base import new_colorTagR


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

            record.__dict__['caller_file'] = record.filename
            record.__dict__['caller_name'] = record.module
            record.__dict__['caller_line'] = record.lineno

            record.args = (msg,)

        # remove color tags
        if record.msg and isinstance(record.msg, str):
            record.msg = new_colorTagR.sub('', record.msg)

        return super().format(record).rstrip()
