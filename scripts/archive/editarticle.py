#!/usr/bin/python
"""
Edit a Wikipedia article with your favourite editor.

TODO:

 - non existing pages
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
# (C) Pywikibot team, 2004-2020
#
# Distributed under the terms of the MIT license.
#
import argparse
import os
import sys
import tempfile

import pywikibot
from pywikibot import i18n
from pywikibot.backports import Tuple
from pywikibot.editor import TextEditor
from pywikibot.exceptions import EditConflictError, NoPageError


class ArticleEditor:

    """Edit a wiki page."""

    def __init__(self, *args):
        """Initializer."""
        self.set_options(*args)
        self.site = pywikibot.Site()
        self.setpage()

    def set_options(self, *args):
        """Parse commandline and set options attribute."""
        my_args = pywikibot.handle_args(args)

        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument('-r', '--edit_redirect', '--edit-redirect',
                            action='store_true', help='Ignore/edit redirects')
        parser.add_argument('-p', '--page', help='Page to edit')
        parser.add_argument('-w', '--watch', action='store_true',
                            help='Watch article after edit')
        # convenience positional argument so we can act like a normal editor
        parser.add_argument('wikipage', nargs='?', help='Page to edit')
        self.options = parser.parse_args(my_args)

        if self.options.page and self.options.wikipage:
            pywikibot.error('Multiple pages passed. Please specify a single '
                            'page to edit.')
            sys.exit(1)
        self.options.page = self.options.page or self.options.wikipage

    def setpage(self):
        """Set page and page title."""
        page_title = self.options.page or pywikibot.input('Page to edit:')
        self.page = pywikibot.Page(pywikibot.Link(page_title, self.site))
        if not self.options.edit_redirect and self.page.isRedirectPage():
            self.page = self.page.getRedirectTarget()

    def handle_edit_conflict(self, new):
        """When an edit conflict occurs save the new text to a file."""
        fn = os.path.join(tempfile.gettempdir(), self.page.title())
        with open(fn, 'w') as fp:
            fp.write(new)
        pywikibot.output(
            'An edit conflict has arisen. Your edit has been saved to {}. '
            'Please try again.'.format(fn))

    def run(self):
        """Run the bot."""
        self.site.login()
        try:
            old = self.page.get(get_redirect=self.options.edit_redirect)
        except NoPageError:
            old = ''
        text_editor = TextEditor()
        new = text_editor.edit(old)
        if new and old != new:
            pywikibot.showDiff(old, new)
            changes = pywikibot.input('What did you change?')
            comment = i18n.twtranslate(self.site, 'editarticle-edit',
                                       {'description': changes})
            try:
                self.page.put(new, summary=comment, minor=False,
                              watch=self.options.watch)
            except EditConflictError:
                self.handle_edit_conflict(new)
        else:
            pywikibot.output('Nothing changed')


def main(*args: Tuple[str, ...]):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    app = ArticleEditor(*args)
    app.run()


if __name__ == '__main__':
    main()
