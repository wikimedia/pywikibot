"""Abstract base user interface module.

.. versionadded:: 6.2
"""
#
# (C) Pywikibot team, 2021
#
# Distributed under the terms of the MIT license.
#
import sys
from abc import ABC, abstractmethod
from typing import Any, Union

from pywikibot.backports import List


class ABUIC(ABC):

    """Abstract base user interface class.

    Every user interface should derive from it to ensure that all
    required methods are implemented.

    .. versionadded:: 6.2
    """

    def argvu(self) -> List[str]:
        """Return copy of sys.argv.

        Assigned to pywikibot.argvu in bot module
        """
        return list(sys.argv)

    @abstractmethod
    def flush(self) -> None:
        """Flush cached output.

        May be passed to atexit.register() to flush any ui cache.
        """

    @abstractmethod
    def init_handlers(self, *args, **kwargs) -> None:
        """Initialize the handlers for user output.

        Called in bot.init_handlers().
        """

    @abstractmethod
    def input(self, *args, **kwargs) -> str:
        """Ask the user a question and return the answer.

        Called by bot.input().
        """
        if args:
            return input(args[0])
        return input()

    @abstractmethod
    def input_choice(self, *args, **kwargs) -> Union[int, str]:
        """Ask the user and returns a value from the options.

        Called by bot.input_choice().
        """
        return self.input()

    @abstractmethod
    def input_list_choice(self, *args, **kwargs) -> Any:
        """Ask the user to select one entry from a list of entries.

        Called by bot.input_list_choice().
        """
        return self.input()

    @abstractmethod
    def output(self, *args, **kwargs) -> None:
        """Output text to a stream."""
        print(*args, **kwargs)  # noqa: T001, T201
