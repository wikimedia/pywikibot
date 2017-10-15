#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot appends some text to all unused images and notifies uploaders.

Parameters:

-always         Don't be asked every time.
-nouserwarning  Do not warn uploader about orphaned file.
-total          Specify number of pages to work on with "-total:n" where
                n is the maximum number of articles to work on.
                If not used, all pages are used.
"""
#
# (C) Leonardo Gregianin, 2007
# (C) Filnik, 2008
# (c) xqt, 2011-2016
# (C) Pywikibot team, 2015-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot
from pywikibot import i18n, pagegenerators, Bot

template_to_the_image = {
    'meta': '{{Orphan file}}',
    'it': u'{{immagine orfana}}',
    'fa': u'{{تصاویر بدون استفاده}}',
}

# This template message should use subst:
template_to_the_user = {
    'fa': '\n\n{{جا:اخطار به کاربر برای تصاویر بدون استفاده|%(title)s}}--~~~~',
}


class UnusedFilesBot(Bot):

    """Unused files bot."""

    def __init__(self, site, **kwargs):
        """Constructor."""
        self.availableOptions.update({
            'nouserwarning': False  # do not warn uploader
        })
        super(UnusedFilesBot, self).__init__(**kwargs)
        self.site = site

        self.template_image = i18n.translate(self.site,
                                             template_to_the_image)
        self.template_user = i18n.translate(self.site,
                                            template_to_the_user)
        self.summary = i18n.twtranslate(self.site, 'unusedfiles-comment')
        if not (self.template_image and
                (self.template_user or self.getOption('nouserwarning'))):
            raise pywikibot.Error(u'This script is not localized for %s site.'
                                  % self.site)

    def treat(self, image):
        """Process one image page."""
        if not image.exists():
            pywikibot.output("File '%s' does not exist (see bug T71133)."
                             % image.title())
            return
        # Use fileUrl() and fileIsShared() to confirm it is local media
        # rather than a local page with the same name as shared media.
        if (image.fileUrl() and not image.fileIsShared() and
                u'http://' not in image.text):
            if self.template_image in image.text:
                pywikibot.output(u"%s done already"
                                 % image.title(asLink=True))
                return

            self.append_text(image, '\n\n' + self.template_image)
            if self.getOption('nouserwarning'):
                return
            uploader = image.getFileVersionHistory().pop(0)['user']
            user = pywikibot.User(image.site, uploader)
            usertalkpage = user.getUserTalkPage()
            msg2uploader = self.template_user % {'title': image.title()}
            self.append_text(usertalkpage, msg2uploader)

    def append_text(self, page, apptext):
        """Append apptext to the page."""
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        if page.exists():
            text = page.text
        else:
            if page.isTalkPage():
                text = u''
            else:
                raise pywikibot.NoPage(page)

        oldtext = text
        text += apptext
        self.userPut(page, oldtext, text, summary=self.summary)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    options = {}
    total = None

    local_args = pywikibot.handle_args(args)

    for arg in local_args:
        arg, sep, value = arg.partition(':')
        if arg == '-total':
            total = value
        else:
            options[arg[1:]] = True

    site = pywikibot.Site()
    gen = pagegenerators.UnusedFilesGenerator(total=total, site=site)
    gen = pagegenerators.PreloadingGenerator(gen)

    bot = UnusedFilesBot(site, generator=gen, **options)
    try:
        bot.run()
    except pywikibot.Error as e:
        pywikibot.bot.suggest_help(exception=e)
        return False
    else:
        return True


if __name__ == "__main__":
    main()
