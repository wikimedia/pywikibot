"""Objects representing obsolete MediaWiki sites."""
#
# (C) Pywikibot team, 2019-2022
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import pywikibot
from pywikibot.exceptions import NoPageError
from pywikibot.site._apisite import APISite
from pywikibot.site._basesite import BaseSite


class RemovedSite(BaseSite):

    """Site removed from a family."""


class ClosedSite(APISite):

    """Site closed to read-only mode."""

    def _closed_error(self, notice: str = '') -> None:
        """An error instead of pointless API call."""
        pywikibot.error(f'Site {self.sitename} has been closed. {notice}')

    def page_restrictions(
            self, page: pywikibot.Page) -> dict[str, tuple[str, str]]:
        """Return a dictionary reflecting page protections."""
        if not page.exists():
            raise NoPageError(page)
        if not hasattr(page, '_protection'):
            page._protection = dict.fromkeys(
                ('create', 'delete', 'edit', 'move', 'upload'),
                ('steward', 'infinity'))
        return page._protection

    def recentchanges(self, **kwargs) -> None:
        """An error instead of pointless API call."""
        self._closed_error('No recent changes can be returned.')

    def is_uploaddisabled(self) -> bool:
        """Upload is disabled on site."""
        return True

    def newpages(self, **kwargs) -> None:
        """An error instead of pointless API call."""
        self._closed_error('No new pages can be returned.')
