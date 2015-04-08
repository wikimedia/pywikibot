#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
A bot to remove stale protection templates from pages that are not protected.

Very often sysops block the pages for a setted time but then the forget to
remove the warning! This script is useful if you want to remove those useless
warning left in these pages.

Parameters:

These command line parameters can be used to specify which pages to work on:

&params;

-xml              Retrieve information from a local XML dump (pages-articles
                  or pages-meta-current, see https://download.wikimedia.org).
                  Argument can also be given as "-xml:filename".

-protectedpages:  Check all the blocked pages; useful when you have not
                  categories or when you have problems with them. (add the
                  namespace after ":" where you want to check - default checks
                  all protected pages.)

-moveprotected:   Same as -protectedpages, for moveprotected pages

Furthermore, the following command line parameters are supported:

-always         Doesn't ask every time if the bot should make the change or not,
                do it always.

-show           When the bot can't delete the template from the page (wrong
                regex or something like that) it will ask you if it should show
                the page on your browser.
                (attention: pages included may give false positives!)

-move           The bot will check if the page is blocked also for the move
                option, not only for edit

--- Example of how to use the script ---

python blockpageschecker.py -always

python blockpageschecker.py -cat:Geography -always

python blockpageschecker.py -show -protectedpages:4

"""
#
# (C) Monobi a.k.a. Wikihermit, 2007
# (C) Filnik, 2007-2011
# (C) Nicolas Dumazet (NicDumZ), 2008-2009
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import time
import re
import webbrowser
import pywikibot
from pywikibot import i18n
from pywikibot import pagegenerators
from pywikibot import config

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;':     pagegenerators.parameterHelp,
}

# PREFERENCES

templateSemiProtection = {
    'en': None,
    'it': [r'\{\{(?:[Tt]emplate:|)[Aa]vvisobloccoparziale(?:|[ _]scad\|.*?|\|.*?)\}\}',
           r'\{\{(?:[Tt]emplate:|)[Aa]bp(?:|[ _]scad\|(?:.*?))\}\}'],
    'fr': [r'\{\{(?:[Tt]emplate:|' + u'[Mm]odèle:' +
           r'|)[Ss]emi[- ]?protection(|[^\}]*)\}\}'],
    'ja': [r'(?<!\<nowiki\>)\{\{(?:[Tt]emplate:|)' +
           u'半保護' + r'(?:[Ss]|)(?:\|.+|)\}\}(?!\<\/nowiki\>)\s*(?:\r\n|)*'],
}
# Regex to get the total-protection template
templateTotalProtection = {
    'en': None,
    'it': [r'\{\{(?:[Tt]emplate:|)[Aa]vvisoblocco(?:|[ _]scad\|(?:.*?)|minaccia|cancellata)\}\}',
           r'\{\{(?:[Tt]emplate:|)(?:[Cc][Tt]|[Cc]anc fatte|[Cc][Ee])\}\}',
           r'<div class="toccolours[ _]itwiki[ _]template[ _]avviso">(?:\s|\n)*?[Qq]uesta pagina'],
    'fr': [r'\{\{(?:[Tt]emplate:|' + u'[Mm]odèle:' +
           r'|)[Pp]rotection(|[^\}]*)\}\}',
           r'\{\{(?:[Tt]emplate:|' + u'[Mm]odèle:' + r'|)(?:[Pp]age|[Aa]rchive|' +
           u'[Mm]odèle) protégée' + r'?(|[^\}]*)\}\}'],
    'ja': [r'(?<!\<nowiki\>)\{\{(?:[Tt]emplate:|)' + u'保護(?:性急|)' +
           r'(?:[Ss]|)(?:\|.+|)\}\}(?!\<\/nowiki\>)\s*(?:\r\n|)*'],
}

# Regex to get the semi-protection move template
templateSemiMoveProtection = {
    'en': None,
    'it': [r'\{\{(?:[Tt]emplate:|)[Aa]vvisobloccospostamento(?:|[ _]scad\|.*?|\|.*?)\}\}'],
    'ja': [r'(?<!\<nowiki\>)\{\{(?:[Tt]emplate:|)' + u'移動半保護' +
           r'(?:[Ss]|)(?:\|.+|)\}\}(?!\<\/nowiki\>)\s*(?:\r\n|)*'],
}

# Regex to get the total-protection move template
templateTotalMoveProtection = {
    'en': None,
    'it': [r'\{\{(?:[Tt]emplate:|)[Aa]vvisobloccospostamento(?:|[ _]scad\|.*?|\|.*?)\}\}'],
    'ja': [r'(?<!\<nowiki\>)\{\{(?:[Tt]emplate:|)' + u'移動保護' +
           r'(?:[Ss]|)(?:\|.+|)\}\}(?!\<\/nowiki\>)\s*(?:\r\n|)*'],
}

# If you use only one template for all the type of protection, put it here.
# You may use only one template or an unique template and some other "old"
# template that the script should still check (as on it.wikipedia)
templateUnique = {
    'en': None,
    'it': [r'\{\{(?:[Tt]emplate:|)[Pp]rotetta\}\}'],
}

# Array: 0 => Semi-block, 1 => Total Block, 2 => Semi-Move, 3 => Total-Move,
#        4 => template-unique
templateNoRegex = {
    'it': ['{{Avvisobloccoparziale}}', '{{Avvisoblocco}}', None, None,
           '{{Protetta}}'],
    'fr': ['{{Semi-protection}}', '{{Protection}}', None, None, None],
    'ja': [u'{{半保護}}', u'{{保護}}', u'{{移動半保護}}', u'{{移動保護}}', None],
}

# Category where the bot will check
categoryToCheck = {
    'en': [u'Category:Protected'],
    'ar': [u'تصنيف:محتويات محمية'],
    'fr': [u'Category:Page semi-protégée', u'Category:Page protégée',
           u'Catégorie:Article protégé'],
    'he': [u'קטגוריה:ויקיפדיה: דפים מוגנים',
           u'קטגוריה:ויקיפדיה: דפים מוגנים חלקית'],
    'it': [u'Categoria:Pagine protette - scadute',
           u'Categoria:Pagine semiprotette', u'Categoria:Voci protette'],
    'ja': [u'Category:編集保護中の記事', u'Category:編集半保護中の記事',
           u'Category:移動保護中の記事'],
    'pt': [u'Category:!Páginas protegidas',
           u'Category:!Páginas semiprotegidas'],
    'zh': [u'Category:被保护的页面', u'Category:被保護的模板',
           u'Category:暂时不能移动的页面', u'Category:被半保护的页面'],
}

# Check list to block the users that haven't set their preferences
project_inserted = ['en', 'fr', 'it', 'ja', 'pt', 'zh']

# END PREFERENCES


def understandBlock(text, TTP, TSP, TSMP, TTMP, TU):
    """Understand if the page is blocked and if it has the right template."""
    if TTP:
        for catchRegex in TTP:  # TTP = templateTotalProtection
            resultCatch = re.findall(catchRegex, text)
            if resultCatch:
                return ('sysop-total', catchRegex)
    if TSP:
        for catchRegex in TSP:
            resultCatch = re.findall(catchRegex, text)
            if resultCatch:
                return ('autoconfirmed-total', catchRegex)
    if TU:
        for catchRegex in TU:
            resultCatch = re.findall(catchRegex, text)
            if resultCatch:
                return ('unique', catchRegex)
    if TSMP and TTMP and TTP != TTMP and TSP != TSMP:
        for catchRegex in TTMP:
            resultCatch = re.findall(catchRegex, text)
            if resultCatch:
                return ('sysop-move', catchRegex)
        for catchRegex in TSMP:
            resultCatch = re.findall(catchRegex, text)
            if resultCatch:
                return ('autoconfirmed-move', catchRegex)
    # If editable means that we have no regex, won't change anything with this
    # regex
    return ('editable', r'\A\n')


def showQuest(page):
    """Ask for an editor and invoke it."""
    quest = pywikibot.input_choice(
        u'Do you want to open the page?',
        [('with browser', 'b'), ('with gui', 'g'), ('no', 'n')], 'n',
        automatic_quit=False)
    site = page.site
    url = '%s://%s%s?redirect=no' % (site.protocol(),
                                     site.hostname(),
                                     site.nice_get_address(
                                         page.title(asUrl=True)))
    if quest == 'b':
        webbrowser.open(url)
    elif quest == 'g':
        from pywikibot import editor as editarticle
        editor = editarticle.TextEditor()
        editor.edit(page.text)


def main(*args):
    """
    Process command line arguments and perform task.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    # Loading the comments
    global categoryToCheck, project_inserted
    # always, define a generator to understand if the user sets one,
    # defining what's genFactory
    always = False
    generator = False
    show = False
    moveBlockCheck = False
    protectedpages = False
    protectType = 'edit'
    namespace = 0

    # To prevent Infinite loops
    errorCount = 0

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    # Process local args
    for arg in local_args:
        if arg == '-always':
            always = True
        elif arg == '-move':
            moveBlockCheck = True
        elif arg == '-show':
            show = True
        elif arg.startswith('-protectedpages'):
            protectedpages = True
            if len(arg) > 15:
                namespace = int(arg[16:])
        elif arg.startswith('-moveprotected'):
            protectedpages = True
            protectType = 'move'
            if len(arg) > 14:
                namespace = int(arg[15:])
        else:
            genFactory.handleArg(arg)

    if config.mylang not in project_inserted:
        pywikibot.output(u"Your project is not supported by this script.\n"
                         u"You have to edit the script and add it!")
        return

    site = pywikibot.Site()

    if protectedpages:
        generator = site.protectedpages(namespace=namespace, type=protectType)
    # Take the right templates to use, the category and the comment
    TSP = i18n.translate(site, templateSemiProtection)
    TTP = i18n.translate(site, templateTotalProtection)
    TSMP = i18n.translate(site, templateSemiMoveProtection)
    TTMP = i18n.translate(site, templateTotalMoveProtection)
    TNR = i18n.translate(site, templateNoRegex)
    TU = i18n.translate(site, templateUnique)

    categories = i18n.translate(site, categoryToCheck)
    commentUsed = i18n.twtranslate(site, 'blockpageschecker-summary')
    if not generator:
        generator = genFactory.getCombinedGenerator()
    if not generator:
        generator = list()
        pywikibot.output(u'Loading categories...')
        # Define the category if no other generator has been setted
        for CAT in categories:
            cat = pywikibot.Category(site, CAT)
            # Define the generator
            gen = pagegenerators.CategorizedPageGenerator(cat)
            for pageCat in gen:
                generator.append(pageCat)
        pywikibot.output(u'Categories loaded, start!')
    # Main Loop
    preloadingGen = pagegenerators.PreloadingGenerator(generator, step=60)
    for page in preloadingGen:
        pagename = page.title(asLink=True)
        pywikibot.output('Loading %s...' % pagename)
        try:
            text = page.text
        except pywikibot.NoPage:
            pywikibot.output("%s doesn't exist! Skipping..." % pagename)
            continue
        except pywikibot.IsRedirectPage:
            pywikibot.output("%s is a redirect! Skipping..." % pagename)
            if show:
                showQuest(page)
            continue
        # FIXME: This check does not work :
        # PreloadingGenerator cannot set correctly page.editRestriction
        # (see bug 55322)
        # if not page.canBeEdited():
        #    pywikibot.output("%s is sysop-protected : this account can't edit "
        #                     "it! Skipping..." % pagename)
        #    continue
        restrictions = page.protection()
        try:
            editRestr = restrictions['edit']
        except KeyError:
            editRestr = None
        if not page.canBeEdited():
            pywikibot.output(u"%s is protected: "
                             u"this account can't edit it! Skipping..."
                             % pagename)
            continue

        # Understand, according to the template in the page, what should be the
        # protection and compare it with what there really is.
        TemplateInThePage = understandBlock(text, TTP, TSP, TSMP, TTMP, TU)
        # Only to see if the text is the same or not...
        oldtext = text
        # keep track of the changes for each step (edit then move)
        changes = -1

        if not editRestr:
            # page is not edit-protected
            # Deleting the template because the page doesn't need it.
            if TU:
                replaceToPerform = u'|'.join(TTP + TSP + TU)
            else:
                replaceToPerform = u'|'.join(TTP + TSP)
            text, changes = re.subn('<noinclude>(%s)</noinclude>'
                                    % replaceToPerform, '', text)
            if changes == 0:
                text, changes = re.subn('(%s)' % replaceToPerform, '', text)
            msg = u'The page is editable for all'
            if not moveBlockCheck:
                msg += u', deleting the template..'
            pywikibot.output(u'%s.' % msg)

        elif editRestr[0] == 'sysop':
            # total edit protection
            if (TemplateInThePage[0] == 'sysop-total' and TTP) or \
               (TemplateInThePage[0] == 'unique' and TU):
                msg = 'The page is protected to the sysop'
                if not moveBlockCheck:
                    msg += ', skipping...'
                pywikibot.output(msg)
            else:
                pywikibot.output(u'The page is protected to the sysop, but the '
                                 u'template seems not correct. Fixing...')
                if TU:
                    text, changes = re.subn(TemplateInThePage[1], TNR[4], text)
                else:
                    text, changes = re.subn(TemplateInThePage[1], TNR[1], text)

        elif TSP or TU:
            # implicitely editRestr[0] = 'autoconfirmed', edit-Semi-protection
            if TemplateInThePage[0] == 'autoconfirmed-total' or \
               TemplateInThePage[0] == 'unique':
                msg = 'The page is editable only for the autoconfirmed users'
                if not moveBlockCheck:
                    msg += ', skipping...'
                pywikibot.output(msg)
            else:
                pywikibot.output(u'The page is editable only for the '
                                 u'autoconfirmed users, but the template '
                                 u'seems not correct. Fixing...')
                if TU:
                    text, changes = re.subn(TemplateInThePage[1], TNR[4], text)
                else:
                    text, changes = re.subn(TemplateInThePage[1], TNR[0], text)

        if changes == 0:
            # We tried to fix edit-protection templates, but it did not work.
            pywikibot.warning('No edit-protection template could be found')

        if moveBlockCheck and changes > -1:
            # checking move protection now
            try:
                moveRestr = restrictions['move']
            except KeyError:
                moveRestr = False
            changes = -1

            if not moveRestr:
                pywikibot.output(u'The page is movable for all, deleting the '
                                 u'template...')
                # Deleting the template because the page doesn't need it.
                if TU:
                    replaceToPerform = u'|'.join(TSMP + TTMP + TU)
                else:
                    replaceToPerform = u'|'.join(TSMP + TTMP)
                text, changes = re.subn('<noinclude>(%s)</noinclude>'
                                        % replaceToPerform, '', text)
                if changes == 0:
                    text, changes = re.subn('(%s)' % replaceToPerform, '', text)
            elif moveRestr[0] == 'sysop':
                # move-total-protection
                if (TemplateInThePage[0] == 'sysop-move' and TTMP) or \
                   (TemplateInThePage[0] == 'unique' and TU):
                    pywikibot.output(u'The page is protected from moving to '
                                     u'the sysop, skipping...')
                    if TU:
                        # no changes needed, better to revert the old text.
                        text = oldtext
                else:
                    pywikibot.output(u'The page is protected from moving to '
                                     u'the sysop, but the template seems not '
                                     u'correct. Fixing...')
                    if TU:
                        text, changes = re.subn(TemplateInThePage[1], TNR[4],
                                                text)
                    else:
                        text, changes = re.subn(TemplateInThePage[1], TNR[3],
                                                text)

            elif TSMP or TU:
                # implicitely moveRestr[0] = 'autoconfirmed',
                # move-semi-protection
                if TemplateInThePage[0] == 'autoconfirmed-move' or \
                   TemplateInThePage[0] == 'unique':
                    pywikibot.output(u'The page is movable only for the '
                                     u'autoconfirmed users, skipping...')
                    if TU:
                        # no changes needed, better to revert the old text.
                        text = oldtext
                else:
                    pywikibot.output(u'The page is movable only for the '
                                     u'autoconfirmed users, but the template '
                                     u'seems not correct. Fixing...')
                    if TU:
                        text, changes = re.subn(TemplateInThePage[1], TNR[4],
                                                text)
                    else:
                        text, changes = re.subn(TemplateInThePage[1], TNR[2],
                                                text)

            if changes == 0:
                # We tried to fix move-protection templates, but it did not work
                pywikibot.warning('No move-protection template could be found')

        if oldtext != text:
            # Ok, asking if the change has to be performed and do it if yes.
            pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                             % page.title())
            pywikibot.showDiff(oldtext, text)
            if not always:
                choice = pywikibot.input_choice(u'Do you want to accept these '
                                                u'changes?',
                                                [('Yes', 'y'), ('No', 'n'),
                                                 ('All', 'a')], 'n')
                if choice == 'a':
                    always = True
            if always or choice == 'y':
                while True:
                    try:
                        page.put(text, commentUsed, force=True)
                    except pywikibot.EditConflict:
                        pywikibot.output(u'Edit conflict! skip!')
                        break
                    except pywikibot.ServerError:
                        # Sometimes there is this error that's quite annoying
                        # because can block the whole process for nothing.
                        errorCount += 1
                        if errorCount < 5:
                            pywikibot.output(u'Server Error! Wait..')
                            time.sleep(3)
                            continue
                        else:
                            # Prevent Infinite Loops
                            raise pywikibot.ServerError(u'Fifth Server Error!')
                    except pywikibot.SpamfilterError as e:
                        pywikibot.output(u'Cannot change %s because of '
                                         u'blacklist entry %s'
                                         % (page.title(), e.url))
                        break
                    except pywikibot.LockedPage:
                        pywikibot.output(u'The page is still protected. '
                                         u'Skipping...')
                        break
                    except pywikibot.PageNotSaved as error:
                        pywikibot.output(u'Error putting page: %s'
                                         % (error.args,))
                        break
                    else:
                        # Break only if the errors are one after the other
                        errorCount = 0
                        break


if __name__ == "__main__":
    main()
