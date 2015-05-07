#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Allows access to the bot account's watchlist.

The function refresh() downloads the current watchlist and saves it to disk.
It is run automatically when a bot first tries to save a page retrieved. The
watchlist can be updated manually by running this script. The list will also
be reloaded automatically once a month.

Syntax: python watchlist [-all | -new]

Command line options:
    -all  -  Reloads watchlists for all wikis where a watchlist is already
             present
    -new  -  Load watchlists for all wikis where accounts is setting in
             user-config.py
"""
#
# (C) Daniel Herding, 2005
# (C) Pywikibot team, 2005-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import os
import pywikibot
from pywikibot import config
from pywikibot.data.api import CachedRequest
from scripts.maintenance.cache import CacheEntry

cache = {}


def get(site=None):
    """Load the watchlist, fetching it if necessary."""
    if site is None:
        site = pywikibot.Site()
    if site in cache:
        # Use cached copy if it exists.
        watchlist = cache[site]
    else:
        # create cached copy
        watchlist = refresh(site)
        cache[site] = watchlist
    return watchlist


def isWatched(pageName, site=None):
    """Check whether a page is being watched."""
    watchlist = get(site)
    return pageName in watchlist


def refresh(site, sysop=False):
    """Fetch the watchlist."""
    if not site.logged_in(sysop=sysop):
        site.login(sysop=sysop)

    params = {
        'action': 'query',
        'list': 'watchlistraw',
        'wrlimit': config.special_page_limit,
    }

    pywikibot.output(u'Retrieving watchlist for %s via API.' % str(site))
    # pywikibot.put_throttle() # It actually is a get, but a heavy one.
    watchlist = []
    while True:
        req = CachedRequest(config.API_config_expiry, site=site, **params)
        data = req.submit()
        if 'error' in data:
            raise RuntimeError('ERROR: %s' % data)
        watchlist.extend([w['title'] for w in data['watchlistraw']])

        if 'query-continue' in data:
            params.update(data['query-continue']['watchlistraw'])
        else:
            break
    return watchlist


def refresh_all(sysop=False):
    """Reload watchlists for all wikis where a watchlist is already present."""
    cache_path = CachedRequest._get_cache_dir()
    files = os.listdir(cache_path)
    seen = []
    for filename in files:
        entry = CacheEntry(cache_path, filename)
        entry._load_cache()
        entry.parse_key()
        entry._rebuild()
        if entry.site not in seen:
            if entry._data['watchlistraw']:
                refresh(entry.site, sysop)
                seen.append(entry.site)


def refresh_new(sysop=False):
    """Load watchlists of all wikis for accounts set in user-config.py."""
    pywikibot.output(
        'Downloading all watchlists for your accounts in user-config.py')
    for family in config.usernames:
        for lang in config.usernames[family]:
            refresh(pywikibot.Site(lang, family), sysop=sysop)
    for family in config.sysopnames:
        for lang in config.sysopnames[family]:
            refresh(pywikibot.Site(lang, family), sysop=sysop)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    all = False
    new = False
    sysop = False
    for arg in pywikibot.handle_args(args):
        if arg in ('-all', '-update'):
            all = True
        elif arg == '-new':
            new = True
        elif arg == '-sysop':
            sysop = True
    if all:
        refresh_all(sysop=sysop)
    elif new:
        refresh_new(sysop=sysop)
    else:
        site = pywikibot.Site()
        refresh(site, sysop=sysop)

        watchlist = get(site)
        pywikibot.output(u'%i pages in the watchlist.' % len(watchlist))
        for pageName in watchlist:
            pywikibot.output(pageName, toStdout=True)

if __name__ == "__main__":
    main()
