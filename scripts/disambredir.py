#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
User assisted updating redirect links on disambiguation pages.

Usage:

    python pwb.py disambredir [start]

If no starting name is provided, the bot starts at '!'.

"""
#
# (C) André Engels, 2006-2009
# (C) Pywikibot team, 2006-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot

from pywikibot import textlib, pagegenerators
from pywikibot.bot import (MultipleSitesBot, InteractiveReplace,
                           AutomaticTWSummaryBot)


class DisambiguationRedirectBot(MultipleSitesBot, AutomaticTWSummaryBot):

    """Change redirects from disambiguation pages."""

    summary_key = 'disambredir-msg'

    def _create_callback(self, old, new):
        replace_callback = InteractiveReplace(
            old, new, default='n', automatic_quit=False)
        replace_callback.allow_replace = True
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
            self.put_current(text)


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
        pywikibot.bot.suggest_help(exception=e)
        return False

    generator = pagegenerators.CategorizedPageGenerator(
        mysite.disambcategory(), start=start, content=True, namespaces=[0])

    bot = DisambiguationRedirectBot(generator=generator)
    bot.run()


if __name__ == "__main__":
    main()
