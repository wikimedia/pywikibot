# -*- coding: utf-8 -*-
"""
This script can be used to protect and unprotect pages en masse.
Of course, you will need an admin account on the relevant wiki.


These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-always:          Don't prompt to protect pages, just do it.

-summary:         Supply a custom edit summary.

-unprotect:       Actually unprotect pages instead of protecting

-edit:PROTECTION_LEVEL Set edit protection level to PROTECTION_LEVEL

-move:PROTECTION_LEVEL Set move protection level to PROTECTION_LEVEL

## Without support ##
## -create:PROTECTION_LEVEL Set move protection level to PROTECTION_LEVEL ##

Values for PROTECTION_LEVEL are: sysop, autoconfirmed, none.
If an operation parameter (edit, move or create) is not specified, default
protection level is 'sysop' (or 'none' if -unprotect).

Usage: python protect.py <OPTIONS>

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
# (c) Pywikibot team, 2008-2014
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


class ProtectionRobot:
    """ This bot allows protection of pages en masse. """

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
        """ Starts the bot's action.
        Loop through everything in the page generator and (un)protect it.

        """
        for page in self.generator:
            pywikibot.output(u'Processing page %s' % page.title())
            page.protect(unprotect=self.unprotect, reason=self.summary,
                         prompt=self.prompt, edit=self.edit, move=self.move)


def choiceProtectionLevel(operation, default):
    """ Asks a valid protection level for "operation".
    Returns the protection level chosen by user.

    """
    default = default[0]
    firstChar = map(lambda level: level[0], protectionLevels)
    choiceChar = pywikibot.inputChoice('Choice a protection level to %s:'
                                       % operation,
                                       protectionLevels, firstChar,
                                       default=default)
    for level in protectionLevels:
        if level.startswith(choiceChar):
            return level


def main(*args):
    global protectionLevels
    protectionLevels = ['sysop', 'autoconfirmed', 'none']

    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    pageName = ''
    summary = None
    always = False
    generator = None
    edit = ''
    move = ''
    defaultProtection = 'sysop'

    # read command line parameters
    local_args = pywikibot.handleArgs(*args)
    genFactory = pagegenerators.GeneratorFactory()
    mysite = pywikibot.Site()

    for arg in local_args:
        if arg == '-always':
            always = True
        elif arg.startswith('-summary'):
            if len(arg) == len('-summary'):
                summary = pywikibot.input(u'Enter a reason for the protection:')
            else:
                summary = arg[len('-summary:'):]
        elif arg.startswith('-images'):
            pywikibot.output('\n\03{lightred}-image option is deprecated. '
                             'Please use -imagelinks instead.\03{default}\n')
            local_args.append('-imagelinks' + arg[7:])
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
        else:
            genFactory.handleArg(arg)
            found = arg.find(':') + 1
            if found:
                pageName = arg[found:]

        if not summary:
            if pageName:
                if arg.startswith('cat') or arg.startswith('subcats'):
                    summary = i18n.twtranslate(mysite, 'protect-category',
                                               {'cat': pageName})
                elif arg.startswith('links'):
                    summary = i18n.twtranslate(mysite, 'protect-links',
                                               {'page': pageName})
                elif arg.startswith('ref'):
                    summary = i18n.twtranslate(mysite, 'protect-ref',
                                               {'page': pageName})
                elif arg.startswith('imageused'):
                    summary = i18n.twtranslate(mysite, 'protect-images',
                                               {'page': pageName})
            elif arg.startswith('file'):
                summary = i18n.twtranslate(mysite, 'protect-simple')

    generator = genFactory.getCombinedGenerator()
    # We are just protecting pages, so we have no need of using a preloading
    # page generator to actually get the text of those pages.
    if generator:
        if summary is None:
            summary = pywikibot.input(u'Enter a reason for the %sprotection:'
                                      % ['', 'un'][protectionLevels == 'none'])
        if not edit:
            edit = defaultProtection
        if not move:
            move = defaultProtection
        bot = ProtectionRobot(generator, summary, always, edit=edit, move=move)
        bot.run()
    else:
        # Show help text from the top of this file
        pywikibot.showHelp()


if __name__ == "__main__":
    main()
