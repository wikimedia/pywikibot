#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Text editor class for your favourite editor."""
#
# (C) Pywikibot team, 2004-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import codecs
import os
import subprocess
import tempfile

from sys import platform

import pywikibot

from pywikibot import config
from pywikibot.tools import deprecated

try:
    from pywikibot.userinterfaces import gui
except ImportError as e:
    gui = e


class TextEditor(object):

    """Text editor."""

    def _command(self, file_name, text, jump_index=None):
        """Return editor selected in user-config.py."""
        if jump_index:
            # Some editors make it possible to mark occurrences of substrings,
            # or to jump to the line of the first occurrence.
            # TODO: Find a better solution than hardcoding these, e.g. a config
            # option.
            line = text[:jump_index].count('\n')
            column = jump_index - (text[:jump_index].rfind('\n') + 1)
        else:
            line = column = 0
        # Linux editors. We use startswith() because some users might use
        # parameters.
        if config.editor.startswith('kate'):
            command = ['-l', '%i' % (line + 1), '-c', '%i' % (column + 1)]
        elif config.editor.startswith('gedit'):
            command = ['+%i' % (line + 1)]  # seems not to support columns
        elif config.editor.startswith('emacs'):
            command = ['+%i' % (line + 1)]  # seems not to support columns
        elif config.editor.startswith('jedit'):
            command = ['+line:%i' % (line + 1)]  # seems not to support columns
        elif config.editor.startswith('vim'):
            command = ['+%i' % (line + 1)]  # seems not to support columns
        elif config.editor.startswith('nano'):
            command = ['+%i,%i' % (line + 1, column + 1)]
        # Windows editors
        elif config.editor.lower().endswith('notepad++.exe'):
            command = ['-n%i' % (line + 1)]  # seems not to support columns
        else:
            command = []

        # See T102465 for problems relating to using config.editor unparsed.
        command = [config.editor] + command + [file_name]
        pywikibot.log('Running editor: %s' % TextEditor._concat(command))
        return command

    @staticmethod
    def _concat(command):
        return ' '.join("'{0}'".format(part) if ' ' in part else part
                        for part in command)

    @deprecated('_command (should not be used from the outside)',
                since='20150111')
    def command(self, tempFilename, text, jumpIndex=None):
        """Return editor selected in user-config.py."""
        return TextEditor._concat(self._command(tempFilename, text, jumpIndex))

    def edit(self, text, jumpIndex=None, highlight=None):
        """
        Call the editor and thus allows the user to change the text.

        Halts the thread's operation until the editor is closed.

        @param text: the text to be edited
        @type text: str
        @param jumpIndex: position at which to put the caret
        @type jumpIndex: int
        @param highlight: each occurrence of this substring will be highlighted
        @type highlight: str
        @return: the modified text, or None if the user didn't save the text
            file in his text editor
        @rtype: str or None
        """
        if config.editor:
            handle, tempFilename = tempfile.mkstemp()
            tempFilename = '%s.%s' % (tempFilename,
                                      config.editor_filename_extension)
            try:
                with codecs.open(tempFilename, 'w',
                                 encoding=config.editor_encoding) as tempFile:
                    tempFile.write(text)
                creationDate = os.stat(tempFilename).st_mtime
                cmd = self._command(tempFilename, text, jumpIndex)
                subprocess.call(cmd, shell=platform == 'win32')
                lastChangeDate = os.stat(tempFilename).st_mtime
                if lastChangeDate == creationDate:
                    # Nothing changed
                    return None
                else:
                    with codecs.open(
                        tempFilename, 'r', encoding=config.editor_encoding
                    ) as temp_file:
                        newcontent = temp_file.read()
                    return newcontent
            finally:
                os.close(handle)
                os.unlink(tempFilename)

        if isinstance(gui, ImportError):
            raise ImportError(
                'Could not load GUI modules: %s\nNo editor available.\n'
                'Set your favourite editor in user-config.py "editor", '
                'or install python packages tkinter and idlelib, which '
                'are typically part of Python but may be packaged separately '
                'on your platform.\n' % gui)

        return pywikibot.ui.editText(
            text, jumpIndex=jumpIndex, highlight=highlight)
