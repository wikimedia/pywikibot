#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This script can move pages.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-from and -to     The page to move from and the page to move to.

-noredirect       Leave no redirect behind.

-notalkpage       Do not move this page's talk page (if it exists)

-prefix           Move pages by adding a namespace prefix to the names of the
                  pages. (Will remove the old namespace prefix if any)
                  Argument can also be given as "-prefix:namespace:".

-always           Don't prompt to make changes, just do them.

-skipredirects    Skip redirect pages (Warning: increases server load)

-summary          Prompt for a custom summary, bypassing the predefined message
                  texts. Argument can also be given as "-summary:XYZ".

-pairs            Read pairs of file names from a file. The file must be in a
                  format [[frompage]] [[topage]] [[frompage]] [[topage]] ...
                  Argument can also be given as "-pairs:filename"

"""
#
# (C) Leonardo Gregianin, 2006
# (C) Andreas J. Schwab, 2007
# (C) Pywikibot team, 2006-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import re
import pywikibot
from pywikibot import i18n, pagegenerators, Bot

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;':     pagegenerators.parameterHelp,
}


class MovePagesBot(Bot):

    """Page move bot."""

    def __init__(self, generator, **kwargs):
        self.availableOptions.update({
            'prefix': None,
            'noredirect': False,
            'movetalkpage': True,
            'skipredirects': False,
            'summary': None,
        })
        super(MovePagesBot, self).__init__(**kwargs)

        self.generator = generator
        self.appendAll = False
        self.regexAll = False
        self.noNamespace = False

    def moveOne(self, page, newPageTitle):
        try:
            msg = self.getOption('summary')
            if not msg:
                msg = i18n.twtranslate(page.site, 'movepages-moving')
            pywikibot.output(u'Moving page %s to [[%s]]'
                             % (page.title(asLink=True),
                                newPageTitle))
            page.move(newPageTitle, reason=msg, movetalkpage=self.getOption('movetalkpage'),
                      deleteAndMove=self.getOption('noredirect'))
        except pywikibot.PageRelatedError as error:
            pywikibot.output(error)

    def treat(self, page):
        self.current_page = page
        if self.getOption('skipredirects') and page.isRedirectPage():
            pywikibot.output(u'Page %s is a redirect; skipping.' % page.title())
            return
        pagetitle = page.title(withNamespace=False)
        namesp = page.site.namespace(page.namespace())
        if self.appendAll:
            newPageTitle = (u'%s%s%s'
                            % (self.pagestart, pagetitle, self.pageend))
            if not self.noNamespace and namesp:
                newPageTitle = (u'%s:%s' % (namesp, newPageTitle))
        elif self.regexAll:
            newPageTitle = self.regex.sub(self.replacePattern, pagetitle)
            if not self.noNamespace and namesp:
                newPageTitle = (u'%s:%s' % (namesp, newPageTitle))
        if self.getOption('prefix'):
            newPageTitle = (u'%s%s' % (self.getOption('prefix'), pagetitle))
        if self.getOption('prefix') or self.appendAll or self.regexAll:
            if not self.getOption('always'):
                choice2 = pywikibot.input_choice(
                    u'Change the page title to "%s"?' % newPageTitle,
                    [('yes', 'y'), ('no', 'n'), ('all', 'a')])
                if choice2 == 'y':
                    self.moveOne(page, newPageTitle)
                elif choice2 == 'a':
                    self.options['always'] = True
                    self.moveOne(page, newPageTitle)
                elif choice2 == 'n':
                    pass
                else:
                    self.treat(page)
            else:
                self.moveOne(page, newPageTitle)
        else:
            choice = pywikibot.input_choice(u'What do you want to do?',
                                            [('change page name', 'c'),
                                             ('append to page name', 'a'),
                                             ('use a regular expression', 'r'),
                                             ('next page', 'n')])
            if choice == 'c':
                newPageTitle = pywikibot.input(u'New page name:')
                self.moveOne(page, newPageTitle)
            elif choice == 'a':
                self.pagestart = pywikibot.input(u'Append this to the start:')
                self.pageend = pywikibot.input(u'Append this to the end:')
                newPageTitle = (u'%s%s%s'
                                % (self.pagestart, pagetitle, self.pageend))
                if namesp:
                    if pywikibot.input_yn(u'Do you want to remove the '
                                          'namespace prefix "%s:"?' % namesp,
                                          automatic_quit=False):
                        self.noNamespace = True
                    else:
                        newPageTitle = (u'%s:%s' % (namesp, newPageTitle))
                choice2 = pywikibot.input_choice(
                    u'Change the page title to "%s"?'
                    % newPageTitle, [('yes', 'y'), ('no', 'n'), ('all', 'a')])
                if choice2 == 'y':
                    self.moveOne(page, newPageTitle)
                elif choice2 == 'a':
                    self.appendAll = True
                    self.moveOne(page, newPageTitle)
                elif choice2 == 'n':
                    pass
                else:
                    self.treat(page)
            elif choice == 'r':
                searchPattern = pywikibot.input(u'Enter the search pattern:')
                self.replacePattern = pywikibot.input(
                    u'Enter the replace pattern:')
                self.regex = re.compile(searchPattern)
                if page.title() == page.title(withNamespace=False):
                    newPageTitle = self.regex.sub(self.replacePattern,
                                                  page.title())
                else:
                    if pywikibot.input_yn(u'Do you want to remove the '
                                          'namespace prefix "%s:"?' % namesp,
                                          automatic_quit=False):
                        newPageTitle = self.regex.sub(
                            self.replacePattern, page.title(withNamespace=False))
                        self.noNamespace = True
                    else:
                        newPageTitle = self.regex.sub(self.replacePattern,
                                                      page.title())
                choice2 = pywikibot.input_choice(
                    u'Change the page title to "%s"?'
                    % newPageTitle, [('yes', 'y'), ('no', 'n'), ('all', 'a')])
                if choice2 == 'y':
                    self.moveOne(page, newPageTitle)
                elif choice2 == 'a':
                    self.regexAll = True
                    self.moveOne(page, newPageTitle)
                elif choice2 == 'n':
                    pass
                else:
                    self.treat(page)
            elif choice == 'n':
                pass
            else:
                self.treat(page)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    gen = None
    oldName = None
    options = {}
    fromToPairs = []

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg.startswith('-pairs'):
            if len(arg) == len('-pairs'):
                filename = pywikibot.input(
                    u'Enter the name of the file containing pairs:')
            else:
                filename = arg[len('-pairs:'):]
            oldName1 = None
            for page in pagegenerators.TextfilePageGenerator(filename):
                if oldName1:
                    fromToPairs.append([oldName1, page.title()])
                    oldName1 = None
                else:
                    oldName1 = page.title()
            if oldName1:
                pywikibot.warning(
                    u'file %s contains odd number of links' % filename)
        elif arg == '-noredirect':
            options['noredirect'] = True
        elif arg == '-notalkpage':
            options['movetalkpage'] = False
        elif arg == '-always':
            options['always'] = True
        elif arg == '-skipredirects':
            options['skipredirects'] = True
        elif arg.startswith('-from:'):
            if oldName:
                pywikibot.warning(u'-from:%s without -to:' % oldName)
            oldName = arg[len('-from:'):]
        elif arg.startswith('-to:'):
            if oldName:
                fromToPairs.append([oldName, arg[len('-to:'):]])
                oldName = None
            else:
                pywikibot.warning(u'%s without -from' % arg)
        elif arg.startswith('-prefix'):
            if len(arg) == len('-prefix'):
                options['prefix'] = pywikibot.input(u'Enter the prefix:')
            else:
                options['prefix'] = arg[8:]
        elif arg.startswith('-summary'):
            if len(arg) == len('-summary'):
                options['summary'] = pywikibot.input(u'Enter the summary:')
            else:
                options['summary'] = arg[9:]
        else:
            genFactory.handleArg(arg)

    if oldName:
        pywikibot.warning(u'-from:%s without -to:' % oldName)
    site = pywikibot.Site()
    for pair in fromToPairs:
        page = pywikibot.Page(site, pair[0])
        bot = MovePagesBot(None, **options)
        bot.moveOne(page, pair[1])

    if not gen:
        gen = genFactory.getCombinedGenerator()
    if gen:
        preloadingGen = pagegenerators.PreloadingGenerator(gen)
        bot = MovePagesBot(preloadingGen, **options)
        bot.run()
    elif not fromToPairs:
        pywikibot.showHelp()

if __name__ == '__main__':
    main()
