"""Special bot library containing BaseUnlinkBot.

Do not import classes directly from here but from specialbots.
"""
#
# (C) Pywikibot team, 2003-2022
#
# Distributed under the terms of the MIT license.
#
from pywikibot.bot import (
    AlwaysChoice,
    AutomaticTWSummaryBot,
    ChoiceException,
    ExistingPageBot,
    InteractiveReplace,
)
from pywikibot.bot_choice import UnhandledAnswer
from pywikibot.editor import TextEditor
from pywikibot.textlib import replace_links


class EditReplacementError(ChoiceException, UnhandledAnswer):

    """The text should be edited and replacement should be restarted."""

    def __init__(self) -> None:
        """Initializer."""
        super().__init__('edit', 'e')
        self.stop = True


class InteractiveUnlink(InteractiveReplace):

    """An implementation which just allows unlinking."""

    def __init__(self, bot) -> None:
        """Create default settings."""
        super().__init__(old_link=bot.pageToUnlink,
                         new_link=False, default='u')
        self._always = AlwaysChoice(self, 'unlink all pages', 'a')
        self._always.always = bot.opt.always
        self.additional_choices = [
            AlwaysChoice(self, 'unlink all on page', 'p'),
            self._always, EditReplacementError()]
        self._bot = bot
        self.context = 100
        self.context_change = 100

    def handle_answer(self, choice):
        """Handle choice and store in bot's options."""
        answer = super().handle_answer(choice)
        self._bot.opt.always = self._always.always
        return answer


class BaseUnlinkBot(ExistingPageBot, AutomaticTWSummaryBot):

    """A basic bot unlinking a given link from the current page."""

    use_redirects = False

    def __init__(self, **kwargs) -> None:
        """Redirect all parameters and add namespace as an available option."""
        self.available_options.update({
            'namespaces': [],
            # Which namespaces should be processed?
            # default to [] which means all namespaces will be processed
        })
        super().__init__(**kwargs)

    def _create_callback(self):
        """Create a new callback instance for replace_links."""
        return InteractiveUnlink(self)

    def unlink(self, target_page) -> None:
        """Unlink all links linking to the target page."""
        text = self.current_page.text
        while True:
            unlink_callback = self._create_callback()
            try:
                text = replace_links(text, unlink_callback, target_page.site)
            except EditReplacementError:
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
