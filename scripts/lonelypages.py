#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This is a script written to add the template "orphan" to the pages that aren't
linked by other pages. It can give some strange Errors sometime, I hope that
all of them are fixed in this version.

These command line parameters can be used to specify which pages to work on:

&params;

-xml              Retrieve information from a local XML dump (pages-articles
                  or pages-meta-current, see http://download.wikimedia.org).
                  Argument can also be given as "-xml:filename".

-page             Only edit a specific page.
                  Argument can also be given as "-page:pagetitle". You can
                  give this parameter multiple times to edit multiple pages.

Furthermore, the following command line parameters are supported:

-enable:          Enable or disable the bot via a Wiki Page.

-disambig:        Set a page where the bot save the name of the disambig
                  pages found (default: skip the pages)

-limit:           Set how many pages check.

-always           Always say yes, won't ask


--- Examples ---
python lonelypages.py -enable:User:Bot/CheckBot -always
"""
#
# (C) Pietrodn, it.wiki 2006-2007
# (C) Filnik, it.wiki 2007
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import re

import pywikibot
from pywikibot import i18n
from pywikibot import pagegenerators

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;':     pagegenerators.parameterHelp,
}

Template = {
    'ar': u'{{يتيمة|تاريخ={{نسخ:اسم_شهر}} {{نسخ:عام}}}}',
    'ca': u'{{Orfe|date={{subst:CURRENTMONTHNAME}} {{subst:CURRENTYEAR}}}}',
    'en': u'{{Orphan|date={{subst:CURRENTMONTHNAME}} {{subst:CURRENTYEAR}}}}',
    'it': u'{{O||mese={{subst:CURRENTMONTHNAME}} {{subst:CURRENTYEAR}}}}',
    'ja': u'{{孤立|{{subst:DATE}}}}',
    'zh': u'{{subst:Orphan/auto}}',
}

# Use regex to prevent to put the same template twice!
exception_regex = {
    'ar': [ur'\{\{(?:قالب:|)(يتيمة)[\|\}]'],
    'ca': [r'\{\{(?:template:|)(orfe)[\|\}]'],
    'en': [r'\{\{(?:template:|)(orphan)[\|\}]',
           r'\{\{(?:template:|)(wi)[\|\}]'],
    'it': [r'\{\{(?:template:|)(o|a)[\|\}]'],
    'ja': [ur'\{\{(?:template:|)(孤立)[\|\}]'],
    'zh': [r'\{\{(?:template:|)(orphan)[\|\}]'],
}


def main():
    enablePage = None  # Check if someone set an enablePage or not
    limit = 50000    # Hope that there aren't so many lonely pages in a project
    generator = None  # Check if bot should use default generator or not
    # Load all default generators!
    genFactory = pagegenerators.GeneratorFactory()
    nwpages = False  # Check variable for newpages
    always = False  # Check variable for always
    disambigPage = None  # If no disambigPage given, not use it.
    # Arguments!
    for arg in pywikibot.handleArgs():
        if arg.startswith('-enable'):
            if len(arg) == 7:
                enablePage = pywikibot.input(
                    u'Would you like to check if the bot should run or not?')
            else:
                enablePage = arg[8:]
        if arg.startswith('-disambig'):
            if len(arg) == 9:
                disambigPage = pywikibot.input(
                    u'In which page should the bot save the disambig pages?')
            else:
                disambigPage = arg[10:]
        elif arg.startswith('-limit'):
            if len(arg) == 6:
                limit = int(pywikibot.input(
                    u'How many pages do you want to check?'))
            else:
                limit = int(arg[7:])
        elif arg.startswith('-newpages'):
            if len(arg) == 9:
                nwlimit = 50  # Default: 50 pages
            else:
                nwlimit = int(arg[10:])
            generator = pywikibot.Site().newpages(number=nwlimit)
            nwpages = True
        elif arg == '-always':
            always = True
        else:
            genFactory.handleArg(arg)
    # Retrive the site
    wikiSite = pywikibot.Site()

    if not generator:
        generator = genFactory.getCombinedGenerator()

    # If the generator is not given, use the default one
    if not generator:
        generator = wikiSite.lonelypages(repeat=True, number=limit)
    # Take the configurations according to our project
    comment = i18n.twtranslate(wikiSite, 'lonelypages-comment-add-template')
    commentdisambig = i18n.twtranslate(wikiSite, 'lonelypages-comment-add-disambig-template')
    template = i18n.translate(wikiSite, Template)
    exception = i18n.translate(wikiSite, exception_regex)
    if template is None or exception is None:
        raise Exception("Missing configuration for site %r" % wikiSite)
    # EnablePage part
    if enablePage is not None:
        # Define the Page Object
        enable = pywikibot.Page(wikiSite, enablePage)
        # Loading the page's data
        try:
            getenable = enable.text
        except pywikibot.NoPage:
            pywikibot.output(
                u"%s doesn't esist, I use the page as if it was blank!"
                % enable.title())
            getenable = ''
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"%s is a redirect, skip!" % enable.title())
            getenable = ''
        # If the enable page is set to disable, turn off the bot
        # (useful when the bot is run on a server)
        if getenable != 'enable':
            pywikibot.output('The bot is disabled')
            return
    # DisambigPage part
    if disambigPage is not None:
        disambigpage = pywikibot.Page(wikiSite, disambigPage)
        try:
            disambigtext = disambigpage.get()
        except pywikibot.NoPage:
            pywikibot.output(u"%s doesn't esist, skip!" % disambigpage.title())
            disambigtext = ''
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"%s is a redirect, don't use it!"
                             % disambigpage.title())
            disambigPage = None
    # Main Loop
    for page in generator:
        if nwpages:
            # The newpages generator returns a tuple, not a Page object.
            page = page[0]
        pywikibot.output(u"Checking %s..." % page.title())
        if page.isRedirectPage():  # If redirect, skip!
            pywikibot.output(u'%s is a redirect! Skip...' % page.title())
            continue
        # refs is not a list, it's a generator while resList... is a list, yes.
        refs = page.getReferences()
        refsList = list()
        for j in refs:
            if j is None:
                # We have to find out why the function returns that value
                pywikibot.error(u'1 --> Skip page')
                continue
            refsList.append(j)
        # This isn't possible with a generator
        if refsList != []:
            pywikibot.output(u"%s isn't orphan! Skip..." % page.title())
            continue
        # Never understood how a list can turn in "None", but it happened :-S
        elif refsList is None:
            # We have to find out why the function returns that value
            pywikibot.error(u'2 --> Skip page')
            continue
        else:
            # no refs, no redirect; check if there's already the template
            try:
                oldtxt = page.get()
            except pywikibot.NoPage:
                pywikibot.output(u"%s doesn't exist! Skip..." % page.title())
                continue
            except pywikibot.IsRedirectPage:
                pywikibot.output(u"%s is a redirect! Skip..." % page.title())
                continue
            # I've used a loop in a loop. If I use continue in the second loop,
            # it won't do anything in the first. So let's create a variable to
            # avoid this problem.
            for regexp in exception:
                res = re.findall(regexp, oldtxt.lower())
                # Found a template! Let's skip the page!
                if res != []:
                    pywikibot.output(
                        u'Your regex has found something in %s, skipping...'
                        % page.title())
                    break
            else:
                continue
            if page.isDisambig() and disambigPage is not None:
                pywikibot.output(u'%s is a disambig page, report..'
                                 % page.title())
                if not page.title().lower() in disambigtext.lower():
                    disambigtext = u"%s\n*[[%s]]" % (disambigtext, page.title())
                    disambigpage.put(disambigtext, commentdisambig)
                    continue
            # Is the page a disambig but there's not disambigPage? Skip!
            elif page.isDisambig():
                pywikibot.output(u'%s is a disambig page, skip...'
                                 % page.title())
                continue
            else:
                # Ok, the page need the template. Let's put it there!
                # Adding the template in the text
                newtxt = u"%s\n%s" % (template, oldtxt)
                pywikibot.output(u"\t\t>>> %s <<<" % page.title())
                pywikibot.showDiff(oldtxt, newtxt)
                choice = 'y'
                if not always:
                    choice = pywikibot.inputChoice(
                        u'Orphan page found, add template?',
                        ['Yes', 'No', 'All'], 'yna')
                    if choice == 'a':
                        always = True
                        choice = 'y'
                if choice == 'y':
                    page.text = newtext
                    try:
                        page.save(comment)
                    except pywikibot.EditConflict:
                        pywikibot.output(u'Edit Conflict! Skip...')
                        continue

if __name__ == '__main__':
    main()
