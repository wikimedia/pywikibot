#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This script can be used for reverting certain edits.

The following command line parameters are supported:

&params;

-username         Edits of which user need to be reverted.
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
    """ Base revert bot

    Subclass this bot and override callback to get it to do something useful.

    """
    def __init__(self, site, user=None, comment=None):
        self.site = site
        self.comment = comment
        self.user = user
        if not self.user:
            self.user = self.site.username()

    def get_contributions(self, max=500, ns=None):
        count = 0
        iterator = iter(xrange(0))
        never_continue = False
        while count != max or never_continue:
            try:
                item = iterator.next()
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
        if len(pywikibot.Page(pywikibot.Site(), item['title']).fullVersionHistory(total=2)) > 1:
            rev = pywikibot.Page(pywikibot.Site(), item['title']).fullVersionHistory(total=2)[1]
        else:
            return False

        comment = i18n.twtranslate(pywikibot.Site(), 'revertbot-revert', {'revid': rev[0], 'author': rev[2], 'timestamp': rev[1]})

        if self.comment:
            comment += ': ' + self.comment

        page = pywikibot.Page(self.site, item['title'])
        pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                         % page.title(asLink=True, forceInterwiki=True,
                                      textlink=True))
        old = page.text
        page.text = rev[3]
        pywikibot.showDiff(old, page.text)
        page.save(comment)
        return comment

    def log(self, msg):
        pywikibot.output(msg)


class myRevertBot(BaseRevertBot):

    def callback(self, item):
        if 'top' in item:
            page = pywikibot.Page(self.site, item['title'])
            text = page.get()
            pattern = re.compile(u'\[\[.+?:.+?\..+?\]\]', re.UNICODE)
            return pattern.search(text) >= 0
        return False


def main():
    user = None
    for arg in pywikibot.handleArgs():
        if arg.startswith('-username'):
            if len(arg) == 9:
                user = pywikibot.input(
                    u'Please enter username of the person you want to revert:')
            else:
                user = arg[10:]
    bot = myRevertBot(site=pywikibot.Site(), user=user)
    bot.revert_contribs()

if __name__ == "__main__":
    main()
