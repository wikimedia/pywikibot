#!/usr/bin/python3
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
# (C) Pywikibot team, 2009-2022
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from pywikibot import pagegenerators
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
            page.touch(botflag=self.opt.botflag)
        except (NoCreateError, NoPageError):
            pywikibot.error('Page {} does not exist.'
                            .format(page.title(as_link=True)))
        except LockedPageError:
            pywikibot.error('Page {} is locked.'
                            .format(page.title(as_link=True)))
        except PageSaveRelatedError as e:
            pywikibot.error('Page {} not saved:\n{}'.format(page, e.args))
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

    def treat(self, page) -> None:
        """Purge the given page."""
        done = page.purge(**self.opt)
        if done:
            self.counter['purge'] += 1
        pywikibot.output('Page {}{} purged'
                         .format(page, '' if done else ' not'))


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}

    # Process global and pagegenerators args
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()
    local_args = gen_factory.handle_args(local_args)

    bot_class = TouchBot
    for arg in local_args:
        if arg == '-purge':
            bot_class = PurgeBot
        elif arg.startswith('-'):
            options[arg[1:].lower()] = True

    if gen_factory.gens:
        gen = gen_factory.getCombinedGenerator(preload=True)
        pywikibot.Site().login()
        bot_class(generator=gen, **options).run()
    else:
        pywikibot.bot.suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
