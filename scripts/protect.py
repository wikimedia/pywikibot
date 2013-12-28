# -*- coding: utf-8 -*-
"""
This script can be used to protect and unprotect pages en masse.
Of course, you will need an admin account on the relevant wiki.

Syntax: python protect.py OPTION...

Command line options:

-page:       Protect specified page
-cat:        Protect all pages in the given category.
-nosubcats:  Don't protect pages in the subcategories.
-links:      Protect all pages linked from a given page.
-file:       Protect all pages listed in a text file.
-ref:        Protect all pages referring from a given page.
-images:     Protect all images used on a given page.
-always:     Don't prompt to protect pages, just do it.
-summary:    Supply a custom edit summary.
-unprotect:   Actually unprotect pages instead of protecting
-edit:PROTECTION_LEVEL Set edit protection level to PROTECTION_LEVEL
-move:PROTECTION_LEVEL Set move protection level to PROTECTION_LEVEL

## Without support ##
## -create:PROTECTION_LEVEL Set move protection level to PROTECTION_LEVEL ##

Values for PROTECTION_LEVEL are: sysop, autoconfirmed, none.
If an operation parameter (edit, move or create) is not specified, default
protection level is 'sysop' (or 'none' if -unprotect).

Examples:

Protect everything in the category "To protect" prompting.
    python protect.py -cat:"To protect" -always

Unprotect all pages listed in text file "unprotect.txt" without prompting.
    python protect.py -file:unprotect.txt -unprotect
"""

#
# Written by http://it.wikisource.org/wiki/Utente:Qualc1
# Created by modifying delete.py
#
# (C) Pywikipedia bot team, 2008-2012
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import pywikibot
from pywikibot import i18n
from pywikibot import pagegenerators


class ProtectionRobot:
    """
    This robot allows protection of pages en masse.
    """

    def __init__(self, generator, summary, always=False, unprotect=False,
                 edit='sysop', move='sysop', create='sysop'):
        """
        Arguments:
            * generator - A page generator.
            * always - Protect without prompting?
            * edit, move, create - protection level for these operations
            * unprotect - unprotect pages (and ignore edit, move, create params)
        """
        self.generator = generator
        self.summary = summary
        self.prompt = not always
        self.unprotect = unprotect
        self.edit = edit
        self.move = move

    def run(self):
        """
        Starts the robot's action.
        """
        #Loop through everything in the page generator and (un)protect it.
        for page in self.generator:
            pywikibot.output(u'Processing page %s' % page.title())
            page.protect(unprotect=self.unprotect, reason=self.summary,
                         prompt=self.prompt, edit=self.edit,
                         move=self.move)


# Asks a valid protection level for "operation".
# Returns the protection level chosen by user.
def choiceProtectionLevel(operation, default):
    default = default[0]
    firstChar = map(lambda level: level[0], protectionLevels)
    choiceChar = pywikibot.inputChoice('Choice a protection level to %s:'
                                       % operation,
                                       protectionLevels, firstChar,
                                       default=default)
    for level in protectionLevels:
        if level.startswith(choiceChar):
            return level


def main():
    global protectionLevels
    protectionLevels = ['sysop', 'autoconfirmed', 'none']

    pageName = ''
    summary = ''
    always = False
    doSinglePage = False
    doCategory = False
    protectSubcategories = True
    doRef = False
    doLinks = False
    doImages = False
    fileName = ''
    gen = None
    edit = ''
    move = ''
    defaultProtection = 'sysop'

    # read command line parameters
    for arg in pywikibot.handleArgs():
        if arg == '-always':
            always = True
        elif arg.startswith('-file'):
            if len(arg) == len('-file'):
                fileName = pywikibot.input(u'Enter name of file to protect pages from:')
            else:
                fileName = arg[len('-file:'):]
        elif arg.startswith('-summary'):
            if len(arg) == len('-summary'):
                summary = pywikibot.input(u'Enter a reason for the protection:')
            else:
                summary = arg[len('-summary:'):]
        elif arg.startswith('-cat'):
            doCategory = True
            if len(arg) == len('-cat'):
                pageName = pywikibot.input(u'Enter the category to protect from:')
            else:
                pageName = arg[len('-cat:'):]
        elif arg.startswith('-nosubcats'):
            protectSubcategories = False
        elif arg.startswith('-links'):
            doLinks = True
            if len(arg) == len('-links'):
                pageName = pywikibot.input(u'Enter the page to protect from:')
            else:
                pageName = arg[len('-links:'):]
        elif arg.startswith('-ref'):
            doRef = True
            if len(arg) == len('-ref'):
                pageName = pywikibot.input(u'Enter the page to protect from:')
            else:
                pageName = arg[len('-ref:'):]
        elif arg.startswith('-page'):
            doSinglePage = True
            if len(arg) == len('-page'):
                pageName = pywikibot.input(u'Enter the page to protect:')
            else:
                pageName = arg[len('-page:'):]
        elif arg.startswith('-images'):
            doImages = True
            if len(arg) == len('-images'):
                pageName = pywikibot.input(u'Enter the page with the images to protect:')
            else:
                pageName = arg[len('-images:'):]
        elif arg.startswith('-unprotect'):
            defaultProtection = 'none'
        elif arg.startswith('-edit'):
            edit = arg[len('-edit:'):]
            if edit not in protectionLevels:
                edit = choiceProtectionLevel('edit', defaultProtection)
        elif arg.startswith('-move'):
            move = arg[len('-move:'):]
            if move not in protectionLevels:
                move = choiceProtectionLevel('move', defaultProtection)
        elif arg.startswith('-create'):
            create = arg[len('-create:'):]
            if create not in protectionLevels:
                create = choiceProtectionLevel('create', defaultProtection)

    mysite = pywikibot.getSite()

    if doSinglePage:
        if not summary:
            summary = pywikibot.input(u'Enter a reason for the protection:')
        page = pywikibot.Page(mysite, pageName)
        gen = iter([page])
    elif doCategory:
        if not summary:
            summary = i18n.twtranslate(mysite, 'protect-category', {'cat': pageName})
        ns = mysite.category_namespace()
        categoryPage = catlib.Category(mysite, ns + ':' + pageName)
        gen = pagegenerators.CategorizedPageGenerator(categoryPage, recurse=protectSubcategories)
    elif doLinks:
        if not summary:
            summary = i18n.twtranslate(mysite, 'protect-links', {'page': pageName})
        linksPage = pywikibot.Page(mysite, pageName)
        gen = pagegenerators.LinkedPageGenerator(linksPage)
    elif doRef:
        if not summary:
            summary = i18n.twtranslate(mysite, 'protect-ref', {'page': pageName})
        refPage = pywikibot.Page(mysite, pageName)
        gen = pagegenerators.ReferringPageGenerator(refPage)
    elif fileName:
        if not summary:
            summary = i18n.twtranslate(mysite, 'protect-simple')
        gen = pagegenerators.TextfilePageGenerator(fileName)
    elif doImages:
        if not summary:
            summary = i18n.twtranslate(mysite, 'protect-images', {'page': pageName})
        gen = pagegenerators.ImagesPageGenerator(pywikibot.Page(mysite, pageName))

    if gen:
        pywikibot.setAction(summary)
        # We are just protecting pages, so we have no need of using a preloading
        # page generator
        # to actually get the text of those pages.
        if not edit:
            edit = defaultProtection
        if not move:
            move = defaultProtection
        bot = ProtectionRobot(gen, summary, always, edit=edit, move=move)
        bot.run()
    else:
        pywikibot.showHelp(u'protect')

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
