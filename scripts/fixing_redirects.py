#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Correct all redirect links in featured pages or only one page of each wiki.

Can be using with:
&params;

-featured         Run over featured pages (for some wikimedia wikis only)

Run fixing_redirects.py -help to see all the command-line
options -file, -ref, -links, ...

"""
#
# (C) Pywikibot team, 2004-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#
import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (SingleSiteBot, ExistingPageBot, NoRedirectPageBot,
                           AutomaticTWSummaryBot, suggest_help)

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;':     pagegenerators.parameterHelp,
}

# Featured articles categories
featured_articles = 'Q4387444'


class FixingRedirectBot(SingleSiteBot, ExistingPageBot, NoRedirectPageBot,
                        AutomaticTWSummaryBot):

    """Run over pages and resolve redirect links."""

    ignore_save_related_errors = True
    ignore_server_errors = True
    summary_key = 'fixing_redirects-fixing'

    def treat_page(self):
        """Change all redirects from the current page to actual links."""
        links = self.current_page.linkedPages()
        newtext = self.current_page.text
        i = None
        for i, page in enumerate(links):
            if not page.exists():
                try:
                    target = page.moved_target()
                except (pywikibot.NoMoveTarget,
                        pywikibot.CircularRedirect,
                        pywikibot.InvalidTitle):
                    continue
            elif page.isRedirectPage():
                try:
                    target = page.getRedirectTarget()
                except (pywikibot.CircularRedirect,
                        pywikibot.InvalidTitle):
                    continue
            else:
                continue
            # no fix to user namespaces
            if target.namespace() in [2, 3] and page.namespace() not in [2, 3]:
                continue
            newtext = pywikibot.textlib.replace_links(newtext, [page, target])

        if i is None:
            pywikibot.output('Nothing left to do.')
        else:
            self.put_current(newtext)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    featured = False
    gen = None

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-featured':
            featured = True
        elif genFactory.handleArg(arg):
            pass

    mysite = pywikibot.Site()
    if mysite.sitename == 'wikipedia:nl':
        pywikibot.output(
            '\03{lightred}There is consensus on the Dutch Wikipedia that '
            'bots should not be used to fix redirects.\03{default}')
        return

    if featured:
        repo = mysite.data_repository()
        if repo:
            dp = pywikibot.ItemPage(repo, featured_articles)
            try:
                ref = pywikibot.Category(mysite, dp.getSitelink(mysite))
            except pywikibot.NoPage:
                pass
            else:
                gen = ref.articles(namespaces=0, content=True)
        if not gen:
            suggest_help(
                unknown_parameters=['-featured'],
                additional_text='Option is not available for this site.')
            return False
    else:
        gen = genFactory.getCombinedGenerator()
        if gen:
            gen = mysite.preloadpages(gen)
    if gen:
        bot = FixingRedirectBot(generator=gen)
        bot.run()
        return True
    else:
        suggest_help(missing_generator=True)
        return False

if __name__ == "__main__":
    main()
