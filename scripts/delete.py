# -*- coding: utf-8 -*-
"""
This script can be used to delete and undelete pages en masse.
Of course, you will need an admin account on the relevant wiki.

Syntax: python delete.py [-category categoryName]

Command line options:

-page:       Delete specified page
-cat:        Delete all pages in the given category.
-nosubcats:  Don't delete pages in the subcategories.
-links:      Delete all pages linked from a given page.
-file:       Delete all pages listed in a text file.
-ref:        Delete all pages referring from a given page.
-images:     Delete all images used on a given page.
-always:     Don't prompt to delete pages, just do it.
-summary:    Supply a custom edit summary.
-undelete:   Actually undelete pages instead of deleting.
             Obviously makes sense only with -page and -file.

Examples:

Delete everything in the category "To delete" without prompting.

    python delete.py -cat:"To delete" -always
"""
#
# (C) Pywikibot team, 2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import pywikibot
from pywikibot import i18n, config, catlib, pagegenerators


class DeletionRobot:
    """ This robot allows deletion of pages en masse. """

    def __init__(self, generator, summary, always=False, undelete=True):
        """ Arguments:
        * generator - A page generator.
        * always - Delete without prompting?

        """
        self.generator = generator
        self.summary = summary
        self.always = always
        self.undelete = undelete

    def run(self):
        """ Starts the robot's action. """
        #Loop through everything in the page generator and delete it.
        for page in self.generator:
            pywikibot.output(u'Processing page %s' % page.title())
            if self.undelete:
                page.undelete(self.summary, throttle=True)
            else:
                page.delete(self.summary, not self.always, throttle=True)


def main():
    genFactory = pagegenerators.GeneratorFactory()
    pageName = ''
    singlePage = ''
    summary = ''
    always = False
    doSinglePage = False
    doCategory = False
    deleteSubcategories = True
    doRef = False
    doLinks = False
    doImages = False
    undelete = False
    fileName = ''
    generator = None

    # read command line parameters
    for arg in pywikibot.handleArgs():
        if arg == '-always':
            always = True
        elif arg.startswith('-summary'):
            if len(arg) == len('-summary'):
                summary = pywikibot.input(u'Enter a reason for the deletion:')
            else:
                summary = arg[len('-summary:'):]
        elif arg.startswith('-nosubcats'):
            deleteSubcategories = False
        elif arg.startswith('-images'):
            doImages = True
            if len(arg) == len('-images'):
                pageName = pywikibot.input(
                    u'Enter the page with the images to delete:')
            else:
                pageName = arg[len('-images'):]
        elif arg.startswith('-undelete'):
            undelete = True
        else:
            genFactory.handleArg(arg)
        if not summary:
            if arg.startswith('-category'):
                summary = i18n.twtranslate(mysite, 'delete-from-category', {'page': pageName})
            elif arg.startswith('-links'):
                summary = i18n.twtranslate(mysite, 'delete-linked-pages', {'page': pageName})
            elif arg.startswith('-ref'):
                summary = i18n.twtranslate(mysite, 'delete-referring-pages', {'page': pageName})
            elif arg.startswith('-file'):
                summary = i18n.twtranslate(mysite, 'delete-from-file')
    mysite = pywikibot.getSite()
    if doImages:
        if not summary:
            summary = i18n.twtranslate(mysite, 'delete-images',
                                       {'page': pageName})
        page = pywikibot.Page(mysite, pageName)
        generator = pagegenerators.ImagesPageGenerator(page)
    if not summary:
        summary = pywikibot.input(u'Enter a reason for the %sdeletion:'
                                  % ['', 'un'][undelete])
    if not generator:
        generator = genFactory.getCombinedGenerator()
    if not generator:
        # syntax error, show help text from the top of this file
        pywikibot.showHelp('delete')
        return
    if generator:
        pywikibot.setAction(summary)
        # We are just deleting pages, so we have no need of using a preloading
        # page generator to actually get the text of those pages.
        bot = DeletionRobot(generator, summary, always, undelete)
        bot.run()
if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
