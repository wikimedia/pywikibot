#!/usr/bin/python
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
# (C) Pywikibot team, 2012-2021
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import ExistingPageBot, MultipleSitesBot, NoRedirectPageBot
from pywikibot.tools.formatter import color_format


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class DashRedirectBot(
    MultipleSitesBot,  # A bot working on multiple sites
    ExistingPageBot,  # CurrentPageBot which only treats existing pages
    NoRedirectPageBot  # CurrentPageBot which only treats non-redirects
):

    """Bot to create hyphenated or dash redirects."""

    def __init__(self, generator, **kwargs):
        """
        Initializer.

        :param generator: the page generator that determines which pages
            to work on
        :type generator: generator
        """
        # -always option is predefined by BaseBot class
        self.available_options.update({
            'summary': None,  # custom bot summary
            'reversed': False,  # switch bot behavior
        })

        # call initializer of the super class
        super().__init__(site=True, **kwargs)

        # assign the generator to the bot
        self.generator = generator

    def treat_page(self):
        """Do the magic."""
        # set origin
        origin = self.current_page.title()
        site = self.current_page.site

        # create redirect title
        if not self.opt.reversed:
            redir = pywikibot.Page(site, origin.replace('–', '-')
                                               .replace('—', '-'))
        else:
            redir = pywikibot.Page(site, origin.replace('-', '–'))

        # skip unchanged
        if redir.title() == origin:
            pywikibot.output('No need to process {}, skipping...'
                             .format(redir.title()))
            # suggest -reversed parameter
            if '-' in origin and not self.opt.reversed:
                pywikibot.output('Consider using -reversed parameter '
                                 'for this particular page')
        else:
            # skip existing
            if redir.exists():
                pywikibot.output('{} already exists, skipping...'
                                 .format(redir.title()))
            else:
                # confirm and save redirect
                if self.user_confirm(
                    color_format(
                        "Redirect from {lightblue}{0}{default} doesn't exist "
                        'yet.\nDo you want to create it?',
                        redir.title())):
                    # If summary option is None, it takes the default
                    # i18n summary from i18n subdirectory with summary key.
                    summary = self.opt.summary or i18n.twtranslate(
                        site, 'ndashredir-create', {'title': origin})
                    redir.set_redirect_target(self.current_page, create=True,
                                              summary=summary)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    :type args: str
    """
    options = {}
    # Process global arguments to determine desired site
    local_args = pywikibot.handle_args(args)

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    gen_factory = pagegenerators.GeneratorFactory()

    # Process the pagegenerators options
    local_args = gen_factory.handle_args(local_args)

    # Parse command line arguments
    for arg in local_args:
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
    gen = gen_factory.getCombinedGenerator(preload=True)
    if gen:
        # pass generator and private options to the bot
        bot = DashRedirectBot(gen, **options)
        bot.run()  # guess what it does
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
