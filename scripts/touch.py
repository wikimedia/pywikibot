#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
This bot goes over multiple pages of a wiki, and edits them without
changing. This is for example used to get category links in templates
working.

This script understands various command-line arguments:

&params;

-purge            Do not touch but purge the page

-redir            specifies that the bot should work on redirect pages;
                  otherwise, they will be skipped.
"""
#
# (C) Pywikibot team, 2009-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import pywikibot
from pywikibot import pagegenerators

docuReplacements = {'&params;': pagegenerators.parameterHelp}


class TouchBot(pywikibot.Bot):

    def __init__(self, generator, **kwargs):
        self.availableOptions.update({
            'redir': False,  # include redirect pages
            'purge': False,  # purge only
        })

        super(TouchBot, self).__init__(**kwargs)
        self.generator = generator

    def run(self):
        for page in self.generator:
            if self.getOption('purge'):
                pywikibot.output(u'Page %s%s purged'
                                 % (page.title(asLink=True),
                                    "" if page.purge() else " not"))
                continue
            try:
                # get the page, and save it using the unmodified text.
                # whether or not getting a redirect throws an exception
                # depends on the variable self.touch_redirects.
                page.get(get_redirect=self.getOption('redir'))
                page.save("Pywikibot touch script")
            except pywikibot.NoPage:
                pywikibot.error(u"Page %s does not exist."
                                % page.title(asLink=True))
            except pywikibot.IsRedirectPage:
                pywikibot.warning(u"Page %s is a redirect; skipping."
                                  % page.title(asLink=True))
            except pywikibot.LockedPage:
                pywikibot.error(u"Page %s is locked."
                                % page.title(asLink=True))
            except pywikibot.PageNotSaved:
                pywikibot.error(u"Page %s not saved."
                                % page.title(asLink=True))


def main(*args):
    gen = None
    options = {}

    # Process global args and prepare generator args parser
    local_args = pywikibot.handleArgs(*args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if genFactory.handleArg(arg):
            continue
        if arg.startswith("-"):
            options[arg[1:].lower()] = True
    pywikibot.Site().login()
    gen = genFactory.getCombinedGenerator()
    if gen:
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        bot = TouchBot(preloadingGen, **options)
        bot.run()
    else:
        pywikibot.showHelp()


if __name__ == "__main__":
    main()
