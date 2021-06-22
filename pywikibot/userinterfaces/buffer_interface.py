"""Non-interactive interface that stores output."""
#
# (C) Pywikibot team, 2021
#
# Distributed under the terms of the MIT license.
#
import logging
from typing import Any, Sequence, Union

from pywikibot import config
from pywikibot.logging import INFO, VERBOSE
from pywikibot.userinterfaces._interface_base import ABUIC


class UI(ABUIC, logging.Handler):

    """Collects output into an unseen buffer."""

    def __init__(self):
        """Initialize the UI."""
        super().__init__()
        self.setLevel(VERBOSE if config.verbose_output else INFO)
        self.setFormatter(logging.Formatter(fmt='%(message)s%(newline)s'))

        self._output = []

    def init_handlers(self, root_logger, *args, **kwargs):
        """Initialize the handlers for user output."""
        root_logger.addHandler(self)

    def input(self, question: str, password: bool = False,
              default: str = '', force: bool = False) -> str:
        """Ask the user a question and return the answer."""
        return default

    def input_choice(self, question: str, options, default: str = None,
                     return_shortcut: bool = True,
                     automatic_quit: bool = True, force: bool = False):
        """Ask the user and returns a value from the options."""
        return default

    def input_list_choice(self, question: str, answers: Sequence[Any],
                          default: Union[int, str, None] = None,
                          force: bool = False) -> Any:
        """Ask the user to select one entry from a list of entries."""
        return default

    def output(self, text, *args, **kwargs) -> None:
        """Output text that would usually go to a stream."""
        self._output.append(text)

    def emit(self, record: logging.LogRecord) -> None:
        """Logger output."""
        self.output(record.getMessage())

    def get_output(self):
        """Provides any output we've buffered."""
        return list(self._output)

    def pop_output(self):
        """Provide and clear any buffered output."""
        buffered_output = self.get_output()
        self.clear()
        return buffered_output

    def clear(self):
        """Removes any buffered output."""
        self._output.clear()
