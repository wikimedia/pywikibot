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

    python pwb.py unlink "Foo bar" -namespace:0 -namespace:6
        Removes links to the page [[Foo bar]] in articles and image descriptions.
"""
#
# (C) Pywikibot team, 2007-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import pywikibot
from pywikibot.bot import (
    SingleSiteBot, ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot,
    InteractiveReplace, ChoiceException, UnhandledAnswer, AlwaysChoice,
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


class BaseUnlinkBot(ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot):

    """A bot unlinking a given link from the current page."""

    def __init__(self, **kwargs):
        """Redirect all parameters and add namespace as an available option."""
        self.availableOptions.update({
            'namespaces': [],
            # Which namespaces should be processed?
            # default to [] which means all namespaces will be processed
        })
        super(BaseUnlinkBot, self).__init__(**kwargs)

    def _create_callback(self):
        """Create a new callback instance for replace_links."""
        return InteractiveUnlink(self)

    def unlink(self, target_page):
        """Unlink all links linking to the target page."""
        text = self.current_page.text
        while True:
            unlink_callback = self._create_callback()
            try:
                text = replace_links(text, unlink_callback, target_page.site)
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

        self.put_current(text)


class UnlinkBot(SingleSiteBot, BaseUnlinkBot):

    """A bot unlinking the given link from the current page."""

    summary_key = 'unlink-unlinking'

    @property
    def summary_parameters(self):
        """Return the title parameter."""
        return {'title': self.pageToUnlink.title()}

    def __init__(self, pageToUnlink, **kwargs):
        """Initialize a UnlinkBot instance with the given page to unlink."""
        super(UnlinkBot, self).__init__(**kwargs)
        self.pageToUnlink = pageToUnlink
        self.generator = pageToUnlink.getReferences(
            namespaces=self.getOption('namespaces'), content=True)

    def treat_page(self):
        """Remove links pointing to the configured page from the given page."""
        self.unlink(self.pageToUnlink)


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
        return True
    else:
        pywikibot.bot.suggest_help(missing_parameters=['page title'])
        return False

if __name__ == "__main__":
    main()
