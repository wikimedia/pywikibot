"""Non-interactive interface that stores output.

.. versionadded:: 6.4
"""
#
# (C) Pywikibot team, 2021-2022
#
# Distributed under the terms of the MIT license.
#
import logging
import queue
from typing import Any, Sequence, Union

from pywikibot import config
from pywikibot.logging import INFO, VERBOSE
from pywikibot.userinterfaces._interface_base import ABUIC


class UI(ABUIC):

    """Collects output into an unseen buffer.

    .. versionadded:: 6.4
    """

    def __init__(self) -> None:
        """Initialize the UI."""
        super().__init__()

        self._buffer = queue.Queue()

        self.log_handler = logging.handlers.QueueHandler(self._buffer)
        self.log_handler.setLevel(VERBOSE if config.verbose_output else INFO)

    def flush(self) -> None:
        """Flush cached output."""
        self.clear()

    def init_handlers(self, root_logger, *args, **kwargs) -> None:
        """Initialize the handlers for user output."""
        root_logger.addHandler(self.log_handler)

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
        self._buffer.put(text)

    def pop_output(self):
        """Provide and clear any buffered output."""
        output = []

        while not self._buffer.empty():
            record = self._buffer.get_nowait()

            if isinstance(record, str):
                output.append(record)
            elif isinstance(record, logging.LogRecord):
                output.append(record.getMessage())
            else:
                raise ValueError(
                    'BUG: buffer can only contain logs and strings, had {}'
                    .format(type(record).__name__))

        return output

    def clear(self) -> None:
        """Removes any buffered output."""
        self.pop_output()
