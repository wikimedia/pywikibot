#!/usr/bin/env python3
"""
This bot goes over multiple pages of a wiki, and edits them without changes.

This is for example used to get category links in templates working.

Command-line arguments:

-purge                    Purge the page instead of touching it

Touch mode (default):

-botflag                  Force botflag in case of edits with changes.

Purge mode:

-converttitles            Convert titles to other variants if necessary
-forcelinkupdate          Update the links tables
-forcerecursivelinkupdate Update the links table, and update the links tables
                          for any page that uses this page as a template
-redirects                Automatically resolve redirects

&params;
"""
#
# (C) Pywikibot team, 2009-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from collections import defaultdict
from contextlib import suppress

import pywikibot
from pywikibot import config, pagegenerators
from pywikibot.bot import MultipleSitesBot
from pywikibot.exceptions import (
    LockedPageError,
    NoCreateError,
    NoPageError,
    PageSaveRelatedError,
)


docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


class TouchBot(MultipleSitesBot):

    """Page touch bot."""

    update_options = {
        'botflag': False,
    }

    def treat(self, page) -> None:
        """Touch the given page."""
        try:
            page.touch(bot=self.opt.botflag)
        except (NoCreateError, NoPageError):
            pywikibot.error(f'Page {page.title(as_link=True)} does not exist.')
        except LockedPageError:
            pywikibot.error(f'Page {page.title(as_link=True)} is locked.')
        except PageSaveRelatedError as e:
            pywikibot.error(f'Page {page} not saved:\n{e.args}')
        else:
            self.counter['touch'] += 1


class PurgeBot(MultipleSitesBot):

    """Purge each page on the generator."""

    available_options = {
        'converttitles': None,
        'forcelinkupdate': None,
        'forcerecursivelinkupdate': None,
        'redirects': None
    }

    def __init__(self, *args, **kwargs):
        """Initializer."""
        super().__init__(*args, **kwargs)
        self.pages = defaultdict(list)
        self.limit = {}

    def treat(self, page) -> None:
        """Purge the given page.

        .. versionchanged:: 8.0
           Enable batch purge using :meth:`APISite.purgepages()
           <pywikibot.site._apisite.APISite.purgepages>`
        """
        # We can have mutiple sites, save pages and cache rate limit
        self.pages[page.site].append(page)
        self.limit.setdefault(page.site, page.site.ratelimit('purge'))
        self.purgepages()

    def teardown(self):
        """Purge remaining pages if no KeyboardInterrupt was made.

        .. versionadded:: 8.0
        """
        if self.generator_completed:
            with suppress(KeyboardInterrupt):
                self.purgepages(flush=True)

        # show the counter even no purges were made
        self.counter['purge'] += 0

    def purgepages(self, flush=False):
        """Purge a bulk of page if rate limit exceeded.

        .. versionadded:: 8.0
        .. versionchanged:: 9.0
           :meth:`site.APISite.ratelimit()
           <pywikibot.site._apisite.APISite.ratelimit>` method is used
           to determine bulk length and delay.
        """
        for site, pagelist in self.pages.items():
            length = len(pagelist)
            if flush or length >= self.limit[site].hits:
                done = site.purgepages(pagelist, **self.opt)
                if done:
                    self.counter['purge'] += length
                self.pages[site].clear()

                pywikibot.info(
                    f"{length} pages{'' if done else ' not'} purged")
                if not flush and config.simulate is False:
                    delay = self.limit[site].delay * (length + 1)
                    if delay:
                        pywikibot.info(
                            f'Waiting {delay} seconds due to purge rate limit')
                        pywikibot.sleep(delay)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}
    unknown = []

    # Process global and pagegenerators args
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    local_args = gen_factory.handle_args(local_args)

    bot_class = TouchBot
    for arg in local_args:
        option = arg[1:]
        if arg == '-purge':
            bot_class = PurgeBot
        elif arg.startswith('-'):
            options[option.lower()] = True
        else:
            unknown.append(arg)

    if not pywikibot.bot.suggest_help(missing_generator=not gen_factory.gens,
                                      unknown_parameters=unknown):
        pywikibot.Site().login()
        gen = gen_factory.getCombinedGenerator(preload=bot_class == TouchBot)
        bot_class(generator=gen, **options).run()


if __name__ == '__main__':
    main()
