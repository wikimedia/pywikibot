#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot goes over multiple pages of a wiki, and edits them without changes.

This is for example used to get category links in templates
working.

This script understands various command-line arguments:

&params;

-purge            Do not touch but purge the page
-botflag          Force botflag in case of edits with changes.

"""
#
# (C) Pywikibot team, 2009-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot

from pywikibot import pagegenerators

from pywikibot.bot import MultipleSitesBot

docuReplacements = {'&params;': pagegenerators.parameterHelp}


class TouchBot(MultipleSitesBot):

    """Page touch bot."""

    def __init__(self, generator, **kwargs):
        """Initialize a TouchBot instance with the options and generator."""
        self.availableOptions.update({
            'botflag': False,
        })
        super(TouchBot, self).__init__(generator=generator, **kwargs)

    def treat(self, page):
        """Touch the given page."""
        try:
            page.touch(botflag=self.getOption('botflag'))
        except pywikibot.NoPage:
            pywikibot.error(u"Page %s does not exist."
                            % page.title(asLink=True))
        except pywikibot.LockedPage:
            pywikibot.error(u"Page %s is locked."
                            % page.title(asLink=True))
        except pywikibot.PageNotSaved:
            pywikibot.error(u"Page %s not saved."
                            % page.title(asLink=True))


class PurgeBot(MultipleSitesBot):

    """Purge each page on the generator."""

    def treat(self, page):
        """Purge the given page."""
        pywikibot.output(u'Page %s%s purged'
                         % (page.title(asLink=True),
                            "" if page.purge() else " not"))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    gen = None
    options = {}

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    bot_class = TouchBot
    for arg in local_args:
        if arg == '-purge':
            bot_class = PurgeBot
        elif arg == '-redir':
            pywikibot.output(u'-redirect option is deprecated, '
                             'do not use it anymore.')
        elif not genFactory.handleArg(arg) and arg.startswith("-"):
            # -botflag
            options[arg[1:].lower()] = True

    gen = genFactory.getCombinedGenerator(preload=True)
    if gen:
        bot = bot_class(generator=gen, **options)
        pywikibot.Site().login()
        bot.run()
        return True
    else:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False


if __name__ == "__main__":
    main()
