#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Allows access to the bot account's watchlist.

The watchlist can be updated manually by running this script.

Syntax:

    python pwb.py watchlist [-all | -new]

Command line options:
    -all  -  Reloads watchlists for all wikis where a watchlist is already
             present
    -new  -  Load watchlists for all wikis where accounts is setting in
             user-config.py
"""
#
# (C) Daniel Herding, 2005
# (C) Pywikibot team, 2005-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import os

import pywikibot

from pywikibot import config

from pywikibot.data.api import CachedRequest

from scripts.maintenance.cache import CacheEntry


def get(site=None):
    """Load the watchlist, fetching it if necessary."""
    if site is None:
        site = pywikibot.Site()
    watchlist = [p.title() for p in site.watched_pages()]
    return watchlist


def isWatched(pageName, site=None):
    """Check whether a page is being watched."""
    watchlist = get(site)
    return pageName in watchlist


def refresh(site, sysop=False):
    """Fetch the watchlist."""
    pywikibot.output('Retrieving watchlist for {0}.'.format(str(site)))
    return list(site.watched_pages(sysop=sysop, force=True))


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
            if entry._data.get('watchlistraw'):
                refresh(entry.site, sysop)
                seen.append(entry.site)


def refresh_new(sysop=False):
    """Load watchlists of all wikis for accounts set in user-config.py."""
    pywikibot.output(
        'Downloading all watchlists for your accounts in user-config.py')
    for family in config.usernames:
        for lang in config.usernames[family]:
            site = pywikibot.Site(lang, family)
            refresh(site, sysop=sysop)
    for family in config.sysopnames:
        for lang in config.sysopnames[family]:
            site = pywikibot.Site(lang, family)
            refresh(site, sysop=sysop)


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
        watchlist = refresh(site, sysop=sysop)
        pywikibot.output(u'%i pages in the watchlist.' % len(watchlist))
        for page in watchlist:
            try:
                pywikibot.stdout(page.title())
            except pywikibot.InvalidTitle:
                pywikibot.exception()


if __name__ == "__main__":
    main()
