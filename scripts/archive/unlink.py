#!/usr/bin/python
"""
This bot unlinks a page on every page that links to it.

This script understands this command-line argument:

    -namespace:n   Number of namespace to process. The parameter can be used
                   multiple times. It works in combination with all other
                   parameters, except for the -start parameter. If you e.g.
                   want to iterate over all user pages starting at User:M, use
                   -start:User:M.

Any other parameter will be regarded as the title of the page
that should be unlinked.

Example
-------

Removes links to the page [[Foo bar]] in articles and image
descriptions:

    python pwb.py unlink "Foo bar" -namespace:0 -namespace:6
"""
#
# (C) Pywikibot team, 2007-2020
#
# Distributed under the terms of the MIT license.
#

import pywikibot
from pywikibot.bot import SingleSiteBot
from pywikibot.specialbots import BaseUnlinkBot


class UnlinkBot(SingleSiteBot, BaseUnlinkBot):

    """A bot unlinking the given link from the current page."""

    summary_key = 'unlink-unlinking'

    def __init__(self, pageToUnlink, **kwargs):
        """Initialize a UnlinkBot instance with the given page to unlink."""
        super().__init__(**kwargs)
        self.pageToUnlink = pageToUnlink
        self.generator = pageToUnlink.getReferences(
            namespaces=self.opt.namespaces, content=True)

    @property
    def summary_parameters(self):
        """Return the title parameter."""
        return {'title': self.pageToUnlink.title()}

    def treat_page(self):
        """Remove links pointing to the configured page from the given page."""
        self.unlink(self.pageToUnlink)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    # This temporary string is used to read the title
    # of the page that should be unlinked.
    page_title = None
    options = {}

    for arg in pywikibot.handle_args(args):
        if arg.startswith('-namespace:'):
            if 'namespaces' not in options:
                options['namespaces'] = []
            try:
                options['namespaces'].append(int(arg[11:]))
            except ValueError:
                options['namespaces'].append(arg[11:])
        elif arg == '-always':
            options['always'] = True
        else:
            page_title = arg

    if page_title:
        page = pywikibot.Page(pywikibot.Site(), page_title)
        bot = UnlinkBot(page, **options)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_parameters=['page title'])


if __name__ == '__main__':
    main()
