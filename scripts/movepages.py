#!/usr/bin/env python3
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
from functools import partial
from itertools import zip_longest

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
        self.create_title = None

    def move_one(self, page, new_page_tite) -> None:
        """Move one page to new_page_tite."""
        msg = self.opt.summary
        if not msg:
            msg = i18n.twtranslate(page.site, 'movepages-moving')
        pywikibot.info(f'Moving page {page} to [[{new_page_tite}]]')
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

    @staticmethod
    def _select_action(page):
        """Manage interactive choices."""

        def create_new_title_change(page, new_title=None):
            """Change helper function."""
            if new_title is None:
                return pywikibot.input('New page name:')
            return new_title

        def create_new_title_append(start, end, page, namespace=None):
            """Append helper function."""
            page_title = page.title(with_ns=False)
            new_page_tite = f'{start}{page_title}{end}'
            if namespace is not None:
                new_page_tite = f'{namespace}:{new_page_tite}'
            return new_page_tite

        def create_new_title_regex(regex, replacement, page, namespace=None):
            """Replace helper function."""
            page_title = page.title(with_ns=False)
            new_page_title = regex.sub(replacement, page_title)
            if namespace is not None:
                new_page_title = f'{namespace}:{new_page_title}'
            return new_page_title

        def manage_namespace(page):
            """Manage interactive choices for namespace prefix."""
            namespace = page.site.namespace(page.namespace())
            q = pywikibot.input_yn('Do you want to remove the '
                                   'namespace prefix "{}:"?'.format(namespace),
                                   automatic_quit=False)
            return None if q else namespace

        choice = pywikibot.input_choice('What do you want to do?',
                                        [('change page name', 'c'),
                                         ('append to page name', 'a'),
                                         ('use a regular expression', 'r'),
                                         ('next page', 'n')])
        if choice == 'c':
            handler = partial(create_new_title_change,
                              new_title=create_new_title_change(page))
            choices = [('yes', 'y'), ('no', 'n')]
        elif choice == 'a':
            start = pywikibot.input('Append this to the start:')
            end = pywikibot.input('Append this to the end:')
            ns = manage_namespace(page)

            handler = partial(create_new_title_append,
                              start, end, namespace=ns)
            choices = [('yes', 'y'), ('no', 'n'), ('all', 'a')]
        elif choice == 'r':
            search_pattern = pywikibot.input('Enter the search pattern:')
            regex = re.compile(search_pattern)
            replacement = pywikibot.input('Enter the replace pattern:')
            ns = manage_namespace(page)

            handler = partial(create_new_title_regex,
                              regex, replacement, namespace=ns)
            choices = [('yes', 'y'), ('no', 'n'), ('all', 'a')]
        else:
            handler = None
            choices = []

        return handler, choices

    def _title_creator(self, page, prefix):
        """Create function to generate new title."""

        def create_new_title_prefix(prefix, page):
            """Replace prefix helper function."""
            page_title = page.title(with_ns=False)
            return f'{prefix}{page_title}'

        if prefix:
            handler = partial(create_new_title_prefix, prefix)
            choices = [('yes', 'y'), ('no', 'n'), ('all', 'a')]
        else:
            handler, choices = self._select_action(page)

        return choices, handler

    def treat_page(self) -> None:
        """Treat a single page."""
        page = self.current_page

        if not self.opt.always:
            choices, create_title = self._title_creator(page, self.opt.prefix)

            if create_title is None:
                return

            self.create_title = create_title

            choice = pywikibot.input_choice(
                'Change the page title '
                'to {!r}?'.format(create_title(page)),
                choices)

            if choice == 'y':
                pass
            elif choice == 'a':
                self.opt.always = True
            else:
                return

        new_page_title = self.create_title(page)
        self.move_one(page, new_page_title)


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
        if not opt.startswith('-'):
            continue
        opt = opt[1:]
        if opt == 'pairsfile':
            filename = value or pywikibot.input(
                'Enter the name of the file containing pairs:')
            page_gen = [pagegenerators.TextIOPageGenerator(filename)] * 2
            for old_page, new_page in zip_longest(*page_gen, fillvalue=None):
                if new_page is None:
                    pywikibot.warning(
                        'file {} contains odd number '
                        'of links'.format(filename))
                else:
                    from_to_pairs.append([old_page.title(), new_page.title()])
        elif opt in ('always', 'noredirect', 'skipredirects'):
            options[opt] = True
        elif opt in ('notalkpage', 'nosubpages'):
            options[opt.replace('no', 'move', 1)] = False
        elif opt == 'from':
            if old_name:
                pywikibot.warning(f'-from:{old_name} without -to:')
            old_name = value
        elif opt == 'to':
            if old_name:
                from_to_pairs.append([old_name, value])
                old_name = None
            else:
                pywikibot.warning(f'{arg} without -from')
        elif opt == 'prefix':
            options[opt] = value or pywikibot.input('Enter the prefix:')
        elif opt == 'summary':
            options[opt] = value or pywikibot.input('Enter the summary:')

    if old_name:
        pywikibot.warning(f'-from:{old_name} without -to:')

    site = pywikibot.Site()

    if not site.logged_in():
        site.login()

    bot = MovePagesBot(**options)
    for old_title, new_title in from_to_pairs:
        bot.move_one(pywikibot.Page(site, old_title), new_title)

    gen = gen_factory.getCombinedGenerator(preload=True)
    if gen:
        bot = MovePagesBot(generator=gen, **options)
        bot.run()
    elif not from_to_pairs:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
