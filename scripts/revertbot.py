#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script can be used for reverting certain edits.

The following command line parameters are supported:

-username         Edits of which user need to be reverted.

-rollback         Rollback edits instead of reverting them.
                  Note that in rollback, no diff would be shown.
"""
#
# (C) Bryan Tong Minh, 2008
# (C) Pywikibot team, 2008-2017
#
# Ported by Geoffrey "GEOFBOT" Mon - User:Sn1per
# for Google Code-In 2013
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import re

import pywikibot
from pywikibot import i18n
from pywikibot.tools.formatter import color_format


class BaseRevertBot(object):

    """Base revert bot.

    Subclass this bot and override callback to get it to do something useful.

    """

    def __init__(self, site, user=None, comment=None, rollback=False):
        """Constructor."""
        self.site = site
        self.comment = comment
        self.user = user
        if not self.user:
            self.user = self.site.username()
        self.rollback = rollback

    def get_contributions(self, max=500, ns=None):
        """Get contributions."""
        return self.site.usercontribs(user=self.user, namespaces=ns, total=max)

    def revert_contribs(self, callback=None):
        """Revert contributions."""
        if callback is None:
            callback = self.callback

        for item in self.get_contributions():
            if callback(item):
                result = self.revert(item)
                if result:
                    self.log(u'%s: %s' % (item['title'], result))
                else:
                    self.log(u'Skipped %s' % item['title'])
            else:
                self.log(u'Skipped %s by callback' % item['title'])

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
        if self.comment:
            comment += ': ' + self.comment
        pywikibot.output(color_format(
            '\n\n>>> {lightpurple}{0}{default} <<<',
            page.title(asLink=True, forceInterwiki=True, textlink=True)))
        if not self.rollback:
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
        return 'The edit(s) made in %s by %s was rollbacked' % (page.title(),
                                                                self.user)

    def log(self, msg):
        """Log the message msg."""
        pywikibot.output(msg)


class RevertBot(BaseRevertBot):

    """Example revert bot."""

    def callback(self, item):
        """Callback function for 'private' revert bot.

        @param item: an item from user contributions
        @type item: dict
        @rtype: bool

        """
        if 'top' in item:
            page = pywikibot.Page(self.site, item['title'])
            text = page.get(get_redirect=True)
            pattern = re.compile(r'\[\[.+?:.+?\..+?\]\]', re.UNICODE)
            return bool(pattern.search(text))
        return False


myRevertBot = RevertBot  # for compatibility only


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    user = None
    rollback = False
    for arg in pywikibot.handle_args(args):
        if arg.startswith('-username'):
            if len(arg) == 9:
                user = pywikibot.input(
                    u'Please enter username of the person you want to revert:')
            else:
                user = arg[10:]
        elif arg == '-rollback':
            rollback = True
    bot = myRevertBot(site=pywikibot.Site(), user=user, rollback=rollback)
    bot.revert_contribs()


if __name__ == "__main__":
    main()
