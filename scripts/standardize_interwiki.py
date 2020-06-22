#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Loop over all pages in the home wiki, standardizing the interwiki links.

Parameters:

-start:     - Set from what page you want to start
"""
#
# (C) Pywikibot team, 2003-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import pywikibot

from pywikibot import i18n, textlib


def main(*args):
    """Process command line arguments and run the script."""
    start = '!'

    # Load the default parameters and start
    for arg in pywikibot.handle_args():
        if arg.startswith('-start'):
            if len(arg) == 6:
                start = pywikibot.input('From what page do you want to start?')
            else:
                start = arg[7:]
    site = pywikibot.Site()
    comm = i18n.twtranslate(site, 'standardize_interwiki-comment')
    for pl in site.allpages(start):
        plname = pl.title()
        pywikibot.output('\nLoading {0}...'.format(plname))
        try:
            oldtext = pl.get()
        except pywikibot.IsRedirectPage:
            pywikibot.output('{0} is a redirect!'.format(plname))
            continue
        old = pl.interwiki()
        new = {}
        for pl2 in old:
            new[pl2.site] = pywikibot.Page(pl2)
        newtext = textlib.replaceLanguageLinks(oldtext, new, site=site)
        if new:
            if oldtext != newtext:
                pywikibot.showDiff(oldtext, newtext)
                # Submit changes
                try:
                    pl.put(newtext, comment=comm)
                except pywikibot.LockedPage:
                    pywikibot.output('{0} is locked'.format(plname))
                    continue
            else:
                pywikibot.output('No changes needed.')
                continue
        else:
            pywikibot.output('No interwiki found.')
            continue


if __name__ == '__main__':
    main()
