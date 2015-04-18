#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Bot to create capitalized redirects.

It creates redirects where the first character of the first
word is uppercase and the remaining characters and words are lowercase.

Command-line arguments:

&params;

-always           Don't prompt to make changes, just do them.

-titlecase        creates a titlecased redirect version of a given page
                  where all words of the title start with an uppercase
                  character and the remaining characters are lowercase.

Example: "python capitalize_redirects.py -start:B -always"
"""
#
# (C) Yrithinnd, 2006
# (C) Pywikibot team, 2007-2015
#
# Distributed under the terms of the MIT license.
#
# Originally derived from:
#    http://en.wikipedia.org/wiki/User:Drinibot/CapitalizationRedirects
#
# Automatically converted from compat branch by compat2core.py script
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import FollowRedirectPageBot, ExistingPageBot

docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class CapitalizeBot(FollowRedirectPageBot, ExistingPageBot):

    """Capitalization Bot."""

    def __init__(self, generator, **kwargs):
        """Constructor.

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
            pywikibot.output(u'%s already exists, skipping...\n'
                             % page_cap.title(asLink=True))
        else:
            pywikibot.output(u'%s doesn\'t exist'
                             % page_cap.title(asLink=True))
            if not self.getOption('always'):
                choice = pywikibot.input_choice(
                    u'Do you want to create a redirect?',
                    [('Yes', 'y'), ('No', 'n'), ('All', 'a')], 'n')
                if choice == 'a':
                    self.options['always'] = True
            if self.getOption('always') or choice == 'y':
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
    @type args: list of unicode
    """
    options = {}

    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-always':
            options['always'] = True
        elif arg == '-titlecase':
            options['titlecase'] = True
        else:
            genFactory.handleArg(arg)

    gen = genFactory.getCombinedGenerator()
    if gen:
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        bot = CapitalizeBot(preloadingGen, **options)
        bot.run()
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    main()
