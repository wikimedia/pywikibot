#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Special bot library containing BaseUnlinkBot.

Do not import classes directly from here but from specialbots.
"""
#
# (C) Pywikibot team, 2003-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from pywikibot.bot import (
    AlwaysChoice, AutomaticTWSummaryBot, ChoiceException, ExistingPageBot,
    InteractiveReplace, NoRedirectPageBot, UnhandledAnswer,
)
from pywikibot.editor import TextEditor
from pywikibot.textlib import replace_links


class EditReplacement(ChoiceException, UnhandledAnswer):

    """The text should be edited and replacement should be restarted."""

    def __init__(self):
        """Initializer."""
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
        self.additional_choices = [
            AlwaysChoice(self, 'unlink all on page', 'p'),
            self._always, EditReplacement()]
        self._bot = bot
        self.context = 100
        self.context_change = 100

    def handle_answer(self, choice):
        """Handle choice and store in bot's options."""
        answer = super(InteractiveUnlink, self).handle_answer(choice)
        self._bot.options['always'] = self._always.always
        return answer


class BaseUnlinkBot(ExistingPageBot, NoRedirectPageBot, AutomaticTWSummaryBot):

    """A basic bot unlinking a given link from the current page."""

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
