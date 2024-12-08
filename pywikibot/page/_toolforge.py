"""Object representing interface to toolforge tools.

.. versionadded:: 7.7
"""
#
# (C) Pywikibot team, 2022-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import collections
import re
from http import HTTPStatus
from typing import TYPE_CHECKING

import pywikibot
from pywikibot import textlib
from pywikibot.tools import deprecated, deprecated_args


try:
    import wikitextparser
except ImportError as e:
    wikitextparser = e

if TYPE_CHECKING:
    import datetime

    from pywikibot import Timestamp
    DATETYPE = str | Timestamp | datetime.datetime | datetime.date | None


class WikiBlameMixin:

    """Page mixin for main authorship.

    .. versionadded:: 7.7
    """

    #: Supported wikipedia site codes
    WIKIBLAME_CODES = (
        'ar', 'de', 'en', 'es', 'eu', 'fr', 'hu', 'id', 'it', 'ja', 'nl', 'pl',
        'pt', 'tr',
    )

    def _check_wh_supported(self):
        """Check if WikiHistory is supported."""
        if self.site.family.name != 'wikipedia':
            raise NotImplementedError(
                'main_authors method is implemented for wikipedia family only')

        if self.site.code not in self.WIKIBLAME_CODES:
            raise NotImplementedError('main_authors method is not implemented '
                                      f'for wikipedia:{self.site.code}')

        if self.namespace() != pywikibot.site.Namespace.MAIN:
            raise NotImplementedError(
                'main_authors method is implemented for main namespace only')

        if not self.exists():
            raise pywikibot.exceptions.NoPageError(self)

        if isinstance(wikitextparser, ImportError):
            raise wikitextparser

    @deprecated('authorsship', since='9.3.0')
    @deprecated_args(onlynew=None)  # since 9.2.0
    def main_authors(self) -> collections.Counter[str, int]:
        """Retrieve the 5 topmost main authors of an article.

        Sample:

        >>> import pywikibot
        >>> site = pywikibot.Site('wikipedia:eu')
        >>> page = pywikibot.Page(site, 'Python (informatika)')
        >>> auth = page.main_authors()
        >>> auth.most_common(1)
        [('Ksarasola', 82)]

        .. important:: Only implemented for main namespace pages and
           only wikipedias of :attr:`WIKIBLAME_CODES` are supported.
        .. seealso::
           - https://wikihistory.toolforge.org
           - https://de.wikipedia.org/wiki/Wikipedia:Technik/Cloud/wikihistory
           - https://xtools.wmcloud.org/authorship/

        .. versionchanged:: 9.2
           do not use any wait cycles due to :phab:`366100`.
        .. versionchanged:: 9.3
           https://xtools.wmcloud.org/authorship/ is used to retrieve
           authors
        .. deprecated:: 9.3
           use :meth:`authorship` instead.

        :return: Percentage of edits for each username

        :raise ImportError: missing ``wikitextparser`` module.
        :raise NotImplementedError: unsupported site or unsupported
            namespace.
        :raise Error: Error response from xtools.
        :raise NoPageError: The page does not exist.
        :raise requests.exceptions.HTTPError: 429 Client Error: Too Many
            Requests for url; login to meta family first.
        """
        return collections.Counter(
            {user: int(cnt) for user, (_, cnt) in self.authorship(5).items()})

    def authorship(
        self,
        n: int | None = None,
        *,
        min_chars: int = 0,
        min_pct: float = 0.0,
        max_pct_sum: float | None = None,
        revid: int | None = None,
        date: DATETYPE = None,
    ) -> dict[str, tuple[int, float]]:
        """Retrieve authorship attribution of an article.

        This method uses XTools/Authorship to retrieve the authors
        measured by character count.

        Sample:

        >>> import pywikibot
        >>> site = pywikibot.Site('wikipedia:en')
        >>> page = pywikibot.Page(site, 'Pywikibot')
        >>> auth = page.authorship()
        >>> auth
        {'1234qwer1234qwer4': (68, 100.0)}

        .. important:: Only implemented for main namespace pages and
           only wikipedias of :attr:`WIKIBLAME_CODES` are supported.
        .. seealso::
           - https://xtools.wmcloud.org/authorship/
           - https://www.mediawiki.org/wiki/XTools/Authorship
           - https://www.mediawiki.org/wiki/WikiWho

        .. versionadded:: 9.3
           this method replaces :meth:`main_authors`.

        :param n: Only return the first *n* or fewer authors.
        :param min_chars: Only return authors with more than *min_chars*
            chars changes.
        :param min_pct: Only return authors with more than *min_pct*
            percentage edits.
        :param max_pct_sum: Only return authors until the prcentage sum
            reached *max_pct_sum*.
        :param revid: The revision id for the authors should be found.
            If ``None`` or ``0``, the latest revision is be used. Cannot
            be used together with *date*.
        :param date: The revision date for the authors should be found.
            If ``None``, it will be ignored. Cannot be used together
            with *revid*. If the parameter is a string it must be given
            in the form ``YYYY-MM-DD``
        :return: Character count and percentage of edits for each
            username.

        :raise ImportError: missing ``wikitextparser`` module
        :raise NotImplementedError: unsupported site or unsupported
            namespace.
        :raise Error: Error response from xtools.
        :raiseNoPageError: The page does not exist.
        :raise requests.exceptions.HTTPError: 429 Client Error: Too Many
            Requests for url; login to meta family first.
        """
        baseurl = 'https://xtools.wmcloud.org/authorship/{url}&format=wikitext'
        pattern = r'\[\[.+[|/](?P<user>.+)\]\]'

        self._check_wh_supported()

        if revid and date:
            raise ValueError(
                'You cannot specify revid together with date argument')

        show = revid or 0 if date is None else str(date)[:10]
        url = '{}.wikipedia.org/{}/{}?uselang={}'.format(
            self.site.code,
            self.title(as_url=True, with_ns=False, with_section=False),
            show,
            'en',
        )
        url = baseurl.format(url=url)

        r = pywikibot.comms.http.fetch(url)
        if r.status_code != HTTPStatus.OK:
            r.raise_for_status()

        result: list[list[str]] = []
        try:
            table = wikitextparser.parse(r.text).tables[0]
        except IndexError:
            pattern = textlib.get_regexes('code')[0]
            match = pattern.search(r.text)
            if match:
                msg = textlib.removeHTMLParts(match[0])
            else:
                pattern = textlib.get_regexes('strong')[0]
                strongs = pattern.findall(r.text)
                if strongs:
                    msg = textlib.removeHTMLParts('\n'.join(strongs))
                else:
                    msg = 'Unknown exception from xtools'
            raise pywikibot.exceptions.Error(msg) from None

        pct_sum = 0.0
        for row in table.data():
            if row[0] == 'Rank':
                continue  # skip headline

            rank = int(row[0])
            user = re.match(pattern, row[1])['user']
            chars = int(row[3].replace(',', '_'))
            percent = float(row[4].rstrip('%'))

            # take into account that data() is ordered
            if n and rank > n or chars < min_chars or percent < min_pct:
                break

            result.append((user, chars, percent))
            pct_sum += percent
            if max_pct_sum and pct_sum >= max_pct_sum:
                break

        return {user: (chars, percent) for user, chars, percent in result}
