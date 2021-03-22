#!/usr/bin/python
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
# (C) Pywikibot team, 2006-2021
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import config, i18n, pagegenerators
from pywikibot.backports import Tuple
from pywikibot.bot import ExistingPageBot, NoRedirectPageBot
from pywikibot.cosmetic_changes import CANCEL, CosmeticChangesToolkit


warning = """
ATTENTION: You can run this script as a stand-alone for testing purposes.
However, the changes that are made are only minor, and other users
might get angry if you fill the version histories and watchlists with such
irrelevant changes. Some wikis prohibit stand-alone running."""

docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
    '&warning;': warning,
}


class CosmeticChangesBot(ExistingPageBot, NoRedirectPageBot):

    """Cosmetic changes bot."""

    def __init__(self, generator, **kwargs) -> None:
        """Initializer."""
        self.available_options.update({
            'async': False,
            'summary': 'Robot: Cosmetic changes',
            'ignore': CANCEL.ALL,
        })
        super().__init__(**kwargs)

        self.generator = generator

    def treat_page(self) -> None:
        """Treat page with the cosmetic toolkit."""
        cc_toolkit = CosmeticChangesToolkit(self.current_page,
                                            ignore=self.opt.ignore)
        changed_text = cc_toolkit.change(self.current_page.get())
        if changed_text is not False:
            self.put_current(new_text=changed_text,
                             summary=self.opt.summary,
                             asynchronous=self.opt['async'])


def main(*args: Tuple[str, ...]) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
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
                options['ignore'] = CANCEL.METHOD
            elif ignore_mode == 'page':
                options['ignore'] = CANCEL.PAGE
            elif ignore_mode == 'match':
                options['ignore'] = CANCEL.MATCH
            else:
                raise ValueError(
                    'Unknown ignore mode "{}"!'.format(ignore_mode))
        else:
            gen_factory.handle_arg(arg)

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
