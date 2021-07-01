#!/usr/bin/python
"""
User assisted updating redirect links on disambiguation pages.

Usage:

    python pwb.py disambredir [start]

If no starting name is provided, the bot starts at '!'.

"""
#
# (C) Pywikibot team, 2006-2020
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import pagegenerators, textlib
from pywikibot.bot import (
    AutomaticTWSummaryBot,
    InteractiveReplace,
    MultipleSitesBot,
)
from pywikibot.exceptions import Error, SectionError


class DisambiguationRedirectBot(MultipleSitesBot, AutomaticTWSummaryBot):

    """Change redirects from disambiguation pages."""

    summary_key = 'disambredir-msg'

    def _create_callback(self, old, new):
        replace_callback = InteractiveReplace(
            old, new, default='n')
        replace_callback.allow_replace = True
        replace_callback.allow_replace_label = True
        replace_callback.allow_replace_section = True
        replace_callback.allow_replace_all = True
        return replace_callback

    def treat_page(self):
        """Iterate over linked pages and replace redirects conditionally."""
        text = self.current_page.text
        for linked_page in self.current_page.linkedPages():
            try:
                target = linked_page.getRedirectTarget()
            except (Error, SectionError):
                continue
            # TODO: Work on all links at the same time (would mean that the
            # user doesn't get them ordered like in links but how they appear
            # in the page)
            text = textlib.replace_links(
                text, self._create_callback(linked_page, target),
                self.current_page.site)

        if text != self.current_page.get():
            self.put_current(text)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    local_args = pywikibot.handle_args(args)

    start = local_args[0] if local_args else '!'

    mysite = pywikibot.Site()
    try:
        mysite.disambcategory()
    except Error as e:
        pywikibot.bot.suggest_help(exception=e)
        return

    generator = pagegenerators.CategorizedPageGenerator(
        mysite.disambcategory(), start=start, content=True, namespaces=[0])

    bot = DisambiguationRedirectBot(generator=generator)
    bot.run()


if __name__ == '__main__':
    main()
