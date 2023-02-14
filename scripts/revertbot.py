#!/usr/bin/env python3
r"""
This script can be used for reverting certain edits.

The following command line parameters are supported:

-username         Edits of which user need to be reverted.
                  Default is bot's username (site.username())

-rollback         Rollback edits instead of reverting them.
                  Note that in rollback, no diff would be shown.

-limit:num        Use the last num contributions to be checked for revert.
                  Default is 500.

Users who want to customize the behaviour should subclass the `BaseRevertBot`
and override its `callback` method. Here is a sample:

    class myRevertBot(BaseRevertBot):

        '''Example revert bot.'''

        def callback(self, item) -> bool:
            '''Sample callback function for 'private' revert bot.

            :param item: an item from user contributions
            :type item: dict
            '''
            if 'top' in item:
                page = pywikibot.Page(self.site, item['title'])
                text = page.get(get_redirect=True)
                pattern = re.compile(r'\[\[.+?:.+?\..+?\]\]')
                return bool(pattern.search(text))
            return False

"""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
from typing import Union

import pywikibot
from pywikibot import i18n
from pywikibot.backports import Container
from pywikibot.bot import OptionHandler
from pywikibot.date import format_date, formatYear
from pywikibot.exceptions import APIError, Error


class BaseRevertBot(OptionHandler):

    """Base revert bot.

    Subclass this bot and override callback to get it to do something useful.
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

    def get_contributions(self, total: int = 500, ns=None):
        """Get contributions."""
        return self.site.usercontribs(user=self.user, namespaces=ns,
                                      total=total)

    def revert_contribs(self, callback=None) -> None:
        """Revert contributions."""
        if callback is None:
            callback = self.callback

        for item in self.get_contributions(total=self.opt.limit):
            if callback(item):
                result = self.revert(item)
                if result:
                    pywikibot.info('{}: {}'.format(item['title'], result))
                else:
                    pywikibot.info('Skipped {}'.format(item['title']))
            else:
                pywikibot.info('Skipped {} by callback'.format(item['title']))

    @staticmethod
    def callback(item: Container) -> bool:
        """Callback function."""
        return 'top' in item

    def local_timestamp(self, ts) -> str:
        """Convert Timestamp to a localized timestamp string.

        .. versionadded:: 7.0
        """
        year = formatYear(self.site.lang, ts.year)
        date = format_date(ts.month, ts.day, self.site)
        *_, time = str(ts).strip('Z').partition('T')
        return ' '.join((date, year, time))

    def revert(self, item) -> Union[str, bool]:
        """Revert a single item."""
        page = pywikibot.Page(self.site, item['title'])
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
            self.site.rollbackpage(page, user=self.user, markbot=True)
        except APIError as e:
            if e.code == 'badtoken':
                pywikibot.error(
                    'There was an API token error rollbacking the edit')
                return False
        except Error:
            pass
        else:
            return 'The edit(s) made in {} by {} was rollbacked'.format(
                page.title(), self.user)

        pywikibot.exception(exc_info=False)
        return False


# for compatibility only
myRevertBot = BaseRevertBot  # noqa: N816


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

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

    bot = myRevertBot(**options)
    bot.revert_contribs()


if __name__ == '__main__':
    main()
