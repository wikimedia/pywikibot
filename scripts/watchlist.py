# -*- coding: utf-8 -*-
"""
Allows access to the bot account's watchlist.

The function refresh() downloads the current watchlist and saves it to disk.
It is run automatically when a bot first tries to save a page retrieved. The
watchlist can be updated manually by running this script. The list will also
be reloaded automatically once a month.

Syntax: python watchlist [-all]

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
__version__ = '$Id$'
#

import re
import pickle
import os.path
import time

import pywikibot
from pywikibot import config

cache = {}


def get(site=None):
    """Load the watchlist, fetching it if necessary."""
    if site is None:
        site = pywikibot.Site()
    if site in cache:
        # Use cached copy if it exists.
        watchlist = cache[site]
    else:
        fn = config.datafilepath('watchlists',
                                 'watchlist-%s-%s.dat'
                                 % (site.family.name, site.code))
        try:
            # find out how old our saved dump is (in seconds)
            file_age = time.time() - os.path.getmtime(fn)
            # if it's older than 1 month, reload it
            if file_age > 30 * 24 * 60 * 60:
                pywikibot.output(
                    u'Copy of watchlist is one month old, reloading')
                refresh(site)
        except OSError:
            # no saved watchlist exists yet, retrieve one
            refresh(site)
        with open(fn, 'rb') as f:
            watchlist = pickle.load(f)
        # create cached copy
        cache[site] = watchlist
    return watchlist


def isWatched(pageName, site=None):
    """Check whether a page is being watched."""
    watchlist = get(site)
    return pageName in watchlist


def refresh(site, sysop=False):
    """Fetch the watchlist."""
    if not site.logged_in(sysop=sysop):
        site.forceLogin(sysop=sysop)

    params = {
        'action': 'query',
        'list': 'watchlistraw',
        'site': site,
        'wrlimit': config.special_page_limit,
    }

    pywikibot.output(u'Retrieving watchlist for %s via API.' % str(site))
    # pywikibot.put_throttle() # It actually is a get, but a heavy one.
    watchlist = []
    while True:
        req = pywikibot.data.api.Request(**params)
        data = req.submit()
        if 'error' in data:
            raise RuntimeError('ERROR: %s' % data)
        watchlist.extend([w['title'] for w in data['watchlistraw']])

        if 'query-continue' in data:
            params.update(data['query-continue']['watchlistraw'])
        else:
            break

    # Save the watchlist to disk
    # The file is stored in the watchlists subdir. Create if necessary.
    with open(config.datafilepath('watchlists',
                                  'watchlist-%s-%s%s.dat'
                                  % (site.family.name, site.code,
                                     '-sysop' if sysop else '')),
              'wb') as f:
        pickle.dump(watchlist, f, protocol=config.pickle_protocol)


def refresh_all(new=False, sysop=False):
    """Fetch and locally cache several watchlists."""
    if new:
        pywikibot.output(
            'Downloading all watchlists for your accounts in user-config.py')
        for family in config.usernames:
            for lang in config.usernames[family]:
                refresh(pywikibot.Site(lang, family), sysop=sysop)
        for family in config.sysopnames:
            for lang in config.sysopnames[family]:
                refresh(pywikibot.Site(lang, family), sysop=sysop)

    else:
        import dircache
        filenames = dircache.listdir(
            config.datafilepath('watchlists'))
        watchlist_filenameR = re.compile('watchlist-([a-z\-:]+).dat')
        for filename in filenames:
            match = watchlist_filenameR.match(filename)
            if match:
                arr = match.group(1).split('-')
                family = arr[0]
                lang = '-'.join(arr[1:])
                refresh(pywikibot.Site(lang, family))


def main():
    """ Script entry point. """
    local_args = pywikibot.handleArgs()
    all = False
    new = False
    sysop = False
    for arg in local_args:
        if arg in ('-all', '-update'):
            all = True
        elif arg == '-new':
            new = True
        elif arg == '-sysop':
            sysop = True
    if all:
        refresh_all(sysop=sysop)
    elif new:
        refresh_all(new, sysop=sysop)
    else:
        site = pywikibot.Site()
        refresh(site, sysop=sysop)

        watchlist = get(site)
        pywikibot.output(u'%i pages in the watchlist.' % len(watchlist))
        for pageName in watchlist:
            pywikibot.output(pageName, toStdout=True)

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
