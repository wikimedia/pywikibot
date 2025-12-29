"""Object representing interface to toolforge tools.

.. versionadded:: 7.7
"""
#
# (C) Pywikibot team, 2022-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import collections
import re
from http import HTTPStatus
from warnings import warn

import pywikibot
from pywikibot.tools import deprecated, deprecated_args, remove_last_args


class WikiBlameMixin:

    """Page mixin for main authorship.

    .. versionadded:: 7.7
    """

    #: Supported wikipedia site codes
    WIKIBLAME_CODES = 'als', 'bar', 'de', 'en', 'it', 'nds', 'sco'

    def _check_wh_supported(self) -> None:
        """Check if WikiHistory is supported."""
        if self.site.family.name != 'wikipedia':
            raise NotImplementedError(
                'main_authors method is implemented for wikipedia family only')

        if (code := self.site.code) not in self.WIKIBLAME_CODES:
            raise NotImplementedError(
                f'main_authors method is not implemented for wikipedia:{code}')

        if (ns := self.namespace()) not in (0, 4, 10, 12, 14, 100):
            raise NotImplementedError(
                f'main_authors method is not implemented for {ns} namespace')

        if not self.exists():
            raise pywikibot.exceptions.NoPageError(self)

    @deprecated('authorsship', since='9.3.0')
    @deprecated_args(onlynew=None)  # since 9.2.0
    def main_authors(self) -> collections.Counter[str, int]:
        """Retrieve the 5 topmost main authors of an article.

        Sample:

        >>> import pywikibot
        >>> site = pywikibot.Site('wikipedia:de')
        >>> page = pywikibot.Page(site, 'Project:Pywikibot')
        >>> auth = page.main_authors()
        >>> auth.most_common(1)
        [('DrTrigon', 37)]

        .. deprecated:: 9.3
           use :meth:`authorship` instead.
        .. seealso:: :meth:`authorship` for further informations

        :return: Percentage of edits for each username

        :raise NotImplementedError: unsupported site or unsupported
            namespace.
        :raise NoPageError: The page does not exist.
        :raise TimeoutError: WikiHistory timeout
        """
        return collections.Counter(
            {user: int(cnt) for user, (_, cnt) in self.authorship(5).items()})

    @remove_last_args(['revid', 'date'])  # since 10.1.0
    def authorship(
        self,
        n: int | None = None,
        *,
        min_chars: int = 0,
        min_pct: float = 0.0,
        max_pct_sum: float | None = None,
    ) -> dict[str, tuple[int, float]]:
        """Retrieve authorship attribution of an article.

        This method uses WikiHistory to retrieve the authors measured by
        character count.

        Sample:

        >>> import pywikibot
        >>> site = pywikibot.Site('wikipedia:en')
        >>> page = pywikibot.Page(site, 'Pywikibot')
        >>> auth = page.authorship()  # doctest: +SKIP
        >>> auth  # doctest: +SKIP
        {'1234qwer1234qwer4': (68, 100.0)}

        .. important:: Only implemented for pages in Main, Project,
           Category and Template namespaces and only wikipedias of
           :attr:`WIKIBLAME_CODES` are supported.
        .. versionadded:: 9.3
           XTools is used to retrieve authors. This method replaces
           :meth:`main_authors`.
        .. versionchanged:: 10.1
           WikiHistory is used to retrieve authors due to :phab:`T392694`.

        Here are the differences between these two implementations:

        .. tabs::

           .. tab:: WikiHistory

              .. versionadded:: 10.1

              - Implemented from version 7.7 until 9.2 (with
                :meth:`main_authors` method) and from 10.1.
              - Main, Project, Category and Template namespaces are
                supported
              - Only 'als', 'bar', 'de', 'en', 'it', 'nds' and 'sco'
                Wikipedias are supported.
              - Revision ID *revid* or revision *date* is not supported.
                Always the latest revision is used.
              - Only the most 5 authors are given.
              - No additional parsing library is required.


              .. seealso::
                 - https://wikihistory.toolforge.org
                 - https://de.wikipedia.org/wiki/WP:HT/wikihistory

           .. tab:: XTools

              .. versionremoved:: 10.1

              - Implemented from version 9.3 until 10.0.
              - Only Main namespace is supported.
              - Only 'ar', 'de', 'en', 'es', 'eu', 'fr', 'hu', 'id',
                'it', 'ja', 'nl', 'pl', 'pt' and 'tr' Wikipedias are
                supported.
              - Revision ID *revid* or revision *date* is supported to
                get authorship for this revision.
              - All authors can be given.
              - wikitextparser parsing library is required.

              .. seealso::
                 - https://xtools.wmcloud.org/authorship/
                 - https://www.mediawiki.org/wiki/XTools/Authorship
                 - https://www.mediawiki.org/wiki/WikiWho


        :param n: Only return the first *n* or fewer authors.
        :param min_chars: Only return authors with more than *min_chars*
            chars changes.
        :param min_pct: Only return authors with more than *min_pct*
            percentage edits.
        :param max_pct_sum: Only return authors until the prcentage sum
            reached *max_pct_sum*.
        :return: Character count and percentage of edits for each
            username.

        :raise NotImplementedError: unsupported site or unsupported
            namespace.
        :raise NoPageError: The page does not exist.
        :raise TimeoutError: WikiHistory timeout
        """
        if n and n > 5:
            warn('Only the first 5 authors can be given.', stacklevel=2)

        baseurl = 'https://wikihistory.toolforge.org'
        pattern = (r'><bdi>(?P<author>.+?)</bdi></a>\s'
                   r'\((?P<percent>\d{1,3})&')

        self._check_wh_supported()

        for onlynew in (1, 0):
            url = baseurl + (f'/wiki/getauthors.php?wiki={self.site.code}wiki'
                             f'&page_id={self.pageid}&onlynew={onlynew}')

            r = pywikibot.comms.http.fetch(url)
            if r.status_code != HTTPStatus.OK:
                r.raise_for_status()

            if 'Timeout' not in r.text:
                break

            pywikibot.sleep(pywikibot.config.retry_wait)
        else:
            raise pywikibot.exceptions.TimeoutError('WikiHistory Timeout')

        length = len(self.text)
        result: list[list[str]] = []
        pct_sum = 0.0
        for rank, (user, cnt) in enumerate(re.findall(pattern, r.text),
                                           start=1):
            chars = length * int(cnt) // 100
            percent = float(cnt)

            # take into account that data() is ordered
            if n and rank > n or chars < min_chars or percent < min_pct:
                break

            result.append((user, chars, percent))

            pct_sum += percent
            if max_pct_sum and pct_sum >= max_pct_sum:
                break

        return {user: (chars, percent) for user, chars, percent in result}
