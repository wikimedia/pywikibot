#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
User assisted updating redirect links on disambiguation pages.

Usage:
    python disambredir.py [start]

If no starting name is provided, the bot starts at '!'.

"""
#
# (C) André Engels, 2006-2009
# (C) Pywikibot team, 2006-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#
import pywikibot

from pywikibot import i18n, textlib, pagegenerators
from pywikibot.bot import MultipleSitesBot, CurrentPageBot, InteractiveReplace

msg = {
    'ar': u'تغيير التحويلات في صفحة توضيح',
    'be-x-old': u'Замена перанакіраваньняў на старонку неадназначнасьцяў',
    'en': u'Changing redirects on a disambiguation page',
    'he': u'משנה קישורים להפניות בדף פירושונים',
    'fa': u'اصلاح تغییرمسیرها در یک صفحه ابهام‌زدایی',
    'ja': u'ロボットによる: 曖昧さ回避ページのリダイレクト修正',
    'nl': u'Verandering van redirects op een doorverwijspagina',
    'pl': u'Zmiana przekierowań na stronie ujednoznaczającej',
    'pt': u'Arrumando redirects na página de desambiguação',
    'ru': u'Изменение перенаправлений на странице неоднозначности',
    'uk': u'Зміна перенаправлень на сторінці багатозначності',
    'zh': u'機器人: 修改消歧義頁中的重定向連結',
}


class DisambiguationRedirectBot(MultipleSitesBot, CurrentPageBot):

    """Change redirects from disambiguation pages."""

    def _create_callback(self, old, new):
        replace_callback = InteractiveReplace(
            old, new, default='n', automatic_quit=False)
        replace_callback.allow_replace_label = True
        replace_callback.allow_replace_section = True
        replace_callback.allow_replace_all = True
        return replace_callback

    def treat_page(self):
        """Iterate over the linked pages and replace redirects conditionally."""
        text = self.current_page.text
        for linked_page in self.current_page.linkedPages():
            try:
                target = linked_page.getRedirectTarget()
            except (pywikibot.Error, pywikibot.SectionError):
                continue
            # TODO: Work on all links at the same time (would mean that the user
            # doesn't get them ordered like in links but how they appear in the page)
            text = textlib.replace_links(
                text, self._create_callback(linked_page, target),
                self.current_page.site)

        if text != self.current_page.get():
            summary = i18n.translate(self.current_page.site, msg, fallback=True)
            self.put_current(text, summary=summary)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    local_args = pywikibot.handle_args(args)

    start = local_args[0] if local_args else '!'

    mysite = pywikibot.Site()
    try:
        mysite.disambcategory()
    except pywikibot.Error as e:
        pywikibot.output(e)
        pywikibot.showHelp()
        return

    generator = pagegenerators.CategorizedPageGenerator(
        mysite.disambcategory(), start=start, content=True, namespaces=[0])

    bot = DisambiguationRedirectBot(generator=generator)
    bot.run()


if __name__ == "__main__":
    main()
