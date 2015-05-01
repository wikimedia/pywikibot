#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This bot appends some text to all unused images and notifies uploaders.

Parameters:

-always     Don't be asked every time.

"""
#
# (C) Leonardo Gregianin, 2007
# (C) Filnik, 2008
# (c) xqt, 2011-2014
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import pywikibot
from pywikibot import i18n, pagegenerators, Bot

comment = {
    'ar': u'صور للاستبعاد',
    'en': u'images for elimination',
    'fa': u'تصویر استفاده نشده',
    'he': u'תמונות להסרה',
    'it': u'Bot: segnalo immagine orfana da eliminare',
    'pt': u'Bot: marcação de imagens para eliminação',
}

template_to_the_image = {
    'en': u'{{subst:No-use2}}',
    'it': u'{{immagine orfana}}',
    'fa': u'{{تصاویر بدون استفاده}}',
}
template_to_the_user = {
    'en': u'\n\n{{img-sem-uso|%(title)s}}',
    'fa': u'\n\n{{جا:اخطار به کاربر برای تصاویر بدون استفاده|%(title)s}}--~~~~',
    'it': u'\n\n{{Utente:Filbot/Immagine orfana}}',
}


class UnusedFilesBot(Bot):

    """Unused files bot."""

    def __init__(self, site, **kwargs):
        """Constructor."""
        super(UnusedFilesBot, self).__init__(**kwargs)
        self.site = site

    def run(self):
        """Start the bot."""
        template_image = i18n.translate(self.site,
                                        template_to_the_image)
        template_user = i18n.translate(self.site,
                                       template_to_the_user)
        summary = i18n.translate(self.site, comment, fallback=True)
        if not all([template_image, template_user, comment]):
            raise pywikibot.Error(u'This script is not localized for %s site.'
                                  % self.site)
        self.summary = summary
        generator = pagegenerators.UnusedFilesGenerator(site=self.site)
        generator = pagegenerators.PreloadingGenerator(generator)
        for image in generator:
            if not image.exists():
                pywikibot.output(u"File '%s' does not exist (see bug 69133)."
                                 % image.title())
                continue
            # Use fileUrl() and fileIsShared() to confirm it is local media
            # rather than a local page with the same name as shared media.
            if (image.fileUrl() and not image.fileIsShared() and
                    u'http://' not in image.text):
                if template_image in image.text:
                    pywikibot.output(u"%s done already"
                                     % image.title(asLink=True))
                    continue
                self.append_text(image, u"\n\n" + template_image)
                uploader = image.getFileVersionHistory().pop(0)['user']
                user = pywikibot.User(image.site, uploader)
                usertalkpage = user.getUserTalkPage()
                msg2uploader = template_user % {'title': image.title()}
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

    for arg in pywikibot.handle_args(args):
        if arg == '-always':
            options['always'] = True

    bot = UnusedFilesBot(pywikibot.Site(), **options)
    try:
        bot.run()
    except pywikibot.Error as e:
        pywikibot.showHelp()
        pywikibot.warning(e)


if __name__ == "__main__":
    main()
