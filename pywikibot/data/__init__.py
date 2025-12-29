"""Module providing several layers of data access to the wiki."""
#
# (C) Pywikibot team, 2007-2023
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import pywikibot


class WaitingMixin:

    """A mixin to implement wait cycles.

    .. versionadded:: 8.4

    :ivar int max_retries: Maximum number of times to retry an API
        request before quitting. Defaults to ``config.max_retries`` if
        attribute is missing.
    :ivar int retry_wait: Minimum time to wait before resubmitting a
        failed API request. Defaults to ``config.retry_wait`` if
        attribute is missing.
    :ivar int current_retries: counter of retries made for the current
        request. Starting with 1 if attribute is missing.
    """

    def wait(self, delay: int | None = None) -> None:
        """Determine how long to wait after a failed request.

        :param delay: Minimum time in seconds to wait. Overwrites
            ``retry_wait`` variable if given. The delay doubles each
            retry until ``retry_max`` seconds is reached.
        """
        if not hasattr(self, 'max_retries'):
            self.max_retries = pywikibot.config.max_retries

        if not hasattr(self, 'retry_wait'):
            self.retry_wait = pywikibot.config.retry_wait

        if not hasattr(self, 'current_retries'):
            self.current_retries = 1
        else:
            self.current_retries += 1

        if self.current_retries > self.max_retries:
            raise pywikibot.exceptions.TimeoutError(
                'Maximum retries attempted without success.')

        # double the next wait, but do not exceed config.retry_max seconds
        delay = delay or self.retry_wait
        delay *= 2 ** (self.current_retries - 1)
        delay = min(delay, pywikibot.config.retry_max)

        pywikibot.warning(f'Waiting {delay:.1f} seconds before retrying.')
        pywikibot.sleep(delay)
