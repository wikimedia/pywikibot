#!/usr/bin/python
"""Script that preloads site and user info for all sites of given family.

The following parameters are supported:

-worker:<num>     The number of parallel tasks to be run. Default is the
                  number of precessors on the machine

Usage:

    python pwb.py preload_sites [{<family>}] [-worker{<num>}]

To force preloading, change the global expiry value to 0:

    python pwb.py -API_config_expiry:0 preload_sites [{<family>}]

"""
#
# (C) Pywikibot team, 2021
#
# Distributed under the terms of the MIT license.
#
from concurrent.futures import ThreadPoolExecutor, wait
from datetime import datetime

import pywikibot
from pywikibot.family import Family


# supported families by this script
families_list = [
    'wikibooks',
    'wikinews',
    'wikipedia',
    'wikiquote',
    'wikisource',
    'wikiversity',
    'wikivoyage',
    'wiktionary',
]

exceptions = {
}


def preload_family(family, executor):
    """Preload all sites of a single family file."""
    msg = 'Preloading sites of {} family{}'
    pywikibot.output(msg.format(family, '...'))

    codes = Family.load(family).languages_by_size
    for code in exceptions.get(family, []):
        if code in codes:
            codes.remove(code)
    obsolete = Family.load(family).obsolete

    futures = set()
    for code in codes:
        if code not in obsolete:
            site = pywikibot.Site(code, family)
            # page title does not care
            futures.add(executor.submit(pywikibot.Page, site, 'Main page'))
    wait(futures)
    pywikibot.output(msg.format(family, ' completed.'))


def preload_families(families, worker):
    """Preload all sites of all given family files."""
    start = datetime.now()
    with ThreadPoolExecutor(worker) as executor:
        futures = {executor.submit(preload_family, family, executor)
                   for family in families}
        wait(futures)
    pywikibot.output('Loading time used: {}'.format(datetime.now() - start))


if __name__ == '__main__':
    fam = set()
    worker = None
    for arg in pywikibot.handle_args():
        if arg in families_list:
            fam.add(arg)
        elif arg.startswith('-worker'):
            worker = int(arg.partition(':')[2])
    preload_families(fam or families_list, worker)
