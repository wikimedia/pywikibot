# -*- coding: utf-8  -*-
"""CGI user interface."""
from __future__ import absolute_import, unicode_literals

import sys


class UI(object):

    """CGI user interface."""

    def output(self, text, colors=None, newline=True, toStdout=False):
        """Output text to CGI stream if toStdout is True."""
        if not toStdout:
            return
        sys.stdout.write(text.encode('UTF-8', 'replace'))

    def input(self, question, colors=None):
        """Output question to CGI stream."""
        self.output(question + ' ', newline=False, toStdout=True)
