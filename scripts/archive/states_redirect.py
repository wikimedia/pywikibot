#!/usr/bin/python
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
# (C) Pywikibot team, 2004-2020
#
# Distributed under the terms of the MIT license.
#
import re

import pywikibot
from pywikibot import i18n
from pywikibot.bot import SingleSiteBot, suggest_help
from pywikibot.exceptions import IsNotRedirectPageError, NoPageError


try:
    import pycountry
except ImportError as e:
    pycountry = e


class StatesRedirectBot(SingleSiteBot):

    """Bot class used for implementation of re-direction norms."""

    def __init__(self, start: str, force: bool):
        """Initializer.

        :param start:xxx Specify the place in the alphabet to start searching.
        :param force: Don't ask whether to create pages, just create them.
        """
        super().__init__()
        self.start = start
        self.force = force

    def setup(self):
        """Create abbrev from pycountry data base."""
        self.abbrev = {}
        for subd in pycountry.subdivisions:
            # Used subd.code[3:] to extract the exact code for
            # subdivisional states(ignoring the country code).
            self.abbrev[subd.name] = subd.code[3:]

    @property
    def generator(self):
        """Generator used by run() method."""
        return self.site.allpages(start=self.start)

    def treat(self, page):
        """Re-directing process.

        Check if pages are in the given form Something, State, and
        if so, create a redirect from Something, ST..
        """
        for sn in self.abbrev:
            if re.fullmatch(r', {}'.format(sn), page.title()):
                pl = pywikibot.Page(self.site, page.title().replace(sn,
                                    self.abbrev[sn]))
                # A bit hacking here - the real work is done in the
                # 'except NoPageError' part rather than the 'try'.

                try:
                    pl.get(get_redirect=True)
                    goal = pl.getRedirectTarget().title()
                    if pywikibot.Page(self.site, goal).exists():
                        pywikibot.output(
                            'Not creating {} - redirect already exists.'
                            .format(goal))
                    else:
                        pywikibot.warning(
                            '{} already exists but redirects elsewhere!'
                            .format(goal))
                except IsNotRedirectPageError:
                    pywikibot.warning(
                        'Page {} already exists and is not a redirect '
                        'Please check page!'
                        .format(pl.title()))
                except NoPageError:
                    if page.isRedirectPage():
                        p2 = page.getRedirectTarget()
                        pywikibot.output(
                            'Note: goal page is redirect.\nCreating redirect '
                            'to "{}" to avoid double redirect.'
                            .format(p2.title()))
                    else:
                        p2 = page
                    if self.force or pywikibot.input_yn('Create redirect {}?'
                                                        .format(pl.title())):
                        pl.set_redirect_target(
                            p2, create=True,
                            summary=i18n.twtranslate(
                                self.site, 'states_redirect-comment'))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    local_args = pywikibot.handle_args(args)
    start = None
    force = False
    unknown_parameters = []

    # Parse command line arguments
    for arg in local_args:
        if arg.startswith('-start:'):
            start = arg[7:]
        elif arg == '-force':
            force = True
        else:
            unknown_parameters.append(arg)

    if isinstance(pycountry, ImportError):
        missing_dependencies = ('pycountry',)
    else:
        missing_dependencies = None

    if suggest_help(unknown_parameters=unknown_parameters,
                    missing_dependencies=missing_dependencies):
        return

    bot = StatesRedirectBot(start, force)
    bot.run()


if __name__ == '__main__':
    main()
