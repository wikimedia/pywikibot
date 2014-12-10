#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Text editor class for your favourite editor."""

#
# (C) Gerrit Holl, 2004
# (C) Pywikibot team, 2004-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import sys
import os
import tempfile
import codecs
import pywikibot
from pywikibot import config


class TextEditor(object):

    """Text editor."""

    def command(self, tempFilename, text, jumpIndex=None):
        """Return editor selected in user-config.py."""
        command = config.editor
        if jumpIndex:
            # Some editors make it possible to mark occurrences of substrings,
            # or to jump to the line of the first occurrence.
            # TODO: Find a better solution than hardcoding these, e.g. a config
            # option.
            line = text[:jumpIndex].count('\n')
            column = jumpIndex - (text[:jumpIndex].rfind('\n') + 1)
        else:
            line = column = 0
        # Linux editors. We use startswith() because some users might use
        # parameters.
        if config.editor.startswith('kate'):
            command += " -l %i -c %i" % (line + 1, column + 1)
        elif config.editor.startswith('gedit'):
            command += " +%i" % (line + 1)  # seems not to support columns
        elif config.editor.startswith('emacs'):
            command += " +%i" % (line + 1)  # seems not to support columns
        elif config.editor.startswith('jedit'):
            command += " +line:%i" % (line + 1)  # seems not to support columns
        elif config.editor.startswith('vim'):
            command += " +%i" % (line + 1)  # seems not to support columns
        elif config.editor.startswith('nano'):
            command += " +%i,%i" % (line + 1, column + 1)
        # Windows editors
        elif config.editor.lower().endswith('notepad++.exe'):
            command += " -n%i" % (line + 1)  # seems not to support columns

        command += ' %s' % tempFilename
        pywikibot.log(u'Running editor: %s' % command)
        return command

    def convertLinebreaks(self, text):
        """Convert line-breaks."""
        if sys.platform == 'win32':
            return text.replace('\r\n', '\n')
        # TODO: Mac OS handling
        return text

    def restoreLinebreaks(self, text):
        """Restore line-breaks."""
        if text is None:
            return
        if sys.platform == 'win32':
            return text.replace('\n', '\r\n')
        # TODO: Mac OS handling
        return text

    def edit(self, text, jumpIndex=None, highlight=None):
        """
        Call the editor and thus allows the user to change the text.

        Halts the thread's operation until the editor is closed.

        @param text: the text to be edited
        @type text: unicode
        @param jumpIndex: position at which to put the caret
        @type jumpIndex: int
        @param highlight: each occurrence of this substring will be highlighted
        @type highlight: unicode
        @return: the modified text, or None if the user didn't save the text
            file in his text editor
        @rtype: unicode or None
        """
        text = self.convertLinebreaks(text)
        if config.editor:
            tempFilename = '%s.%s' % (tempfile.mktemp(),
                                      config.editor_filename_extension)
            with codecs.open(tempFilename, 'w',
                             encoding=config.editor_encoding) as tempFile:
                tempFile.write(text)
            creationDate = os.stat(tempFilename).st_mtime
            command = self.command(tempFilename, text, jumpIndex)
            os.system(command)
            lastChangeDate = os.stat(tempFilename).st_mtime
            if lastChangeDate == creationDate:
                # Nothing changed
                return None
            else:
                with codecs.open(tempFilename, 'r',
                                 encoding=config.editor_encoding) as temp_file:
                    newcontent = temp_file.read()
                os.unlink(tempFilename)
                return self.restoreLinebreaks(newcontent)

        try:
            import gui  # noqa
        except ImportError as e:
            raise pywikibot.Error(
                'Could not load GUI modules: %s\nNo editor available.\n'
                'Set your favourite editor in user-config.py "editor", '
                'or install python packages tkinter and idlelib, which '
                'are typically part of Python but may be packaged separately '
                'on your platform.\n' % e)

        return self.restoreLinebreaks(
            pywikibot.ui.editText(
                text,
                jumpIndex=jumpIndex,
                highlight=highlight))
