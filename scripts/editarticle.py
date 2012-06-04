#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Edit a Wikipedia article with your favourite editor.
"""

#
# (C) Gerrit Holl 2004
# (C) Pywikipedia team, 2004-2012
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
import os
import string
import optparse
import tempfile

import pywikibot
from pywikibot import i18n
from pywikibot.editor import TextEditor


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
        pywikibot.output(
            u"An edit conflict has arisen. Your edit has been saved to %s. Please try again."
            % fn)

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
            comment = i18n.twtranslate(pywikibot.getSite(), 'editarticle-edit',
                                       {'description': changes})
            try:
                self.page.put(new, comment=comment, minorEdit=False,
                              watchArticle=self.options.watch)
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

