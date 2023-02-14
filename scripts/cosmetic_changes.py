#!/usr/bin/env python3
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
                  only that method. It can be set to:
                  all - dos not ignore errors
                  match - ignores ISBN related errors (default)
                  method - ignores fixing method errors
                  page - ignores page related errors


The following generators and filters are supported:

&params;

&warning;

For further information see pywikibot/cosmetic_changes.py
"""
#
# (C) Pywikibot team, 2006-2022
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import config, pagegenerators
from pywikibot.bot import AutomaticTWSummaryBot, ExistingPageBot
from pywikibot.cosmetic_changes import CANCEL, CosmeticChangesToolkit
from pywikibot.exceptions import InvalidPageError


warning = """
ATTENTION: You can run this script as a stand-alone for testing purposes.
However, the changes that are made are only minor, and other users
might get angry if you fill the version histories and watchlists with such
irrelevant changes. Some wikis prohibit stand-alone running."""

docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
    '&warning;': warning,
}


class CosmeticChangesBot(AutomaticTWSummaryBot, ExistingPageBot):

    """Cosmetic changes bot."""

    use_redirects = False
    summary_key = 'cosmetic_changes-standalone'
    update_options = {
        'async': False,
        'summary': '',
        'ignore': CANCEL.MATCH,
    }

    def treat_page(self) -> None:
        """Treat page with the cosmetic toolkit.

        .. versionchanged:: 7.0
           skip if InvalidPageError is raised
        """
        cc_toolkit = CosmeticChangesToolkit(self.current_page,
                                            ignore=self.opt.ignore)
        try:
            old_text = self.current_page.text
        except InvalidPageError as e:
            pywikibot.error(e)
            return

        new_text = cc_toolkit.change(old_text)
        if new_text is not False:
            self.put_current(new_text=new_text,
                             summary=self.opt.summary,
                             asynchronous=self.opt['async'])


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}

    # Process global args and prepare generator args parser
    gen_factory = pagegenerators.GeneratorFactory()
    local_args = pywikibot.handle_args(args)
    local_args = gen_factory.handle_args(local_args)

    for arg in local_args:
        opt, _, value = arg.partition(':')
        if opt == '-summary':
            options['summary'] = value
        elif opt in ('-always', '-async'):
            options[opt[1:]] = True
        elif opt == '-ignore':
            value = value.upper()
            try:
                options['ignore'] = getattr(CANCEL, value)
            except AttributeError:
                raise ValueError(f'Unknown ignore mode {value!r}!')

    gen = gen_factory.getCombinedGenerator(preload=True)
    if not pywikibot.bot.suggest_help(missing_generator=not gen) \
       and (options.get('always')
            or config.simulate
            or pywikibot.input_yn(
                warning + '\nDo you really want to continue?',
                default=False, automatic_quit=False)):
        bot = CosmeticChangesBot(generator=gen, **options)
        bot.run()


if __name__ == '__main__':
    main()
