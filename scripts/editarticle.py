#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Edit a Wikipedia article with your favourite editor.

 TODO: - non existing pages
       - edit conflicts
       - minor edits
       - watch/unwatch
       - ...

The following parameters are supported:

-r                Edit redirect pages without following them
--edit_redirect   automatically.
--edit-redirect

-p P              Choose which page to edit.
--page P          This argument can be passed positionally.

-w                Add the page to the user's watchlist after editing.
--watch
"""
#
# (C) Gerrit Holl, 2004
# (C) Pywikibot team, 2004-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import os
import sys
import argparse
import tempfile

import pywikibot
from pywikibot import i18n
from pywikibot.editor import TextEditor


class ArticleEditor(object):

    """Edit a wiki page."""

    # join lines if line starts with this ones
    # TODO: No apparent usage
    # joinchars = string.letters + '[]' + string.digits

    def __init__(self, *args):
        self.set_options(*args)
        self.setpage()
        self.site = pywikibot.Site()

    def set_options(self, *args):
        """Parse commandline and set options attribute."""
        my_args = pywikibot.handle_args(args)

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("-r", "--edit_redirect", "--edit-redirect",
                            action="store_true", help="Ignore/edit redirects")
        parser.add_argument("-p", "--page", help="Page to edit")
        parser.add_argument("-w", "--watch", action="store_true",
                            help="Watch article after edit")
        # convenience positional argument so we can act like a normal editor
        parser.add_argument("wikipage", nargs="?", help="Page to edit")
        self.options = parser.parse_args(my_args)

        if self.options.page and self.options.wikipage:
            pywikibot.error(u"Multiple pages passed. Please specify a single page to edit.")
            sys.exit(1)
        self.options.page = self.options.page or self.options.wikipage

    def setpage(self):
        """Set page and page title."""
        site = pywikibot.Site()
        pageTitle = self.options.page or pywikibot.input(u"Page to edit:")
        self.page = pywikibot.Page(pywikibot.Link(pageTitle, site))
        if not self.options.edit_redirect and self.page.isRedirectPage():
            self.page = self.page.getRedirectTarget()

    def handle_edit_conflict(self, new):
        fn = os.path.join(tempfile.gettempdir(), self.page.title())
        fp = open(fn, 'w')
        fp.write(new)
        fp.close()
        pywikibot.output(
            u"An edit conflict has arisen. Your edit has been saved to %s. Please try again."
            % fn)

    def run(self):
        self.site.login()
        try:
            old = self.page.get(get_redirect=self.options.edit_redirect)
        except pywikibot.NoPage:
            old = ""
        textEditor = TextEditor()
        new = textEditor.edit(old)
        if new and old != new:
            pywikibot.showDiff(old, new)
            changes = pywikibot.input(u"What did you change?")
            comment = i18n.twtranslate(pywikibot.Site(), 'editarticle-edit',
                                       {'description': changes})
            try:
                self.page.put(new, summary=comment, minorEdit=False,
                              watchArticle=self.options.watch)
            except pywikibot.EditConflict:
                self.handle_edit_conflict(new)
        else:
            pywikibot.output(u"Nothing changed")


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    app = ArticleEditor(*args)
    app.run()


if __name__ == "__main__":
    main()
