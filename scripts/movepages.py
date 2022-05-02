#!/usr/bin/python3
"""
This script can move pages.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-from and -to     The page to move from and the page to move to.

-noredirect       Leave no redirect behind.

-notalkpage       Do not move this page's talk page (if it exists)

-nosubpages       Do not move subpages

-prefix           Move pages by adding a namespace prefix to the names of the
                  pages. (Will remove the old namespace prefix if any)
                  Argument can also be given as "-prefix:namespace:".

-always           Don't prompt to make changes, just do them.

-skipredirects    Skip redirect pages (Warning: increases server load)

-summary          Prompt for a custom summary, bypassing the predefined message
                  texts. Argument can also be given as "-summary:XYZ".

-pairsfile        Read pairs of file names from a file. The file must be in a
                  format [[frompage]] [[topage]] [[frompage]] [[topage]] ...
                  Argument can also be given as "-pairsfile:filename"

"""
#
# (C) Pywikibot team, 2006-2022
#
# Distributed under the terms of the MIT license.
#
import re

import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.bot import CurrentPageBot
from pywikibot.exceptions import PageRelatedError


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class MovePagesBot(CurrentPageBot):

    """Page move bot.

    .. versionchanged:: 7.2
       `movesubpages` option was added
    """

    update_options = {
        'prefix': '',
        'noredirect': False,
        'movetalkpage': True,
        'movesubpages': True,
        'skipredirects': False,
        'summary': '',
    }

    def __init__(self, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)
        self.appendAll = False
        self.regexAll = False
        self.noNamespace = False

    def move_one(self, page, new_page_tite) -> None:
        """Move one page to new_page_tite."""
        msg = self.opt.summary
        if not msg:
            msg = i18n.twtranslate(page.site, 'movepages-moving')
        pywikibot.output('Moving page {} to [[{}]]'
                         .format(page, new_page_tite))
        try:
            page.move(new_page_tite, reason=msg,
                      movetalk=self.opt.movetalkpage,
                      movesubpages=self.opt.movesubpages,
                      noredirect=self.opt.noredirect)
        except PageRelatedError as e:
            pywikibot.error(e)

    def skip_page(self, page):
        """Treat only non-redirect pages if 'skipredirects' is set."""
        if self.opt.skipredirects and page.isRedirectPage():
            pywikibot.warning(
                'Page {page} on {page.site} is a redirect; skipping'
                .format(page=page))
            return True
        return super().skip_page(page)

    def treat_page(self) -> None:
        """Treat a single page."""
        page = self.current_page
        pagetitle = page.title(with_ns=False)
        namesp = page.site.namespace(page.namespace())

        if self.appendAll:
            new_page_tite = '{}{}{}'.format(self.pagestart, pagetitle,
                                            self.pageend)
            if not self.noNamespace and namesp:
                new_page_tite = '{}:{}'.format(namesp, new_page_tite)
        elif self.regexAll:
            new_page_tite = self.regex.sub(self.replacePattern, pagetitle)
            if not self.noNamespace and namesp:
                new_page_tite = '{}:{}'.format(namesp, new_page_tite)
        if self.opt.prefix:
            new_page_tite = '{}{}'.format(self.opt.prefix, pagetitle)
        if self.opt.prefix or self.appendAll or self.regexAll:
            if self.user_confirm('Change the page title to {!r}?'
                                 .format(new_page_tite)):
                self.move_one(page, new_page_tite)
            return

        # else:
        choice = pywikibot.input_choice('What do you want to do?',
                                        [('change page name', 'c'),
                                         ('append to page name', 'a'),
                                         ('use a regular expression', 'r'),
                                         ('next page', 'n')])
        if choice == 'c':
            new_page_tite = pywikibot.input('New page name:')
            self.move_one(page, new_page_tite)
        elif choice == 'a':
            self.pagestart = pywikibot.input('Append this to the start:')
            self.pageend = pywikibot.input('Append this to the end:')
            new_page_tite = ('{}{}{}'.format(self.pagestart, pagetitle,
                                             self.pageend))
            if namesp:
                if pywikibot.input_yn('Do you want to remove the '
                                      'namespace prefix "{}:"?'.format(namesp),
                                      automatic_quit=False):
                    self.noNamespace = True
                else:
                    new_page_tite = ('{}:{}'.format(namesp, new_page_tite))
            choice2 = pywikibot.input_choice(
                'Change the page title to {!r}?'.format(new_page_tite),
                [('yes', 'y'), ('no', 'n'), ('all', 'a')])
            if choice2 == 'y':
                self.move_one(page, new_page_tite)
            elif choice2 == 'a':
                self.appendAll = True
                self.move_one(page, new_page_tite)
        elif choice == 'r':
            search_pattern = pywikibot.input('Enter the search pattern:')
            self.replacePattern = pywikibot.input(
                'Enter the replace pattern:')
            self.regex = re.compile(search_pattern)
            if page.title() == page.title(with_ns=False):
                new_page_tite = self.regex.sub(self.replacePattern,
                                               page.title())
            else:
                if pywikibot.input_yn('Do you want to remove the '
                                      'namespace prefix "{}:"?'.format(namesp),
                                      automatic_quit=False):
                    new_page_tite = self.regex.sub(
                        self.replacePattern, page.title(with_ns=False))
                    self.noNamespace = True
                else:
                    new_page_tite = self.regex.sub(self.replacePattern,
                                                   page.title())
            choice2 = pywikibot.input_choice(
                'Change the page title to {!r}?'.format(new_page_tite),
                [('yes', 'y'), ('no', 'n'), ('all', 'a')])
            if choice2 == 'y':
                self.move_one(page, new_page_tite)
            elif choice2 == 'a':
                self.regexAll = True
                self.move_one(page, new_page_tite)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    old_name = None
    options = {}
    from_to_pairs = []

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    local_args = gen_factory.handle_args(local_args)

    for arg in local_args:
        opt, _, value = arg.partition(':')
        if opt.startswith('-'):
            continue
        opt = opt[1:]
        if opt == 'pairsfile':
            filename = value or pywikibot.input(
                'Enter the name of the file containing pairs:')
            old_name1 = None
            for page in pagegenerators.TextIOPageGenerator(filename):
                if old_name1:
                    from_to_pairs.append([old_name1, page.title()])
                    old_name1 = None
                else:
                    old_name1 = page.title()
            if old_name1:
                pywikibot.warning(
                    'file {} contains odd number of links'.format(filename))
        elif opt in ('always', 'noredirect', 'skipredirects'):
            options[opt] = True
        elif opt in ('notalkpage', 'nosubpages'):
            options[opt.replace('no', 'move', 1)] = False
        elif opt == 'from':
            if old_name:
                pywikibot.warning('-from:{} without -to:'.format(old_name))
            old_name = value
        elif opt == 'to:':
            if old_name:
                from_to_pairs.append([old_name, value])
                old_name = None
            else:
                pywikibot.warning('{} without -from'.format(arg))
        elif opt == 'prefix':
            options[opt] = value or pywikibot.input('Enter the prefix:')
        elif opt == 'summary':
            options[opt] = value or pywikibot.input('Enter the summary:')

    if old_name:
        pywikibot.warning('-from:{} without -to:'.format(old_name))

    site = pywikibot.Site()

    if not site.logged_in():
        site.login()

    for pair in from_to_pairs:
        page = pywikibot.Page(site, pair[0])
        bot = MovePagesBot(**options)
        bot.move_one(page, pair[1])

    gen = gen_factory.getCombinedGenerator(preload=True)
    if gen:
        bot = MovePagesBot(generator=gen, **options)
        bot.run()
    elif not from_to_pairs:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
