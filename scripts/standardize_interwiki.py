#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Loop over all pages in the home wiki, standardizing the interwiki links.

Parameters:

-start:     - Set from what page you want to start
"""
#
# (C) Rob W.W. Hooft, 2003
# (C) Pywikibot team, 2003-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot

from pywikibot import textlib

# The summary that the Bot will use.
comment = {
    'ar': u'روبوت: توحيد قياسي للإنترويكي',
    'cs': 'Robot: standardizace interwiki',
    'de': u'Bot: Interwikilinks standardisieren',
    'en': u'Robot: Interwiki standardization',
    'fa': u'ربات: تصحیح جایگذاری میان‌ویکی‌ها',
    'fr': u'Robot : Standardisation des interwikis',
    'he': u'בוט: מסדר את האינטרוויקי',
    'hi': 'बॉट: अंतरविकि मानकीकरण',
    'it': u'Bot: Standardizzo interwiki',
    'ja': u'ロボットによる: 言語間リンクを標準化',
    'ksh': 'Bot: Engerwiki Lengks opprüühme',
    'ml': u'യന്ത്രം: അന്തർവിക്കി ക്രമവൽക്കരണം',
    'nds': 'Bot: Links twüschen Wikis standardisseern',
    'nl': u'Bot: standaardisatie interwikiverwijzingen',
    'no': u'bot: Språklenkestandardisering',
    'ro': 'Robot: Standardizare interwiki',
    'zh': u'機器人: 跨語連結標準化',
}


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
    comm = pywikibot.translate(site, comment)
    for pl in site.allpages(start):
        plname = pl.title()
        pywikibot.output(u'\nLoading %s...' % plname)
        try:
            oldtext = pl.get()
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"%s is a redirect!" % plname)
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
                    pywikibot.output(u"%s is locked" % plname)
                    continue
            else:
                pywikibot.output(u'No changes needed.')
                continue
        else:
            pywikibot.output(u'No interwiki found.')
            continue


if __name__ == '__main__':
    main()
