#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
This is a Bot written by Filnik to add a text at the end of the page but above
categories, interwiki and template for the stars of the interwiki (default).

Alternatively it may also add a text at the top of the page.
These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-page             Use a page as generator

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

python add_text.py -cat:catname -summary:"Bot: Adding a template"
-text:"{{Something}}" -except:"\{\{([Tt]emplate:|)[Ss]omething" -up

2.
# Command used on it.wikipedia to put the template in the page without any
# category.
# Warning! Put it in one line, otherwise it won't work correctly.

python add_text.py -excepturl:"class='catlinks'>" -uncat
-text:"{{Categorizzare}}" -except:"\{\{([Tt]emplate:|)[Cc]ategorizzare"
-summary:"Bot: Aggiungo template Categorizzare"

--- Credits and Help ---
This script has been written by Botwiki's staff, if you want to help us
or you need some help regarding this script, you can find us here:

* http://botwiki.sno.cc/wiki/Main_Page

"""

#
# (C) Filnik, 2007-2010
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import re
import webbrowser
import codecs
import time

import pywikibot
from pywikibot import config, i18n, pagegenerators, textlib

docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}


starsList = [
    u'bueno',
    u'bom interwiki',
    u'cyswllt[ _]erthygl[ _]ddethol', u'dolen[ _]ed',
    u'destacado', u'destaca[tu]',
    u'enllaç[ _]ad',
    u'enllaz[ _]ad',
    u'leam[ _]vdc',
    u'legătură[ _]a[bcf]',
    u'liamm[ _]pub',
    u'lien[ _]adq',
    u'lien[ _]ba',
    u'liên[ _]kết[ _]bài[ _]chất[ _]lượng[ _]tốt',
    u'liên[ _]kết[ _]chọn[ _]lọc',
    u'ligam[ _]adq',
    u'ligazón[ _]a[bd]',
    u'ligoelstara',
    u'ligoleginda',
    u'link[ _][afgu]a', u'link[ _]adq', u'link[ _]f[lm]', u'link[ _]km',
    u'link[ _]sm', u'linkfa',
    u'na[ _]lotura',
    u'nasc[ _]ar',
    u'tengill[ _][úg]g',
    u'ua',
    u'yüm yg',
    u'רא',
    u'وصلة مقالة جيدة',
    u'وصلة مقالة مختارة',
]


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

    # When a page is tagged as "really well written" it has a star in the
    # interwiki links. This is a list of all the templates used (in regex
    # format) to make the stars appear.

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
        url = site.nice_get_address(page.title(asUrl=True))
        result = re.findall(regexSkipUrl, site.getUrl(url))
        if result != []:
            pywikibot.output(
u'''Exception! regex (or word) used with -exceptUrl is in the page. Skip!
Match was: %s''' % result)
            return (False, False, always)
    if regexSkip is not None:
        result = re.findall(regexSkip, text)
        if result != []:
            pywikibot.output(
u'''Exception! regex (or word) used with -except is in the page. Skip!
Match was: %s''' % result)
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
            # Dealing the stars' issue
            allstars = []
            starstext = textlib.removeDisabledParts(text)
            for star in starsList:
                regex = re.compile('(\{\{(?:template:|)%s\|.*?\}\}[\s]*)'
                                   % star, re.I)
                found = regex.findall(starstext)
                if found != []:
                    newtext = regex.sub('', newtext)
                    allstars += found
            if allstars != []:
                newtext = newtext.strip() + config.line_separator * 2
                allstars.sort()
                for element in allstars:
                    newtext += '%s%s' % (element.strip(), config.LS)
            # Adding the interwiki
            newtext = textlib.replaceLanguageLinks(newtext, interwikiInside,
                                                   site)
        else:
            newtext += u"%s%s" % (config.line_separator, addText)
    else:
        newtext = addText + config.line_separator + text
    if putText and text != newtext:
        pywikibot.output(u"\n\n>>> \03{lightpurple}%s\03{default} <<<"
                         % page.title())
        pywikibot.showDiff(text, newtext)
    # Let's put the changes.
    while True:
        # If someone load it as module, maybe it's not so useful to put the
        # text in the page
        if putText:
            if not always:
                choice = pywikibot.inputChoice(
                    u'Do you want to accept these changes?',
                    ['Yes', 'No', 'All', 'open in Browser'],
                    ['y', 'n', 'a', 'b'], 'n')
                if choice == 'a':
                    always = True
                elif choice == 'n':
                    return (False, False, always)
                elif choice == 'b':
                    webbrowser.open("http://%s%s" % (
                        site.hostname(),
                        site.nice_get_address(page.title(asUrl=True))
                    ))
                    pywikibot.input("Press Enter when finished in browser.")
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
                except pywikibot.PageNotSaved as error:
                    pywikibot.output(u'Error putting page: %s' % error.args)
                    return (False, False, always)
                except pywikibot.LockedPage:
                    pywikibot.output(u'Skipping %s (locked page)'
                                     % page.title())
                    return (False, False, always)
                else:
                    # Break only if the errors are one after the other...
                    errorCount = 0
                    return (True, True, always)
        else:
            return (text, newtext, always)


def main():
    # If none, the var is setted only for check purpose.
    summary = None
    addText = None
    regexSkip = None
    regexSkipUrl = None
    generator = None
    always = False
    textfile = None
    talkPage = False
    reorderEnabled = True
    namespaces = []

    # Put the text above or below the text?
    up = False

    # Process global args and prepare generator args parser
    local_args = pywikibot.handleArgs()
    genFactory = pagegenerators.GeneratorFactory()

    # Loading the arguments
    for arg in local_args:
        if arg.startswith('-textfile'):
            if len(arg) == 9:
                textfile = pywikibot.input(
                    u'Which textfile do you want to add?')
            else:
                textfile = arg[10:]
        elif arg.startswith('-text'):
            if len(arg) == 5:
                addText = pywikibot.input(u'What text do you want to add?')
            else:
                addText = arg[6:]
        elif arg.startswith('-summary'):
            if len(arg) == 8:
                summary = pywikibot.input(u'What summary do you want to use?')
            else:
                summary = arg[9:]
        elif arg.startswith('-page'):
            if len(arg) == 5:
                generator = [pywikibot.Page(
                    pywikibot.Site(),
                    pywikibot.input(u'What page do you want to use?'))]
            else:
                generator = [pywikibot.Page(pywikibot.Site(), arg[6:])]
        elif arg.startswith('-excepturl'):
            if len(arg) == 10:
                regexSkipUrl = pywikibot.input(u'What text should I skip?')
            else:
                regexSkipUrl = arg[11:]
        elif arg.startswith('-except'):
            if len(arg) == 7:
                regexSkip = pywikibot.input(u'What text should I skip?')
            else:
                regexSkip = arg[8:]
        elif arg == '-up':
            up = True
        elif arg == '-noreorder':
            reorderEnabled = False
        elif arg == '-always':
            always = True
        elif arg == '-talk' or arg == '-talkpage':
            talkPage = True
        else:
            genFactory.handleArg(arg)
    if textfile and not addText:
        with codecs.open(textfile, 'r', config.textfile_encoding) as f:
            addText = f.read()
    if not generator:
        generator = genFactory.getCombinedGenerator()
    if not generator:
        pywikibot.showHelp()
        return
    if not addText:
        pywikibot.error("The text to add wasn't given.")
        return
    if talkPage:
        generator = pagegenerators.PageWithTalkPageGenerator(generator)
        site = pywikibot.Site()
        for namespace in site.namespaces():
            index = site.getNamespaceIndex(namespace)
            if index % 2 == 1 and index > 0:
                namespaces += [index]
        generator = pagegenerators.NamespaceFilterPageGenerator(
            generator, namespaces)
    for page in generator:
        (text, newtext, always) = add_text(page, addText, summary, regexSkip,
                                           regexSkipUrl, always, up, True,
                                           reorderEnabled=reorderEnabled,
                                           create=talkPage)

if __name__ == "__main__":
    main()
