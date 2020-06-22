#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Bot to create capitalized redirects.

It creates redirects where the first character of the first
word is uppercase and the remaining characters and words are lowercase.

Command-line arguments:

-always           Don't prompt to make changes, just do them.

-titlecase        creates a titlecased redirect version of a given page
                  where all words of the title start with an uppercase
                  character and the remaining characters are lowercase.

&params;

Example:

    python pwb.py capitalize_redirects -start:B -always
"""
#
# (C) Pywikibot team, 2006-2019
#
# Distributed under the terms of the MIT license.
#
# Originally derived from:
#    http://en.wikipedia.org/wiki/User:Drinibot/CapitalizationRedirects
#
# Automatically converted from compat branch by compat2core.py script
#
from __future__ import absolute_import, division, unicode_literals

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import (
    MultipleSitesBot, FollowRedirectPageBot, ExistingPageBot
)

docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class CapitalizeBot(MultipleSitesBot, FollowRedirectPageBot, ExistingPageBot):

    """Capitalization Bot."""

    def __init__(self, generator, **kwargs):
        """Initializer.

        Parameters:
            @param generator: The page generator that determines on which pages
                              to work.
            @kwarg titlecase: create a titlecased redirect page instead a
                              capitalized one.
        """
        self.availableOptions.update({
            'titlecase': False,
        })

        super(CapitalizeBot, self).__init__(generator=generator, **kwargs)

    def treat_page(self):
        """Capitalize redirects of the current page."""
        page_t = self.current_page.title()
        site = self.current_page.site
        if self.getOption('titlecase'):
            page_cap = pywikibot.Page(site, page_t.title())
        else:
            page_cap = pywikibot.Page(site, page_t.capitalize())
        if page_cap.exists():
            pywikibot.output('{} already exists, skipping...\n'
                             .format(page_cap.title(as_link=True)))
        else:
            pywikibot.output("{} doesn't exist"
                             .format(page_cap.title(as_link=True)))
            if self.user_confirm('Do you want to create a redirect?'):
                comment = i18n.twtranslate(
                    site,
                    'capitalize_redirects-create-redirect',
                    {'to': page_t})
                page_cap.set_redirect_target(self.current_page, create=True,
                                             summary=comment)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    options = {}

    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-always':
            options['always'] = True
        elif arg == '-titlecase':
            options['titlecase'] = True
        else:
            gen_factory.handleArg(arg)

    gen = gen_factory.getCombinedGenerator(preload=True)
    if gen:
        bot = CapitalizeBot(gen, **options)
        bot.run()
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
