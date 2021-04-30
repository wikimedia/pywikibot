"""Objects representing obsolete MediaWiki sites."""
#
# (C) Pywikibot team, 2019-2021
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot.exceptions import NoPageError
from pywikibot.site._apisite import APISite
from pywikibot.site._basesite import BaseSite
from pywikibot.tools import remove_last_args


class RemovedSite(BaseSite):

    """Site removed from a family."""

    pass


class ClosedSite(APISite):
    """Site closed to read-only mode."""

    @remove_last_args(['sysop'])
    def __init__(self, code, fam, user=None):
        """Initializer."""
        super().__init__(code, fam, user)

    def _closed_error(self, notice=''):
        """An error instead of pointless API call."""
        pywikibot.error('Site {} has been closed. {}'.format(self.sitename,
                                                             notice))

    def page_restrictions(self, page):
        """Return a dictionary reflecting page protections."""
        if not self.page_exists(page):
            raise NoPageError(page)
        if not hasattr(page, '_protection'):
            page._protection = {'edit': ('steward', 'infinity'),
                                'move': ('steward', 'infinity'),
                                'delete': ('steward', 'infinity'),
                                'upload': ('steward', 'infinity'),
                                'create': ('steward', 'infinity')}
        return page._protection

    def recentchanges(self, **kwargs):
        """An error instead of pointless API call."""
        self._closed_error('No recent changes can be returned.')

    def is_uploaddisabled(self):
        """Return True if upload is disabled on site."""
        if not hasattr(self, '_uploaddisabled'):
            self._uploaddisabled = True
        return self._uploaddisabled

    def newpages(self, **kwargs):
        """An error instead of pointless API call."""
        self._closed_error('No new pages can be returned.')

    def newfiles(self, **kwargs):
        """An error instead of pointless API call."""
        self._closed_error('No new files can be returned.')
