#!/usr/bin/python
# -*- coding: utf-8 -*-
r"""
This is a Bot to add a text at the end of the content of the page.

By default it adds the text above categories and interwiki.

Alternatively it may also add a text at the top of the page.
These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-talkpage         Put the text onto the talk page instead the generated on
-talk

-text             Define which text to add. "\n" are interpreted as newlines.

-textfile         Define a texfile name which contains the text to add

-summary          Define the summary to use

-except           Use a regex to check if the text is already in the page

-excepturl        Use the html page as text where you want to see if there's
                  the text, not the wiki-page.

-newimages        Add text in the new images

-always           If used, the bot won't ask if it should add the text
                  specified

-up               If used, put the text at the top of the page

-noreorder        Avoid to reorder cats and interwiki

--- Example ---
1.
# This is a script to add a template to the top of the pages with
# category:catname
# Warning! Put it in one line, otherwise it won't work correctly.

    python pwb.py add_text -cat:catname -summary:"Bot: Adding a template" \
        -text:"{{Something}}" -except:"\{\{([Tt]emplate:|)[Ss]omething" -up

2.
# Command used on it.wikipedia to put the template in the page without any
# category.
# Warning! Put it in one line, otherwise it won't work correctly.

    python pwb.py add_text -except:"\{\{([Tt]emplate:|)[Cc]ategorizzare" \
        -text:"{{Categorizzare}}" -excepturl:"class='catlinks'>" -uncat \
        -summary:"Bot: Aggiungo template Categorizzare"
"""

#
# (C) Filnik, 2007-2010
# (C) Pywikibot team, 2007-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import codecs
import re
import sys
import time

import pywikibot

from pywikibot import config, i18n, pagegenerators, textlib
from pywikibot.bot_choice import QuitKeyboardInterrupt
from pywikibot.tools.formatter import color_format

docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}


def add_text(page, addText, summary=None, regexSkip=None,
             regexSkipUrl=None, always=False, up=False, putText=True,
             oldTextGiven=None, reorderEnabled=True, create=False):
    """
    Add text to a page.

    @rtype: tuple of (text, newtext, always)
    """
    site = page.site
    if not summary:
        summary = i18n.twtranslate(site, 'add_text-adding',
                                   {'adding': addText[:200]})

    errorCount = 0

    if putText:
        pywikibot.output(u'Loading %s...' % page.title())
    if oldTextGiven is None:
        try:
            text = page.get()
        except pywikibot.NoPage:
            if create:
                pywikibot.output(u"%s doesn't exist, creating it!"
                                 % page.title())
                text = u''
            else:
                pywikibot.output(u"%s doesn't exist, skip!" % page.title())
                return (False, False, always)
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"%s is a redirect, skip!" % page.title())
            return (False, False, always)
    else:
        text = oldTextGiven
    # Understand if the bot has to skip the page or not
    # In this way you can use both -except and -excepturl
    if regexSkipUrl is not None:
        url = page.full_url()
        result = re.findall(regexSkipUrl, site.getUrl(url))
        if result != []:
            pywikibot.output(
                'Exception! regex (or word) used with -exceptUrl '
                'is in the page. Skip!\n'
                'Match was: %s' % result)
            return (False, False, always)
    if regexSkip is not None:
        result = re.findall(regexSkip, text)
        if result != []:
            pywikibot.output(
                'Exception! regex (or word) used with -except '
                'is in the page. Skip!\n'
                'Match was: %s' % result)
            return (False, False, always)
    # If not up, text put below
    if not up:
        newtext = text
        # Translating the \\n into binary \n
        addText = addText.replace('\\n', config.line_separator)
        if (reorderEnabled):
            # Getting the categories
            categoriesInside = textlib.getCategoryLinks(newtext, site)
            # Deleting the categories
            newtext = textlib.removeCategoryLinks(newtext, site)
            # Getting the interwiki
            interwikiInside = textlib.getLanguageLinks(newtext, site)
            # Removing the interwiki
            newtext = textlib.removeLanguageLinks(newtext, site)

            # Adding the text
            newtext += u"%s%s" % (config.line_separator, addText)
            # Reputting the categories
            newtext = textlib.replaceCategoryLinks(newtext,
                                                   categoriesInside, site,
                                                   True)
            # Adding the interwiki
            newtext = textlib.replaceLanguageLinks(newtext, interwikiInside,
                                                   site)
        else:
            newtext += u"%s%s" % (config.line_separator, addText)
    else:
        newtext = addText + config.line_separator + text
    if putText and text != newtext:
        pywikibot.output(color_format(
            '\n\n>>> {lightpurple}{0}{default} <<<', page.title()))
        pywikibot.showDiff(text, newtext)
    # Let's put the changes.
    while True:
        # If someone load it as module, maybe it's not so useful to put the
        # text in the page
        if putText:
            if not always:
                try:
                    choice = pywikibot.input_choice(
                        'Do you want to accept these changes?',
                        [('Yes', 'y'), ('No', 'n'), ('All', 'a'),
                         ('open in Browser', 'b')], 'n')
                except QuitKeyboardInterrupt:
                    sys.exit('User quit bot run.')
                if choice == 'a':
                    always = True
                elif choice == 'n':
                    return (False, False, always)
                elif choice == 'b':
                    pywikibot.bot.open_webbrowser(page)
            if always or choice == 'y':
                try:
                    if always:
                        page.put(newtext, summary,
                                 minorEdit=page.namespace() != 3)
                    else:
                        page.put_async(newtext, summary,
                                       minorEdit=page.namespace() != 3)
                except pywikibot.EditConflict:
                    pywikibot.output(u'Edit conflict! skip!')
                    return (False, False, always)
                except pywikibot.ServerError:
                    errorCount += 1
                    if errorCount < config.max_retries:
                        pywikibot.output(u'Server Error! Wait..')
                        time.sleep(config.retry_wait)
                        continue
                    else:
                        raise pywikibot.ServerError(u'Fifth Server Error!')
                except pywikibot.SpamfilterError as e:
                    pywikibot.output(
                        u'Cannot change %s because of blacklist entry %s'
                        % (page.title(), e.url))
                    return (False, False, always)
                except pywikibot.LockedPage:
                    pywikibot.output(u'Skipping %s (locked page)'
                                     % page.title())
                    return (False, False, always)
                except pywikibot.PageNotSaved as error:
                    pywikibot.output(u'Error putting page: %s' % error.args)
                    return (False, False, always)
                else:
                    # Break only if the errors are one after the other...
                    errorCount = 0
                    return (True, True, always)
        else:
            return (text, newtext, always)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    # If none, the var is setted only for check purpose.
    summary = None
    addText = None
    regexSkip = None
    regexSkipUrl = None
    always = False
    textfile = None
    talkPage = False
    reorderEnabled = True

    # Put the text above or below the text?
    up = False

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    # Loading the arguments
    for arg in local_args:
        option, sep, value = arg.partition(':')
        if option == '-textfile':
            textfile = value or pywikibot.input(
                'Which textfile do you want to add?')
        elif option == '-text':
            addText = value or pywikibot.input('What text do you want to add?')
        elif option == '-summary':
            summary = value or pywikibot.input(
                'What summary do you want to use?')
        elif option == '-excepturl':
            regexSkipUrl = value or pywikibot.input('What text should I skip?')
        elif option == '-except':
            regexSkip = value or pywikibot.input('What text should I skip?')
        elif option == '-up':
            up = True
        elif option == '-noreorder':
            reorderEnabled = False
        elif option == '-always':
            always = True
        elif option in ('-talk', '-talkpage'):
            talkPage = True
        else:
            genFactory.handleArg(arg)

    if textfile and not addText:
        with codecs.open(textfile, 'r', config.textfile_encoding) as f:
            addText = f.read()
    generator = genFactory.getCombinedGenerator()
    if not generator:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False
    if not addText:
        pywikibot.error("The text to add wasn't given.")
        return
    if talkPage:
        generator = pagegenerators.PageWithTalkPageGenerator(generator, True)
    for page in generator:
        (text, newtext, always) = add_text(page, addText, summary, regexSkip,
                                           regexSkipUrl, always, up, True,
                                           reorderEnabled=reorderEnabled,
                                           create=talkPage)


if __name__ == "__main__":
    main()
