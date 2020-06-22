#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This module can do slight modifications to tidy a wiki page's source code.

The changes are not supposed to change the look of the rendered wiki page.

The following parameters are supported:

-always           Don't prompt you for each replacement. Warning (see below)
                  has not to be confirmed. ATTENTION: Use this with care!

-async            Put page on queue to be saved to wiki asynchronously.

-summary:XYZ      Set the summary message text for the edit to XYZ, bypassing
                  the predefined message texts with original and replacements
                  inserted.

-ignore:          Ignores if an error occurred and either skips the page or
                  only that method. It can be set to 'page' or 'method'.

The following generators and filters are supported:

&params;

&warning;

For further information see pywikibot/cosmetic_changes.py
"""
#
# (C) Pywikibot team, 2006-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import pywikibot

from pywikibot import config, cosmetic_changes, i18n, pagegenerators
from pywikibot.bot import MultipleSitesBot, ExistingPageBot, NoRedirectPageBot


warning = """
ATTENTION: You can run this script as a stand-alone for testing purposes.
However, the changes that are made are only minor, and other users
might get angry if you fill the version histories and watchlists with such
irrelevant changes. Some wikis prohibit stand-alone running."""

docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
    '&warning;': warning,
}


class CosmeticChangesBot(MultipleSitesBot, ExistingPageBot, NoRedirectPageBot):

    """Cosmetic changes bot."""

    def __init__(self, generator, **kwargs):
        """Initializer."""
        self.availableOptions.update({
            'async': False,
            'summary': 'Robot: Cosmetic changes',
            'ignore': cosmetic_changes.CANCEL_ALL,
        })
        super(CosmeticChangesBot, self).__init__(**kwargs)

        self.generator = generator

    def treat_page(self):
        """Treat page with the cosmetic toolkit."""
        cc_toolkit = cosmetic_changes.CosmeticChangesToolkit.from_page(
            self.current_page, ignore=self.getOption('ignore'))
        changed_text = cc_toolkit.change(self.current_page.get())
        if changed_text is not False:
            self.put_current(new_text=changed_text,
                             summary=self.getOption('summary'),
                             asynchronous=self.getOption('async'))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    options = {}

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg.startswith('-summary:'):
            options['summary'] = arg[len('-summary:'):]
        elif arg == '-always':
            options['always'] = True
        elif arg == '-async':
            options['async'] = True
        elif arg.startswith('-ignore:'):
            ignore_mode = arg[len('-ignore:'):].lower()
            if ignore_mode == 'method':
                options['ignore'] = cosmetic_changes.CANCEL_METHOD
            elif ignore_mode == 'page':
                options['ignore'] = cosmetic_changes.CANCEL_PAGE
            elif ignore_mode == 'match':
                options['ignore'] = cosmetic_changes.CANCEL_MATCH
            else:
                raise ValueError(
                    'Unknown ignore mode "{0}"!'.format(ignore_mode))
        else:
            gen_factory.handleArg(arg)

    site = pywikibot.Site()

    if not options.get('summary'):
        # Load default summary message.
        options['summary'] = i18n.twtranslate(site,
                                              'cosmetic_changes-standalone')

    gen = gen_factory.getCombinedGenerator(preload=True)
    if gen:
        if options.get('always') or config.simulate or pywikibot.input_yn(
                warning + '\nDo you really want to continue?',
                default=False, automatic_quit=False):
            site.login()
            bot = CosmeticChangesBot(gen, **options)
            bot.run()
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
