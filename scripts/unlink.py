#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot unlinks a page on every page that links to it.

This script understands this command-line argument:

    -namespace:n   Number of namespace to process. The parameter can be used
                   multiple times. It works in combination with all other
                   parameters, except for the -start parameter. If you e.g.
                   want to iterate over all user pages starting at User:M, use
                   -start:User:M.

Any other parameter will be regarded as the title of the page
that should be unlinked.

Example:

python unlink.py "Foo bar" -namespace:0 -namespace:6

    Removes links to the page [[Foo bar]] in articles and image descriptions.
"""
#
# (C) Pywikibot team, 2007-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import pywikibot
from pywikibot import i18n
from pywikibot.bot import (
    SingleSiteBot, ExistingPageBot, NoRedirectPageBot, InteractiveReplace,
    ChoiceException, UnhandledAnswer, AlwaysChoice,
)
from pywikibot.editor import TextEditor
from pywikibot.textlib import replace_links


class EditReplacement(ChoiceException, UnhandledAnswer):

    """The text should be edited and replacement should be restarted."""

    def __init__(self):
        """Constructor."""
        super(EditReplacement, self).__init__('edit', 'e')
        self.stop = True


class InteractiveUnlink(InteractiveReplace):

    """An implementation which just allows unlinking."""

    def __init__(self, bot):
        """Create default settings."""
        super(InteractiveUnlink, self).__init__(
            old_link=bot.pageToUnlink, new_link=False, default='u')
        self._always = AlwaysChoice(self, 'unlink all pages', 'a')
        self._always.always = bot.getOption('always')
        self.additional_choices = [AlwaysChoice(self, 'unlink all on page', 'p'),
                                   self._always, EditReplacement()]
        self._bot = bot
        self.allow_replace = False
        self.context = 100
        self.context_change = 100

    def handle_answer(self, choice):
        """Handle choice and store in bot's options."""
        answer = super(InteractiveUnlink, self).handle_answer(choice)
        self._bot.options['always'] = self._always.always
        return answer


class UnlinkBot(SingleSiteBot, ExistingPageBot, NoRedirectPageBot):

    """Page unlinking bot."""

    def __init__(self, pageToUnlink, **kwargs):
        """Initialize a UnlinkBot instance with the given page to unlink."""
        self.availableOptions.update({
            'namespaces': [],
            # Which namespaces should be processed?
            # default to [] which means all namespaces will be processed
        })

        super(UnlinkBot, self).__init__(site=pageToUnlink.site, **kwargs)
        self.pageToUnlink = pageToUnlink

        self.generator = pageToUnlink.getReferences(
            namespaces=self.getOption('namespaces'), content=True)
        self.comment = i18n.twtranslate(self.pageToUnlink.site, 'unlink-unlinking',
                                        {'title': self.pageToUnlink.title()})

    def _create_callback(self):
        """Create a new callback instance for replace_links."""
        return InteractiveUnlink(self)

    def treat_page(self):
        """Remove links pointing to the configured page from the given page."""
        text = self.current_page.text
        while True:
            unlink_callback = self._create_callback()
            try:
                text = replace_links(text, unlink_callback,
                                     self.pageToUnlink.site)
            except EditReplacement:
                new_text = TextEditor().edit(
                    unlink_callback.current_text,
                    jumpIndex=unlink_callback.current_range[0])
                # if user didn't press Cancel
                if new_text:
                    text = new_text
                else:
                    text = unlink_callback.current_text
            else:
                break

        self.put_current(text, summary=self.comment)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    # This temporary string is used to read the title
    # of the page that should be unlinked.
    page_title = None
    options = {}

    for arg in pywikibot.handle_args(args):
        if arg.startswith('-namespace:'):
            if 'namespaces' not in options:
                options['namespaces'] = []
            try:
                options['namespaces'].append(int(arg[11:]))
            except ValueError:
                options['namespaces'].append(arg[11:])
        elif arg == '-always':
            options['always'] = True
        else:
            page_title = arg

    if page_title:
        page = pywikibot.Page(pywikibot.Site(), page_title)
        bot = UnlinkBot(page, **options)
        bot.run()
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    main()
