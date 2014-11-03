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
__version__ = '$Id$'
#

import pywikibot
from pywikibot import i18n, pagegenerators, Bot

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;':     pagegenerators.parameterHelp,
}


class DeletionRobot(Bot):

    """ This robot allows deletion of pages en masse. """

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
        super(DeletionRobot, self).__init__(**kwargs)

        self.generator = generator
        self.summary = summary

    def run(self):
        """
        Run bot.

        Loop through everything in the page generator and delete it.
        """
        for page in self.generator:
            self.current_page = page

            if self.getOption('undelete'):
                page.undelete(self.summary)
            else:
                if page.exists():
                    page.delete(self.summary, not self.getOption('always'))
                else:
                    pywikibot.output(u'Skipping: %s does not exist.' % page)


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
            pywikibot.output('\n\03{lightred}-image option is deprecated. '
                             'Please use -imageused instead.\03{default}\n')
            local_args.append('-imageused' + arg[7:])
        elif arg.startswith('-undelete'):
            options['undelete'] = True
        else:
            genFactory.handleArg(arg)
            found = arg.find(':') + 1
            if found:
                pageName = arg[found:]

        if not summary:
            if pageName:
                if arg.startswith('-cat') or arg.startswith('-subcats'):
                    summary = i18n.twtranslate(mysite, 'delete-from-category',
                                               {'page': pageName})
                elif arg.startswith('-links'):
                    summary = i18n.twtranslate(mysite, 'delete-linked-pages',
                                               {'page': pageName})
                elif arg.startswith('-ref'):
                    summary = i18n.twtranslate(mysite, 'delete-referring-pages',
                                               {'page': pageName})
                elif arg.startswith('-imageused'):
                    summary = i18n.twtranslate(mysite, 'delete-images',
                                               {'page': pageName})
            elif arg.startswith('-file'):
                summary = i18n.twtranslate(mysite, 'delete-from-file')
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
