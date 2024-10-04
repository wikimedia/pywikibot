#!/usr/bin/env python3
"""
This bot appends some text to all unused images and notifies uploaders.

Parameters:

-limit          Specify number of pages to work on with "-limit:n" where
                n is the maximum number of articles to work on.
                If not used, all pages are used.
-always         Don't be asked every time.

This script is a :py:obj:`ConfigParserBot <bot.ConfigParserBot>`.
The following options can be set within a settings file which is scripts.ini
by default::

-nouserwarning  Do not warn uploader about orphaned file.
-filetemplate:  Use a custom template on unused file pages.
-usertemplate:  Use a custom template to warn the uploader.
"""
#
# (C) Pywikibot team, 2007-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import re

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import (
    AutomaticTWSummaryBot,
    ConfigParserBot,
    ExistingPageBot,
    SingleSiteBot,
)
from pywikibot.exceptions import Error, NoPageError, TranslationError


template_to_the_image = {
    'meta': '{{Orphan file}}',
    'test': '{{Orphan file}}',
    'ar': '{{ملف يتيم}}',
    'ary': '{{Orphan file}}',
    'arz': '{{فايل يتيم}}',
    'ckb': '{{سخ-پ٥|ڕێکەوت={{subst:ڕێکەوت}}}}',
    'en': '{{Orphan file}}',
    'fa': '{{تصاویر بدون استفاده}}',
    'id': '{{Berkas yatim}}',
    'it': '{{immagine orfana}}',
    'mk': '{{Слика сираче}}',
    'te': '{{Orphan image}}',
    'ur': '{{غیر مستعمل تصاویر}}',
    'uz': '{{Yetim tasvir}}',
    'vec': '{{Imaxine orfana}}',
    'vi': '{{Hình mồ côi}}',
}

template_to_the_user = {
    'test': '{{User:Happy5214/Unused file notice (user)|%(title)s}}',
    'ar': '{{subst:تنبيه صورة يتيمة|%(title)s}}',
    'ary': '{{subst:تنبيه صورة يتيمة|%(title)s}}',
    'arz': '{{subst:تنبيه صوره يتيمه|%(title)s}}',
    'ckb': '{{subst:سخ-پ٥-ئاگاداری|1=%(title)s}}',
    'fa': '{{subst:اخطار به کاربر برای تصاویر بدون استفاده|%(title)s}}',
    'ur': '{{subst:اطلاع برائے غیر مستعمل تصاویر|%(title)s}}',
}


class UnusedFilesBot(SingleSiteBot,
                     AutomaticTWSummaryBot,
                     ConfigParserBot,
                     ExistingPageBot):

    """Unused files bot.

    .. versionchanged:: 7.0
       UnusedFilesBot is a ConfigParserBot
    """

    summary_key = 'unusedfiles-comment'
    update_options = {
        'nouserwarning': False,  # do not warn uploader
        'filetemplate': '',
        'usertemplate': '',
    }

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)

        # handle the custom templates
        if not self.opt.filetemplate:
            self.opt.filetemplate = i18n.translate(self.site,
                                                   template_to_the_image)
        elif not re.fullmatch('{{.+}}', self.opt.filetemplate):
            self.opt.filetemplate = '{{%s}}' % self.opt.filetemplate

        if not self.opt.usertemplate:
            self.opt.usertemplate = i18n.translate(self.site,
                                                   template_to_the_user)
        elif not re.fullmatch('{{.+}}', self.opt.usertemplate):
            self.opt.usertemplate = '{{%s}}' % self.opt.usertemplate

        if not (self.opt.filetemplate
                and (self.opt.usertemplate or self.opt.nouserwarning)):
            # if no templates are given
            raise TranslationError(
                f'This script is not localized for {self.site} site;\n'
                'try using -filetemplate:<template name>.')

    def skip_page(self, image: pywikibot.page.FilePage) -> bool:
        """Skip processing on repository images or if image is already tagged.

        Use get_file_url() and file_is_shared() to confirm it is local
        media rather than a local page with the same name as shared
        media.
        """
        if not image.get_file_url() or image.file_is_shared() \
           or 'http://' in image.text:
            return True

        if self.opt.filetemplate in image.text:
            pywikibot.info(f'{image} done already')
            return True

        return super().skip_page(image)

    def treat(self, image) -> None:
        """Process one image page."""
        self.append_text(image, '\n\n' + self.opt.filetemplate)

        if self.opt.nouserwarning:
            return

        uploader = image.oldest_file_info.user
        user = pywikibot.User(image.site, uploader)
        usertalkpage = user.getUserTalkPage()
        msg2uploader = self.opt.usertemplate % {'title': image.title()}
        if usertalkpage.is_flow_page():
            pywikibot.warning(f'Unsupported Flow talkpage {usertalkpage};'
                              '\n         uploader cannot be informed.')
        else:
            self.append_text(usertalkpage, '\n\n' + msg2uploader + ' ~~~~')

    def append_text(self, page, apptext):
        """Append apptext to the page."""
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        if page.exists():
            text = page.text
        else:
            if not page.isTalkPage():
                raise NoPageError(page)
            text = ''

        text += apptext
        self.current_page = page
        self.put_current(text)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}
    total = None

    local_args = pywikibot.handle_args(args)

    for arg in local_args:
        arg, _, value = arg.partition(':')
        if arg == '-limit':
            total = value
        elif arg == '-filetemplate':
            options['filetemplate'] = value
        elif arg == '-usertemplate':
            options['usertemplate'] = value
        else:
            options[arg[1:]] = True

    site = pywikibot.Site()
    gen = site.unusedfiles(total=total)
    gen = pagegenerators.PreloadingGenerator(gen)

    bot = UnusedFilesBot(site=site, generator=gen, **options)
    try:
        bot.run()
    except Error as e:
        pywikibot.bot.suggest_help(exception=e)


if __name__ == '__main__':
    main()
