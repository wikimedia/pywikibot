#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
This bot goes over multiple pages of a wiki, and edits them without
changing. This is for example used to get category links in templates
working.

This script understands various command-line arguments:

&params;

-redir            specifies that the robot should touch redirect pages;
                  otherwise, they will be skipped.

All other parameters will be regarded as a page title; in this case, the bot
will only touch a single page.
"""

#
# (C) Pywikipedia team
#
__version__='$Id$'
#
# Distributed under the terms of the MIT license.
#

import pywikibot
from pywikibot import pagegenerators, config
import sys

docuReplacements = {'&params;': pagegenerators.parameterHelp}


class TouchBot:
    def __init__(self, generator, touch_redirects):
        self.generator = generator
        self.touch_redirects = touch_redirects

    def run(self):
        for page in self.generator:
            try:
                # get the page, and save it using the unmodified text.
                # whether or not getting a redirect throws an exception
                # depends on the variable self.touch_redirects.
                text = page.get(get_redirect = self.touch_redirects)
                page.save("Pywikibot touch script")
            except pywikibot.NoPage:
                pywikibot.error(u"Page %s does not exist."
                                % page.title(asLink=True))
            except pywikibot.IsRedirectPage:
                pywikibot.warning(u"Page %s is a redirect; skipping."
                                  % page.title(asLink=True))
            except pywikibot.LockedPage:
                pywikibot.error(u"Page %s is locked."
                                % page.title(asLink=True))
            except pywikibot.PageNotSaved:
                pywikibot.error(u"Page %s not saved."
                                % page.title(asLink=True))


def main(*args):
    global bot
    # Disable cosmetic changes because we don't want to modify any page
    # content, so that we don't flood the histories with minor changes.
    config.cosmetic_changes = False
    #page generator
    gen = None
    genFactory = pagegenerators.GeneratorFactory()
    redirs = False
    # If the user chooses to work on a single page, this temporary array is
    # used to read the words from the page title. The words will later be
    # joined with spaces to retrieve the full title.
    pageTitle = []
    for arg in pywikibot.handleArgs(*args):
        if genFactory.handleArg(arg):
            continue
        if arg == '-redir':
            redirs = True
        else:
            pageTitle.append(arg)

    gen = genFactory.getCombinedGenerator()
    if not gen:
        if pageTitle:
            # work on a single page
            page = pywikibot.Page(pywikibot.Link(' '.join(pageTitle)))
            gen = iter([page])
        else:
            pywikibot.showHelp()
            return
    preloadingGen = pagegenerators.PreloadingGenerator(gen)
    bot = TouchBot(preloadingGen, redirs)
    bot.run()


if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
