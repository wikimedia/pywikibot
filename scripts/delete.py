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
# (c) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import pywikibot
from pywikibot import i18n
from pywikibot import pagegenerators

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;':     pagegenerators.parameterHelp,
}


class DeletionRobot:
    """ This robot allows deletion of pages en masse. """

    def __init__(self, generator, summary, always=False, undelete=True):
        """
        Arguments:
            * generator - A page generator.
            * always - Delete without prompting?

        """
        self.generator = generator
        self.summary = summary
        self.prompt = not always
        self.undelete = undelete

    def run(self):
        """ Starts the robot's action:
        Loop through everything in the page generator and delete it.

        """
        for page in self.generator:
            pywikibot.output(u'Processing page %s' % page.title())
            if self.undelete:
                page.undelete(self.summary)
            else:
                page.delete(self.summary, self.prompt)


def main():
    genFactory = pagegenerators.GeneratorFactory()
    pageName = ''
    summary = None
    always = False
    undelete = False
    generator = None

    # read command line parameters
    localargs = pywikibot.handleArgs()
    mysite = pywikibot.getSite()

    for arg in localargs:
        if arg == '-always':
            always = True
        elif arg.startswith('-summary'):
            if len(arg) == len('-summary'):
                summary = pywikibot.input(u'Enter a reason for the deletion:')
            else:
                summary = arg[len('-summary:'):]
        elif arg.startswith('-images'):
            pywikibot.output('\n\03{lightred}-image option is deprecated. '
                             'Please use -imageused instead.\03{default}\n')
            localargs.append('-imageused' + arg[7:])
        elif arg.startswith('-undelete'):
            undelete = True
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
                                      % ['', 'un'][undelete])
        bot = DeletionRobot(generator, summary, always, undelete)
        bot.run()
    else:
        # Show help text from the top of this file
        pywikibot.showHelp()


if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
