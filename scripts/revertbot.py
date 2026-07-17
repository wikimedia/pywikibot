#!/usr/bin/env python3
#
# (C) Pywikibot team, 2008-2026
#
# Distributed under the terms of the MIT license.
#
r"""This script can be used for reverting certain edits.

The following command line parameters are supported:

-username   Edits of which user need to be reverted. Default is bot's
            username (:code:`site.username()`).

-rollback   Rollback edits instead of reverting them.

            .. note:: No diff would be shown in this mode.

-limit:num  [int] Use the last num contributions to be checked for
            revert. Default is 500.

Users who want to customize the behaviour should subclass the
`ContribRevertBot` and override its `callback` method. Here is a sample:

.. code:: python

    class myRevertBot(ContribRevertBot):

        '''Example revert bot.'''

        def callback(self, item: page.Contribution) -> bool:
            '''Sample callback function for 'private' revert bot.

            :param item: an item from User.contribs
            '''
            if item.top:
                page = item.page
                text = page.get(get_redirect=True)
                pattern = re.compile(r'\[\[.+?:.+?\..+?\]\]')
                return bool(pattern.search(text))
            return False

.. version-changed:: 11.7
   Contribution items are now :class:`page.Contribution` instances
   instead of generic mappings. :class:`BaseRevertBot` and
   :class:`myRevertBot` are kept for backward compatibility and use the
   legacy data format.
"""
from __future__ import annotations

import abc
from collections.abc import Mapping
from textwrap import fill
from typing import Any

import pywikibot
from pywikibot import i18n
from pywikibot.bot import OptionHandler
from pywikibot.date import format_date, formatYear
from pywikibot.exceptions import APIError, Error
from pywikibot.page import Contribution
from pywikibot.tools import deprecated


class AbstractRevertBot(OptionHandler, abc.ABC):

    """Abstract RevertBot class.

    .. version-added:: 11.7
    """

    available_options = {
        'comment': '',
        'rollback': False,
        'limit': 500
    }

    def __init__(self, site=None, **kwargs) -> None:
        """Initializer."""
        self.site = site or pywikibot.Site()
        self.user = kwargs.pop('user', self.site.username())
        super().__init__(**kwargs)

    @abc.abstractmethod
    def get_contributions(self, total: int = 500, ns=None):
        """Get contributions."""
        ...

    def revert_contribs(self, callback=None) -> None:
        """Revert contributions."""
        if callback is None:
            callback = self.callback

        for item in self.get_contributions(total=self.opt.limit):
            if callback(item):
                result = self.revert(item)
                if result:
                    pywikibot.info(
                        fill(f"{item['title']}: {result}", width=77))
                else:
                    pywikibot.info(f"Skipped {item['title']}")
            else:
                pywikibot.info(f"Skipped {item['title']} by callback")

    @staticmethod
    @abc.abstractmethod
    def callback(item: Mapping[str, Any]) -> bool:
        """Callback function."""
        ...

    def local_timestamp(self, ts) -> str:
        """Convert Timestamp to a localized timestamp string.

        .. version-added:: 7.0
        """
        year = formatYear(self.site.lang, ts.year)
        date = format_date(ts.month, ts.day, self.site)
        *_, time = str(ts).strip('Z').partition('T')
        return f'{date} {year} {time}'

    @abc.abstractmethod
    def get_page(self, item: Mapping[str, Any]) -> pywikibot.Page:
        """Get page from item."""
        ...

    def revert(self, item: Mapping[str, Any]) -> str | bool:
        """Revert a single item."""
        page = self.get_page(item)
        history = list(page.revisions(total=2))
        if len(history) <= 1:
            return False

        rev = history[1]

        pywikibot.info('\n\n>>> <<lightpurple>>{}<<default>> <<<'
                       .format(page.title(as_link=True, force_interwiki=True,
                                          textlink=True)))

        if not self.opt.rollback:
            comment = i18n.twtranslate(
                self.site, 'revertbot-revert',
                {'revid': rev.revid,
                 'author': rev.user,
                 'timestamp': self.local_timestamp(rev.timestamp)})
            if self.opt.comment:
                comment += ': ' + self.opt.comment

            old = page.text
            page.text = page.getOldVersion(rev.revid)
            pywikibot.showDiff(old, page.text)
            page.save(comment)
            return comment

        try:
            result = page.rollback(user=self.user)
        except APIError as e:
            if e.code == 'badtoken':
                pywikibot.error(
                    'There was an API token error rolling back the edit')
                return False
        except Error:
            pass
        else:
            return (f'The edit(s) made in {result["title"]} by {self.user} '
                    f'was rolled back to revision {result["last_revid"]}')

        pywikibot.exception(exc_info=False)
        return False


class BaseRevertBot(AbstractRevertBot):

    """Legacy RevertBot class using dict-like contribution mappings.

    .. version-deprecated:: 11.7
       Use :class:`ContribRevertBot` instead.
    """

    @deprecated(since='11.7.0')
    def __init__(self, site=None, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)

    def get_contributions(self, total: int = 500, ns=None):
        """Get contributions."""
        return self.site.usercontribs(user=self.user, namespaces=ns,
                                      total=total)

    def get_page(self, item: Mapping[str, Any]) -> pywikibot.Page:
        """Get page from item."""
        return pywikibot.Page(self.site, item['title'])

    @staticmethod
    def callback(item: Mapping[str, Any]) -> bool:
        """Callback function.

        .. note:: item is a dict like mapping.
        """
        return 'top' in item


class ContribRevertBot(AbstractRevertBot):

    """Base RevertBot class.

    Subclass this bot and override callback to get it to do something
    useful.

    .. version-added:: 11.7
    """

    def get_contributions(self, total: int = 500, ns=None):
        """Get contributions."""
        user = pywikibot.User(self.site, self.user)
        return user.contribs(namespaces=ns, total=total)

    def get_page(self, item: Contribution) -> pywikibot.Page:
        """Get page from item."""
        return item.page

    @staticmethod
    def callback(item: Contribution) -> bool:
        """Callback function.

        .. note:: item is a :class:`Contribution` mapping.

        :param item: the contribution information.
        """
        return item.top


class myRevertBot(BaseRevertBot):  # noqa: N801

    """Deprecated myRevertBot, for compatibility only.

    .. version-deprecated:: 11.7
    """


def main(*args: str) -> None:
    """Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}

    for arg in pywikibot.handle_args(args):
        opt, _, value = arg.partition(':')
        if not opt.startswith('-'):
            continue
        opt = opt[1:]
        if opt == 'username':
            options['user'] = value or pywikibot.input(
                'Please enter username of the person you want to revert:')
        elif opt == 'rollback':
            options[opt] = True
        elif opt == 'limit':
            options[opt] = int(value)

    bot = ContribRevertBot(**options)
    bot.revert_contribs()


if __name__ == '__main__':
    main()
