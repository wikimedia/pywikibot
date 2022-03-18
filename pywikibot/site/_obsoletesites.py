"""Objects representing obsolete MediaWiki sites."""
#
# (C) Pywikibot team, 2019-2022
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot.backports import Dict, Tuple
from pywikibot.exceptions import NoPageError
from pywikibot.site._apisite import APISite
from pywikibot.site._basesite import BaseSite


class RemovedSite(BaseSite):

    """Site removed from a family."""


class ClosedSite(APISite):
    """Site closed to read-only mode."""

    def __init__(self, code, fam, user=None) -> None:
        """Initializer."""
        super().__init__(code, fam, user)

    def _closed_error(self, notice: str = '') -> None:
        """An error instead of pointless API call."""
        pywikibot.error('Site {} has been closed. {}'.format(self.sitename,
                                                             notice))

    def page_restrictions(
            self, page: 'pywikibot.Page') -> Dict[str, Tuple[str, str]]:
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
        """Return True if upload is disabled on site."""
        if not hasattr(self, '_uploaddisabled'):
            self._uploaddisabled = True
        return self._uploaddisabled

    def newpages(self, **kwargs) -> None:
        """An error instead of pointless API call."""
        self._closed_error('No new pages can be returned.')
