"""Object representing interface to toolforge tools.

.. versionadded:: 7.7
"""
#
# (C) Pywikibot team, 2022-2023
#
# Distributed under the terms of the MIT license.
#
import collections
import re
from typing import Optional

import pywikibot
from pywikibot import config


class WikiBlameMixin:

    """Page mixin for main authorship.

    .. versionadded:: 7.7
    """

    #: Supported wikipedia site codes
    WIKIBLAME_CODES = 'als', 'bar', 'de', 'en', 'it', 'nds', 'sco'

    def _check_wh_supported(self):
        """Check if WikiHistory is supported."""
        if self.site.family.name != 'wikipedia':
            raise NotImplementedError(
                'main_authors method is implemented for wikipedia family only')

        if self.site.code not in self.WIKIBLAME_CODES:
            raise NotImplementedError(
                'main_authors method is not implemented for wikipedia:{}'
                .format(self.site.code))

        if self.namespace() != pywikibot.site.Namespace.MAIN:
            raise NotImplementedError(
                'main_authors method is implemented for main namespace only')

        if not self.exists():
            raise pywikibot.exceptions.NoPageError(self)

    def main_authors(self, *,
                     onlynew: Optional[bool] = None) -> collections.Counter:
        """Retrieve the 5 topmost main authors of an article.

        This method uses WikiHistory to retrieve the text based main
        authorship.

        Sample:

        >>> import pywikibot
        >>> site = pywikibot.Site('wikipedia:nds')
        >>> page = pywikibot.Page(site, 'Python (Programmeerspraak)')
        >>> auth = page.main_authors(onlynew=False)
        >>> auth
        Counter({'RebeccaBreu': 99, 'Slomox': 1})

        .. note:: Only implemented for main namespace pages.
        .. note:: Only wikipedias of :attr:`WIKIBLAME_CODES` are supported.
        .. seealso::
           - https://wikihistory.toolforge.org
           - https://de.wikipedia.org/wiki/Wikipedia:Technik/Cloud/wikihistory

        :param onlynew: If False, use the cached values. If True,
            calculate the Counter data which can take some time; it may
            fail with TimeoutError after ``config.max_retries``. If None
            it calculates new data like for True but uses data from
            cache if new data cannot be calculated in meantime.
        :return: Number of edits for each username
        :raise NotImplementedError: unsupported site or unsupported namespace
        :raise pywikibot.exceptions.NoPageError: The page does not exist
        :raise pywikibot.exceptions.TimeoutError: Maximum retries exceeded
        """
        baseurl = 'https://wikihistory.toolforge.org'
        pattern = (r'><bdi>(?P<author>.+?)</bdi></a>\s'
                   r'\((?P<percent>\d{1,3})&')

        self._check_wh_supported()

        url = baseurl + '/wiki/getauthors.php?wiki={}wiki&page_id={}'.format(
            self.site.code, self.pageid)
        if onlynew:
            url += '&onlynew=1'

        for current_retries in range(config.max_retries):
            r = pywikibot.comms.http.fetch(url)
            if r.status_code != 200:
                r.raise_for_status()

            if 'Timeout' not in r.text:  # window.setTimeout in result
                return collections.Counter(
                    {user: int(cnt)
                     for user, cnt in re.findall(pattern, r.text)})

            delay = pywikibot.config.retry_wait * 2 ** current_retries
            pywikibot.warning('WikiHistory timeout.\n'
                              'Waiting {:.1f} seconds before retrying.'
                              .format(delay))
            pywikibot.sleep(delay)
            if onlynew is None and current_retries >= config.max_retries - 2:
                url += '&onlynew=1'

        raise pywikibot.exceptions.TimeoutError(
            'Maximum retries attempted without success.')
