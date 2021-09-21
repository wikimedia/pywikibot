#!/usr/bin/python
"""
Allows access to the bot account's watchlist.

The watchlist can be updated manually by running this script.

Syntax:

    python pwb.py watchlist [-all | -count | -count:all | -new]

Command line options:

-all         Reloads watchlists for all wikis where a watchlist is already
             present
-count       Count only the total number of pages on the watchlist of the
             account the bot has access to
-count:all   Count only the total number of pages on all wikis watchlists
             that the bot is connected to.
-new         Load watchlists for all wikis where accounts is setting in
             user-config.py
"""
#
# (C) Pywikibot team, 2005-2021
#
# Distributed under the terms of the MIT license.
#
import os

import pywikibot
from pywikibot import config
from pywikibot.data.api import CachedRequest
from pywikibot.exceptions import InvalidTitleError
from scripts.maintenance.cache import CacheEntry


def get(site=None):
    """Load the watchlist, fetching it if necessary."""
    if site is None:
        site = pywikibot.Site()
    watchlist = [p.title() for p in site.watched_pages()]
    return watchlist


def count_watchlist(site=None):
    """Count only the total number of page(s) in watchlist for this wiki."""
    if site is None:
        site = pywikibot.Site()
    watchlist_count = len(refresh(site))
    pywikibot.output('There are {} page(s) in the watchlist.'
                     .format(watchlist_count))


def count_watchlist_all():
    """Count only the total number of page(s) in watchlist for all wikis."""
    wl_count_all = 0
    pywikibot.output('Counting pages in watchlists of all wikis...')
    for family in config.usernames:
        for lang in config.usernames[family]:
            site = pywikibot.Site(lang, family)
            wl_count_all += len(refresh(site))
    pywikibot.output('There are a total of {} page(s) in the watchlists'
                     'for all wikis.'.format(wl_count_all))


def isWatched(pageName, site=None):  # noqa N802, N803
    """Check whether a page is being watched."""
    watchlist = get(site)
    return pageName in watchlist


def refresh(site):
    """Fetch the watchlist."""
    pywikibot.output('Retrieving watchlist for {}.'.format(str(site)))
    return list(site.watched_pages(force=True))


def refresh_all():
    """Reload watchlists for all wikis where a watchlist is already present."""
    cache_path = CachedRequest._get_cache_dir()
    files = os.scandir(cache_path)
    seen = set()
    for filename in files:
        entry = CacheEntry(cache_path, filename)
        entry._load_cache()
        entry.parse_key()
        entry._rebuild()
        if entry.site not in seen and 'watchlistraw' in entry._data:
            refresh(entry.site)
            seen.add(entry.site)


def refresh_new():
    """Load watchlists of all wikis for accounts set in user-config.py."""
    pywikibot.output(
        'Downloading all watchlists for your accounts in user-config.py')
    for family in config.usernames:
        for lang in config.usernames[family]:
            site = pywikibot.Site(lang, family)
            refresh(site)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    opt_all = False
    opt_new = False
    opt_count = False
    opt_count_all = False
    for arg in pywikibot.handle_args(args):
        if arg in ('-all', '-update'):
            opt_all = True
        elif arg == '-new':
            opt_new = True
        elif arg == '-count':
            opt_count = True
        elif arg == '-count:all':
            opt_count_all = True
    if opt_all:
        refresh_all()
    elif opt_new:
        refresh_new()
    elif opt_count:
        count_watchlist()
    elif opt_count_all:
        count_watchlist_all()
    else:
        site = pywikibot.Site()
        count_watchlist(site)
        watchlist = list(site.watched_pages(force=True))
        for page in watchlist:
            try:
                pywikibot.stdout(page.title())
            except InvalidTitleError:
                pywikibot.exception()


if __name__ == '__main__':
    main()
