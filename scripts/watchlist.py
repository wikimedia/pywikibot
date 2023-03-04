#!/usr/bin/env python3
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
-new         Load watchlists for all wikis where accounts is set in user
             config file

.. versionchanged:: 7.7
   watchlist is retrieved in parallel tasks.
"""
#
# (C) Pywikibot team, 2005-2022
#
# Distributed under the terms of the MIT license.
#
import datetime
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import pywikibot
from pywikibot import config
from pywikibot.backports import List
from pywikibot.data.api import CachedRequest
from pywikibot.exceptions import InvalidTitleError
from scripts.maintenance.cache import CacheEntry


def get(site=None) -> List[str]:
    """Load the watchlist, fetching it if necessary."""
    if site is None:
        site = pywikibot.Site()
    return [p.title() for p in site.watched_pages()]


def count_watchlist(site=None) -> None:
    """Count only the total number of page(s) in watchlist for this wiki."""
    if site is None:
        site = pywikibot.Site()
    watchlist_count = len(refresh(site))
    pywikibot.info(f'There are {watchlist_count} page(s) in the watchlist.')


def count_watchlist_all(quiet=False) -> None:
    """Count only the total number of page(s) in watchlist for all wikis."""
    if not quiet:
        pywikibot.info('Counting pages in watchlists of all wikis...')

    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(refresh, pywikibot.Site(lang, family))
                   for family in config.usernames
                   for lang in config.usernames[family]}
        wl_count_all = sum(len(future.result())
                           for future in as_completed(futures))
    if not quiet:
        pywikibot.info('There are a total of {} page(s) in the watchlists for '
                       'all wikis.'.format(wl_count_all))


def isWatched(pageName, site=None):  # noqa: N802, N803
    """Check whether a page is being watched."""
    watchlist = get(site)
    return pageName in watchlist


def refresh(site):
    """Fetch the watchlist."""
    pywikibot.info(f'Retrieving watchlist for {str(site)}.')
    return list(site.watched_pages(force=True))


def refresh_all() -> None:
    """Reload watchlists for all wikis where a watchlist is already present."""
    cache_path = CachedRequest._get_cache_dir()
    files = os.scandir(cache_path)
    seen = set()
    with ThreadPoolExecutor() as executor:
        for filename in files:
            entry = CacheEntry(cache_path, filename)
            entry._load_cache()
            entry.parse_key()
            entry._rebuild()
            if entry.site in seen:
                continue

            # for generator API usage we have to check the modules
            modules = entry._params.get('modules', [])
            modules_found = any(module.endswith('watchlistraw')
                                for module in modules)
            # for list API usage 'watchlistraw' is directly found
            if modules_found or 'watchlistraw' in entry._data:
                executor.submit(refresh, entry.site)
                seen.add(entry.site)


def refresh_new() -> None:
    """Load watchlists of all wikis for accounts set in user config."""
    pywikibot.info(f'Downloading all watchlists for your accounts in '
                   f'{config.user_config_file}')
    count_watchlist_all(quiet=True)


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
            except InvalidTitleError as e:
                pywikibot.error(e)


if __name__ == '__main__':
    start = datetime.datetime.now()
    main()
    pywikibot.info('\nExecution time: {} seconds'
                   .format((datetime.datetime.now() - start).seconds))
