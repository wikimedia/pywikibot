#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script can be used to delete and undelete pages en masse.

Of course, you will need an admin account on the relevant wiki.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-always:          Don't prompt to delete pages, just do it.

-summary:         Supply a custom edit summary.

-undelete:        Actually undelete pages instead of deleting.
                  Obviously makes sense only with -page and -file.

Usage: python delete.py [-category categoryName]

Examples:

Delete everything in the category "To delete" without prompting.

    python delete.py -cat:"To delete" -always
"""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

from warnings import warn

import pywikibot

from pywikibot import exceptions
from pywikibot import i18n, pagegenerators, CurrentPageBot

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;':     pagegenerators.parameterHelp,
}


class DeletionRobot(CurrentPageBot):

    """This robot allows deletion of pages en masse."""

    def __init__(self, generator, summary, **kwargs):
        """
        Constructor.

        @param generator: the pages to work on
        @type  generator: iterable
        @param summary: the reason for the (un)deletion
        @type  summary: unicode
        """
        self.availableOptions.update({
            'undelete': False,
        })
        super(DeletionRobot, self).__init__(generator=generator, **kwargs)

        self.summary = summary

    def treat_page(self):
        """Process one page from the generator."""
        if self.getOption('undelete'):
            if self.current_page.exists():
                pywikibot.output(u'Skipping: {0} already exists.'.format(
                    self.current_page))
            else:
                self.current_page.undelete(self.summary)
        else:
            if self.current_page.exists():
                self.current_page.delete(self.summary,
                                         not self.getOption('always'),
                                         self.getOption('always'))
            else:
                pywikibot.output(u'Skipping: {0} does not exist.'.format(
                    self.current_page))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    pageName = ''
    summary = None
    generator = None
    options = {}

    # read command line parameters
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()
    mysite = pywikibot.Site()

    for arg in local_args:

        if arg == '-always':
            options['always'] = True
        elif arg.startswith('-summary'):
            if len(arg) == len('-summary'):
                summary = pywikibot.input(u'Enter a reason for the deletion:')
            else:
                summary = arg[len('-summary:'):]
        elif arg.startswith('-images'):
            warn('-image option is deprecated. Please use -imageused instead.',
                 exceptions.ArgumentDeprecationWarning)
            local_args.append('-imageused' + arg[7:])
        elif arg.startswith('-undelete'):
            options['undelete'] = True
        else:
            genFactory.handleArg(arg)
            found = arg.find(':') + 1
            if found:
                pageName = arg[found:]

        if not summary:
            un = 'un' if 'undelete' in options else ''
            if pageName:
                if arg.startswith('-cat') or arg.startswith('-subcats'):
                    summary = i18n.twtranslate(mysite, 'delete-from-category',
                                               {'page': pageName})
                elif arg.startswith('-links'):
                    summary = i18n.twtranslate(mysite, un + 'delete-linked-pages',
                                               {'page': pageName})
                elif arg.startswith('-ref'):
                    summary = i18n.twtranslate(mysite, 'delete-referring-pages',
                                               {'page': pageName})
                elif arg.startswith('-imageused'):
                    summary = i18n.twtranslate(mysite, un + 'delete-images',
                                               {'page': pageName})
            elif arg.startswith('-file'):
                summary = i18n.twtranslate(mysite, un + 'delete-from-file')

    generator = genFactory.getCombinedGenerator()
    # We are just deleting pages, so we have no need of using a preloading
    # page generator to actually get the text of those pages.
    if generator:
        if summary is None:
            summary = pywikibot.input(u'Enter a reason for the %sdeletion:'
                                      % ['', 'un'][options.get('undelete', False)])
        bot = DeletionRobot(generator, summary, **options)
        bot.run()
    else:
        # Show help text from the top of this file
        pywikibot.showHelp()


if __name__ == "__main__":
    main()
