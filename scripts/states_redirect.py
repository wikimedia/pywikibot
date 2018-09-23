#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Create country sub-division redirect pages.

Check if they are in the form Something, State, and if so, create a redirect
from Something, ST.

Specific arguments:
-start:xxx Specify the place in the alphabet to start searching
-force: Don't ask whether to create pages, just create them.

PRE-REQUISITE : Need to install python-pycountry library.
* Follow the instructions at: https://www.versioneye.com/python/pycountry/0.16
* Install with pip: pip install pycountry
"""
#
# (C) Andre Engels, 2004
# (C) Pywikibot team, 2004-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import re
import sys

import pywikibot

from pywikibot import i18n

try:
    import pycountry
except ImportError:
    pywikibot.error('This script requires the python-pycountry module')
    pywikibot.error('See: https://pypi.org/project/pycountry')
    pywikibot.exception()
    sys.exit(1)


class StatesRedirectBot(pywikibot.Bot):

    """Bot class used for implementation of re-direction norms."""

    def __init__(self, start, force):
        """Initializer.

        Parameters:
            @param start:xxx Specify the place in the alphabet to start
            searching.
            @param force: Don't ask whether to create pages, just create
            them.
        """
        site = pywikibot.Site()
        generator = site.allpages(start=start)
        super(StatesRedirectBot, self).__init__(generator=generator)

        self.force = force

        # Created abbrev from pycountry data base
        self.abbrev = {}
        for subd in pycountry.subdivisions:
            # Used subd.code[3:] to extract the exact code for
            # subdivisional states(ignoring the country code).
            self.abbrev[subd.name] = subd.code[3:]

    def treat(self, page):
        """Re-directing process.

        Check if pages are in the given form Something, State, and
        if so, create a redirect from Something, ST..
        """
        for sn in self.abbrev:
            if re.search(r', %s$' % sn, page.title()):
                pl = pywikibot.Page(self.site, page.title().replace(sn,
                                    self.abbrev[sn]))
                # A bit hacking here - the real work is done in the
                # 'except pywikibot.NoPage' part rather than the 'try'.

                try:
                    pl.get(get_redirect=True)
                    goal = pl.getRedirectTarget().title()
                    if pywikibot.Page(self.site, goal).exists():
                        pywikibot.output(
                            'Not creating {0} - redirect already exists.'
                            .format(goal))
                    else:
                        pywikibot.warning(
                            '{0} already exists but redirects elsewhere!'
                            .format(goal))
                except pywikibot.IsNotRedirectPage:
                    pywikibot.warning(
                        'Page {0} already exists and is not a redirect '
                        'Please check page!'
                        .format(pl.title()))
                except pywikibot.NoPage:
                    if page.isRedirectPage():
                        p2 = page.getRedirectTarget()
                        pywikibot.output(
                            'Note: goal page is redirect.\nCreating redirect '
                            'to "{0}" to avoid double redirect.'
                            .format(p2.title()))
                    else:
                        p2 = page
                    if self.force or pywikibot.input_yn('Create redirect {0}?'
                                                        .format(pl.title())):
                        pl.set_redirect_target(
                            p2, create=True,
                            summary=i18n.twtranslate(
                                self.site, 'states_redirect-comment'))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: unicode
    """
    local_args = pywikibot.handle_args(args)
    start = None
    force = False

    # Parse command line arguments
    for arg in local_args:
        if arg.startswith('-start:'):
            start = arg[7:]
        elif arg == '-force':
            force = True
        else:
            pywikibot.warning(
                'argument "{0}" not understood; ignoring.'.format(arg))

    bot = StatesRedirectBot(start, force)
    bot.run()


if __name__ == '__main__':
    main()
