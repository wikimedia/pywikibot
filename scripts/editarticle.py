#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Edit a Wikipedia article with your favourite editor.
"""

#
# (C) Gerrit Holl 2004
# (C) Pywikipedia team, 2004-2009
#
__version__ = "$Id$"
#
# Distributed under the terms of the MIT license.
#

# Version 0.4.
#
# TODO: - non existing pages
#       - edit conflicts
#       - minor edits
#       - watch/unwatch
#       - ...

__metaclass__ = type
import sys
import os
import string
import optparse
import tempfile

import pywikibot
from pywikibot import config

msg = {
    'ar': u'تعديل يدوي: %s',
    'de': u'Manuelle Bearbeitung: %s',
    'en': u'Manual edit: %s',
    'he': u'עריכה ידנית: %s',
    'ja': u'手動編集: %s',
    'pt': u'Editando manualmente com bot: %s',
    'sv': u'Manuell redigering: %s',
    'is': u'Handvirk breyting: %s',
    'zh': u'手動編輯: %s',
}

class TextEditor:
    def __init__(self):
        pass

    def command(self, tempFilename, text, jumpIndex = None):
        command = config.editor
        if jumpIndex:
            # Some editors make it possible to mark occurences of substrings, or
            # to jump to the line of the first occurence.
            # TODO: Find a better solution than hardcoding these, e.g. a config
            # option.
            line = text[:jumpIndex].count('\n')
            column = jumpIndex - (text[:jumpIndex].rfind('\n') + 1)
        else:
            line = column = 0
        # Linux editors. We use startswith() because some users might use parameters.
        if config.editor.startswith('kate'):
            command += " -l %i -c %i" % (line, column)
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

class ArticleEditor:
    # join lines if line starts with this ones
    joinchars = string.letters + '[]' + string.digits

    def __init__(self, *args):
        self.set_options(*args)
        self.setpage()
        self.site = pywikibot.getSite()

    def set_options(self, *args):
        """Parse commandline and set options attribute"""
        my_args = []
        for arg in pywikibot.handleArgs(*args):
            my_args.append(arg)
        parser = optparse.OptionParser()
        parser.add_option("-r", "--edit_redirect", action="store_true",
                          default=False, help="Ignore/edit redirects")
        parser.add_option("-p", "--page", help="Page to edit")
        parser.add_option("-w", "--watch", action="store_true", default=False,
                          help="Watch article after edit")
        #parser.add_option("-n", "--new_data", default="",
        #                  help="Automatically generated content")
        (self.options, args) = parser.parse_args(args=my_args)

        # for convenience, if we have an arg, stuff it into the opt, so we
        # can act like a normal editor.
        if (len(args) == 1):
            self.options.page = args[0]

    def setpage(self):
        """Sets page and page title"""
        site = pywikibot.getSite()
        pageTitle = self.options.page or pywikibot.input(u"Page to edit:")
        self.page = pywikibot.Page(pywikibot.Link(pageTitle, site))
        if not self.options.edit_redirect and self.page.isRedirectPage():
            self.page = self.page.getRedirectTarget()

    def handle_edit_conflict(self):
        fn = os.path.join(tempfile.gettempdir(), self.page.title())
        fp = open(fn, 'w')
        fp.write(new)
        fp.close()
        pywikibot.output(u"An edit conflict has arisen. Your edit has been saved to %s. Please try again." % fn)

    def run(self):
        try:
            old = self.page.get(get_redirect = self.options.edit_redirect)
        except pywikibot.NoPage:
            old = ""
        textEditor = TextEditor()
        new = textEditor.edit(old)
        if new and old != new:
            pywikibot.showDiff(old, new)
            changes = pywikibot.input(u"What did you change?")
            comment = pywikibot.translate(pywikibot.getSite(), msg) % changes
            try:
                self.page.put(new, comment = comment, minorEdit = False, watchArticle=self.options.watch)
            except pywikibot.EditConflict:
                self.handle_edit_conflict(new)
        else:
            pywikibot.output(u"Nothing changed")

def main(*args):
    app = ArticleEditor(*args)
    app.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()

