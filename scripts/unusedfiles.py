#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot appends some text to all unused images and notifies uploaders.

Parameters:

-always         Don't be asked every time.
-nouserwarning  Do not warn uploader about orphaned file.
-limit          Specify number of pages to work on with "-limit:n" where
                n is the maximum number of articles to work on.
                If not used, all pages are used.
"""
#
# (C) Pywikibot team, 2007-2020
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import SingleSiteBot, AutomaticTWSummaryBot, ExistingPageBot
from pywikibot.flow import Board

template_to_the_image = {
    'meta': '{{Orphan file}}',
    'test': '{{Orphan file}}',
    'it': '{{immagine orfana}}',
    'fa': '{{تصاویر بدون استفاده}}',
    'ur': '{{غیر مستعمل تصاویر}}',
}

template_to_the_user = {
    'fa': '{{جا:اخطار به کاربر برای تصاویر بدون استفاده|%(title)s}}',
    'ur': '{{جا:اطلاع برائے غیر مستعمل تصاویر}}',
    'test': '{{User:Happy5214/Unused file notice (user)|%(title)s}}',
}


class UnusedFilesBot(SingleSiteBot, AutomaticTWSummaryBot, ExistingPageBot):

    """Unused files bot."""

    summary_key = 'unusedfiles-comment'

    def __init__(self, **kwargs):
        """Initializer."""
        self.available_options.update({
            'nouserwarning': False  # do not warn uploader
        })
        super().__init__(**kwargs)

        self.template_image = i18n.translate(self.site,
                                             template_to_the_image)
        self.template_user = i18n.translate(self.site,
                                            template_to_the_user)
        if not (self.template_image
                and (self.template_user or self.opt.nouserwarning)):
            raise i18n.TranslationError('This script is not localized for {0} '
                                        'site.'.format(self.site))

    def treat(self, image):
        """Process one image page."""
        # Use get_file_url() and file_is_shared() to confirm it is local media
        # rather than a local page with the same name as shared media.
        if (image.get_file_url() and not image.file_is_shared()
                and 'http://' not in image.text):
            if self.template_image in image.text:
                pywikibot.output('{0} done already'
                                 .format(image.title(as_link=True)))
                return

            self.append_text(image, '\n\n' + self.template_image)
            if self.opt.nouserwarning:
                return
            uploader = image.get_file_history().pop(0)['user']
            user = pywikibot.User(image.site, uploader)
            usertalkpage = user.getUserTalkPage()
            template2uploader = self.template_user % {'title': image.title()}
            msg2uploader = self.site.expand_text(template2uploader)
            if usertalkpage.is_flow_page():
                self.post_to_flow_board(usertalkpage, msg2uploader)
            else:
                self.append_text(usertalkpage, '\n\n' + msg2uploader + ' ~~~~')

    def append_text(self, page, apptext):
        """Append apptext to the page."""
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        if page.exists():
            text = page.text
        else:
            if page.isTalkPage():
                text = ''
            else:
                raise pywikibot.NoPage(page)

        text += apptext
        self.current_page = page
        self.put_current(text)

    def post_to_flow_board(self, page, post):
        """Post message as a Flow topic."""
        board = Board(page)
        header, rest = post.split('\n', 1)
        title = header.strip('=')
        content = rest.lstrip()
        board.new_topic(title, content)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    options = {}
    total = None

    local_args = pywikibot.handle_args(args)

    for arg in local_args:
        arg, sep, value = arg.partition(':')
        if arg == '-limit':
            total = value
        else:
            options[arg[1:]] = True

    site = pywikibot.Site()
    gen = pagegenerators.UnusedFilesGenerator(total=total, site=site)
    gen = pagegenerators.PreloadingGenerator(gen)

    bot = UnusedFilesBot(site=site, generator=gen, **options)
    try:
        bot.run()
    except pywikibot.Error as e:
        pywikibot.bot.suggest_help(exception=e)


if __name__ == '__main__':
    main()
