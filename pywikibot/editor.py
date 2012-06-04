#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Text editor class for your favourite editor.
"""

#
# (C) Gerrit Holl 2004
# (C) Pywikipedia team, 2004-2012
#
__version__ = "$Id$"
#
# Distributed under the terms of the MIT license.
#

__metaclass__ = type
import sys
import os
import tempfile
import pywikibot
from pywikibot import config2 as config


class TextEditor(object):
    def __init__(self):
        pass

    def command(self, tempFilename, text, jumpIndex = None):
        command = config.editor
        if jumpIndex:
            # Some editors make it possible to mark occurences of substrings,
            # or to jump to the line of the first occurence.
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
            command += " +%i" % (line + 1) # seems not to support columns
        elif config.editor.startswith('emacs'):
            command += " +%i" % (line + 1) # seems not to support columns
        elif config.editor.startswith('jedit'):
            command += " +line:%i" % (line + 1) # seems not to support columns
        elif config.editor.startswith('vim'):
            command += " +%i" % (line + 1) # seems not to support columns
        elif config.editor.startswith('nano'):
            command += " +%i,%i" % (line + 1, column + 1)
        # Windows editors
        elif config.editor.lower().endswith('notepad++.exe'):
            command += " -n%i" % (line + 1) # seems not to support columns

        command += ' %s' % tempFilename
        #print command
        return command

    def convertLinebreaks(self, text):
        if sys.platform=='win32':
            return text.replace('\r\n', '\n')
        # TODO: Mac OS handling
        return text

    def restoreLinebreaks(self, text):
        if text is None:
            return None
        if sys.platform=='win32':
            return text.replace('\n', '\r\n')
        # TODO: Mac OS handling
        return text

    def edit(self, text, jumpIndex = None, highlight = None):
        """
        Calls the editor and thus allows the user to change the text.
        Returns the modified text. Halts the thread's operation until the editor
        is closed.

        Returns None if the user didn't save the text file in his text editor.

        Parameters:
            * text      - a Unicode string
            * jumpIndex - an integer: position at which to put the caret
            * highlight - a substring; each occurence will be highlighted
        """
        text = self.convertLinebreaks(text)
        if config.editor:
            tempFilename = '%s.%s' % (tempfile.mktemp(),
                                      config.editor_filename_extension)
            tempFile = open(tempFilename, 'w')
            tempFile.write(text.encode(config.editor_encoding))
            tempFile.close()
            creationDate = os.stat(tempFilename).st_mtime
            command = self.command(tempFilename, text, jumpIndex)
            os.system(command)
            lastChangeDate = os.stat(tempFilename).st_mtime
            if lastChangeDate == creationDate:
                # Nothing changed
                return None
            else:
                newcontent = open(tempFilename).read().decode(
                                            config.editor_encoding)
                os.unlink(tempFilename)
                return self.restoreLinebreaks(newcontent)
        else:
            return self.restoreLinebreaks(
                        pywikibot.editText(text, jumpIndex=jumpIndex,
                                           highlight=highlight))

