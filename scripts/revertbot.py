#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This script can be used for reverting certain edits.

The following command line parameters are supported:

&params;

-username         Edits of which user need to be reverted.

-rollback         Rollback edits instead of reverting them.
                  Note that in rollback, no diff would be shown.
"""
#
# (C) Bryan Tong Minh, 2008
# (C) Pywikibot team, 2008-2014
#
# Ported by Geoffrey "GEOFBOT" Mon - User:Sn1per
# for Google Code-In 2013
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import re
import pywikibot
from pywikibot import i18n
from pywikibot import pagegenerators

docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class BaseRevertBot(object):

    """Base revert bot.

    Subclass this bot and override callback to get it to do something useful.

    """

    def __init__(self, site, user=None, comment=None, rollback=False):
        self.site = site
        self.comment = comment
        self.user = user
        if not self.user:
            self.user = self.site.username()
        self.rollback = rollback

    def get_contributions(self, max=500, ns=None):
        count = 0
        iterator = pywikibot.tools.empty_iterator()
        never_continue = False
        while count != max or never_continue:
            try:
                item = next(iterator)
            except StopIteration:
                self.log(u'Fetching new batch of contributions')
                data = list(pywikibot.Site().usercontribs(user=self.user, namespaces=ns, total=max))
                never_continue = True
                iterator = iter(data)
            else:
                count += 1
                yield item

    def revert_contribs(self, callback=None):

        if callback is None:
            callback = self.callback

        contribs = self.get_contributions()
        for item in contribs:
            try:
                if callback(item):
                    result = self.revert(item)
                    if result:
                        self.log(u'%s: %s' % (item['title'], result))
                    else:
                        self.log(u'Skipped %s' % item['title'])
                else:
                    self.log(u'Skipped %s by callback' % item['title'])
            except StopIteration:
                return

    def callback(self, item):
        return 'top' in item

    def revert(self, item):
        history = pywikibot.Page(self.site, item['title']).fullVersionHistory(
            total=2, rollback=self.rollback)
        if len(history) > 1:
            rev = history[1]
        else:
            return False
        comment = i18n.twtranslate(pywikibot.Site(), 'revertbot-revert', {'revid': rev[0], 'author': rev[2], 'timestamp': rev[1]})
        if self.comment:
            comment += ': ' + self.comment
        page = pywikibot.Page(self.site, item['title'])
        pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                         % page.title(asLink=True, forceInterwiki=True,
                                      textlink=True))
        if not self.rollback:
            old = page.text
            page.text = rev[3]
            pywikibot.showDiff(old, page.text)
            page.save(comment)
            return comment
        try:
            pywikibot.data.api.Request(action="rollback", title=page.title(), user=self.user,
                                           token=rev[4], markbot=1).submit()
        except pywikibot.data.api.APIError as e:
            if e.code == 'badtoken':
                pywikibot.error("There was an API token error rollbacking the edit")
            else:
                pywikibot.exception()
            return False
        return u"The edit(s) made in %s by %s was rollbacked" % (page.title(), self.user)

    def log(self, msg):
        pywikibot.output(msg)


class myRevertBot(BaseRevertBot):

    """Example revert bot."""

    def callback(self, item):
        if 'top' in item:
            page = pywikibot.Page(self.site, item['title'])
            text = page.get(get_redirect=True)
            pattern = re.compile(r'\[\[.+?:.+?\..+?\]\]', re.UNICODE)
            return pattern.search(text) >= 0
        return False


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
