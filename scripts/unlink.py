#!/usr/bin/env python3
"""This bot unlinks a page on every page that links to it.

This script understands this command-line argument:

-always       Don't prompt you for each replacement.

-namespace:n  Number of namespace to process. The parameter can be used
              multiple times.

Any other parameter will be regarded as the title of the page
that should be unlinked.

Example
-------

Removes links to the page [[Foo bar]] in articles and image
descriptions:

    python pwb.py unlink "Foo bar" -namespace:0 -namespace:6


.. versionchanged:: 6.0
   script was archived.
.. versionchanged:: 7.0
   script was deleted.
.. versionchanged:: 9.4
   script was recovered.
"""
#
# (C) Pywikibot team, 2007-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import pywikibot
from pywikibot.bot import SingleSiteBot
from pywikibot.specialbots import BaseUnlinkBot


class UnlinkBot(SingleSiteBot, BaseUnlinkBot):

    """A bot unlinking the given link from the current page."""

    summary_key = 'unlink-unlinking'

    def __init__(self, page_title: str, **kwargs):
        """Initialize a UnlinkBot instance with the given page to unlink."""
        super().__init__(**kwargs)
        self.pageToUnlink = pywikibot.Page(self.site, page_title)  # noqa: N803
        self.generator = self.pageToUnlink.getReferences(
            namespaces=self.opt.namespaces, content=True)

    @property
    def summary_parameters(self):
        """Return the title parameter."""
        return {'title': self.pageToUnlink.title()}

    def treat_page(self):
        """Remove links pointing to the configured page from the given page."""
        self.unlink(self.pageToUnlink)


def main(*args: str) -> None:
    """Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    # This temporary string is used to read the title
    # of the page that should be unlinked.
    page_title: str = ''
    options = {}

    for arg in pywikibot.handle_args(args):
        opt, _, value = arg.partition(':')
        if opt == '-namespace':
            options.setdefault('namespaces', [])
            try:
                options['namespaces'].append(int(value))
            except ValueError:
                options['namespaces'].append(value)
        elif arg == '-always':
            options['always'] = True
        else:
            page_title = arg

    if page_title:
        bot = UnlinkBot(page_title, **options)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_parameters=['page title'])


if __name__ == '__main__':
    main()
