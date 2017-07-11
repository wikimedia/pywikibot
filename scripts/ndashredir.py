#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
A script to create hyphenated redirects for n or m dash pages.

This script collects pages with n or m dash in their title and creates
a redirect from the corresponding hyphenated version. If the redirect
already exists, it is skipped.

Use -reversed option to create n dash redirects for hyphenated pages.
Some communities can decide to use hyphenated titles for templates, modules
or categories and in this case this option can be handy.


The following parameters are supported:

-always           don't ask for confirmation when putting a page

-reversed         create n dash redirects for hyphenated pages

-summary:         set custom summary message for the edit


The following generators and filters are supported:

&params;
"""
#
# (C) Bináris, 2012
# (C) Pywikibot team, 2012-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import pywikibot
from pywikibot import i18n, pagegenerators

from pywikibot.bot import (MultipleSitesBot, ExistingPageBot,
                           NoRedirectPageBot)

from pywikibot.tools.formatter import color_format

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class DashRedirectBot(
    MultipleSitesBot,  # A bot working on multiple sites
    ExistingPageBot,  # CurrentPageBot which only treats existing pages
    NoRedirectPageBot  # CurrentPageBot which only treats non-redirects
):

    """Bot to create hyphenated or dash redirects."""

    def __init__(self, generator, **kwargs):
        """
        Constructor.

        @param generator: the page generator that determines which pages
            to work on
        @type generator: generator
        """
        # -always option is predefined by BaseBot class
        self.availableOptions.update({
            'summary': None,  # custom bot summary
            'reversed': False,  # switch bot behavior
        })

        # call constructor of the super class
        super(DashRedirectBot, self).__init__(site=True, **kwargs)

        # assign the generator to the bot
        self.generator = generator

    def treat_page(self):
        """Do the magic."""
        # set origin
        origin = self.current_page.title()
        site = self.current_page.site

        # create redirect title
        if not self.getOption('reversed'):
            redir = pywikibot.Page(site, origin.replace('–', '-')
                                               .replace('—', '-'))
        else:
            redir = pywikibot.Page(site, origin.replace('-', '–'))

        # skip unchanged
        if redir.title() == origin:
            pywikibot.output('No need to process %s, skipping…'
                             % redir.title())
            # suggest -reversed parameter
            if '-' in origin and not self.getOption('reversed'):
                pywikibot.output('Consider using -reversed parameter '
                                 'for this particular page')
        else:
            # skip existing
            if redir.exists():
                pywikibot.output('%s already exists, skipping…'
                                 % redir.title())
            else:
                # confirm and save redirect
                if self.user_confirm(
                    color_format(
                        'Redirect from {lightblue}{0}{default} doesn\'t exist '
                        'yet.\nDo you want to create it?',
                        redir.title())):
                    # If summary option is None, it takes the default
                    # i18n summary from i18n subdirectory with summary key.
                    if self.getOption('summary'):
                        summary = self.getOption('summary')
                    else:
                        summary = i18n.twtranslate(site,
                                                   'ndashredir-create',
                                                   {'title': origin})
                    redir.set_redirect_target(self.current_page, create=True,
                                              summary=summary)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    options = {}
    # Process global arguments to determine desired site
    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    genFactory = pagegenerators.GeneratorFactory()

    # Parse command line arguments
    for arg in local_args:

        # Catch the pagegenerators options
        if genFactory.handleArg(arg):
            continue  # nothing to do here

        # Now pick up custom options
        arg, sep, value = arg.partition(':')
        option = arg[1:]
        if option == 'summary':
            options[option] = value
        # Take the remaining options as booleans.
        # Output a hint if they aren't pre-defined in the bot class
        else:
            options[option] = True

    # The preloading option is responsible for downloading multiple pages
    # from the wiki simultaneously.
    gen = genFactory.getCombinedGenerator(preload=True)
    if gen:
        # pass generator and private options to the bot
        bot = DashRedirectBot(gen, **options)
        bot.run()  # guess what it does
        return True
    else:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False


if __name__ == '__main__':
    main()
