#!/usr/bin/python
# -*- coding: utf-8 -*-
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

        def callback(self, item):
            '''Sample callback function for 'private' revert bot.

            @param item: an item from user contributions
            @type item: dict
            @rtype: bool
            '''
            if 'top' in item:
                page = pywikibot.Page(self.site, item['title'])
                text = page.get(get_redirect=True)
                pattern = re.compile(r'\[\[.+?:.+?\..+?\]\]', re.UNICODE)
                return bool(pattern.search(text))
            return False

"""
#
# (C) Pywikibot team, 2008-2019
#
# Ported by Geoffrey "GEOFBOT" Mon - User:Sn1per
# for Google Code-In 2013
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import pywikibot

from pywikibot.bot import OptionHandler
from pywikibot import i18n
from pywikibot.tools import deprecate_arg
from pywikibot.tools.formatter import color_format


class BaseRevertBot(OptionHandler):

    """Base revert bot.

    Subclass this bot and override callback to get it to do something useful.
    """

    availableOptions = {
        'comment': '',
        'rollback': False,
        'limit': 500
    }

    def __init__(self, site=None, **kwargs):
        """Initializer."""
        self.site = site or pywikibot.Site()
        self.user = kwargs.pop('user', self.site.username())
        super(BaseRevertBot, self).__init__(**kwargs)

    @deprecate_arg('max', 'total')
    def get_contributions(self, total=500, ns=None):
        """Get contributions."""
        return self.site.usercontribs(user=self.user, namespaces=ns,
                                      total=total)

    def revert_contribs(self, callback=None):
        """Revert contributions."""
        if callback is None:
            callback = self.callback

        for item in self.get_contributions(total=self.getOption('limit')):
            if callback(item):
                result = self.revert(item)
                if result:
                    self.log('{0}: {1}'.format(item['title'], result))
                else:
                    self.log('Skipped {0}'.format(item['title']))
            else:
                self.log('Skipped {0} by callback'.format(item['title']))

    def callback(self, item):
        """Callback function."""
        return 'top' in item

    def revert(self, item):
        """Revert a single item."""
        page = pywikibot.Page(self.site, item['title'])
        history = list(page.revisions(total=2))
        if len(history) > 1:
            rev = history[1]
        else:
            return False

        comment = i18n.twtranslate(
            self.site, 'revertbot-revert',
            {'revid': rev.revid,
             'author': rev.user,
             'timestamp': rev.timestamp})
        additional_comment = self.getOption('comment')
        if additional_comment:
            comment += ': ' + additional_comment

        pywikibot.output(color_format(
            '\n\n>>> {lightpurple}{0}{default} <<<',
            page.title(as_link=True, force_interwiki=True, textlink=True)))

        if not self.getOption('rollback'):
            old = page.text
            page.text = page.getOldVersion(rev.revid)
            pywikibot.showDiff(old, page.text)
            page.save(comment)
            return comment

        try:
            pywikibot.data.api.Request(
                self.site, parameters={'action': 'rollback',
                                       'title': page,
                                       'user': self.user,
                                       'token': rev.rollbacktoken,
                                       'markbot': True}).submit()
        except pywikibot.data.api.APIError as e:
            if e.code == 'badtoken':
                pywikibot.error(
                    'There was an API token error rollbacking the edit')
            else:
                pywikibot.exception()
            return False
        return 'The edit(s) made in {0} by {1} was rollbacked'.format(
            page.title(), self.user)

    def log(self, msg):
        """Log the message msg."""
        pywikibot.output(msg)


# for compatibility only
myRevertBot = BaseRevertBot  # noqa: N816


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
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
