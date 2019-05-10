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

Example
-------

1. This is a script to add a template to the top of the pages with
category:catname
Warning! Put it in one line, otherwise it won't work correctly:

    python pwb.py add_text -cat:catname -summary:"Bot: Adding a template" \
        -text:"{{Something}}" -except:"\{\{([Tt]emplate:|)[Ss]omething" -up

2. Command used on it.wikipedia to put the template in the page without any
category.
Warning! Put it in one line, otherwise it won't work correctly:

    python pwb.py add_text -except:"\{\{([Tt]emplate:|)[Cc]ategorizzare" \
        -text:"{{Categorizzare}}" -excepturl:"class='catlinks'>" -uncat \
        -summary:"Bot: Aggiungo template Categorizzare"
"""

#
# (C) Filnik, 2007-2010
# (C) Pywikibot team, 2007-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import codecs
import re
import sys

import pywikibot

from pywikibot import config, i18n, pagegenerators, textlib
from pywikibot.bot_choice import QuitKeyboardInterrupt
from pywikibot.tools.formatter import color_format

docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


def get_text(page, old, create):
    """Get the old text."""
    if old is None:
        try:
            text = page.get()
        except pywikibot.NoPage:
            if create:
                pywikibot.output(
                    "{} doesn't exist, creating it!".format(page.title()))
                text = ''
            else:
                pywikibot.output(
                    "{} doesn't exist, skip!".format(page.title()))
                return None
        except pywikibot.IsRedirectPage:
            pywikibot.output('{} is a redirect, skip!'.format(page.title()))
            return None
    else:
        text = old
    return text


def put_text(page, new, summary, count, asynchronous=False):
    """Save the new text."""
    page.text = new
    try:
        page.save(summary=summary, asynchronous=asynchronous,
                  minor=page.namespace() != 3)
    except pywikibot.EditConflict:
        pywikibot.output('Edit conflict! skip!')
    except pywikibot.ServerError:
        if count <= config.max_retries:
            pywikibot.output('Server Error! Wait..')
            pywikibot.sleep(config.retry_wait)
            return None
        else:
            raise pywikibot.ServerError(
                'Server Error! Maximum retries exceeded')
    except pywikibot.SpamfilterError as e:
        pywikibot.output(
            'Cannot change {} because of blacklist entry {}'
            .format(page.title(), e.url))
    except pywikibot.LockedPage:
        pywikibot.output('Skipping {} (locked page)'.format(page.title()))
    except pywikibot.PageNotSaved as error:
        pywikibot.output('Error putting page: {}'.format(error.args))
    else:
        return True
    return False


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
    if putText:
        pywikibot.output('Loading {}...'.format(page.title()))

    text = get_text(page, oldTextGiven, create)
    if text is None:
        return (False, False, always)

    # Understand if the bot has to skip the page or not
    # In this way you can use both -except and -excepturl
    if regexSkipUrl is not None:
        url = page.full_url()
        result = re.findall(regexSkipUrl, site.getUrl(url))
        if result != []:
            pywikibot.output(
                'Exception! regex (or word) used with -exceptUrl '
                'is in the page. Skip!\n'
                'Match was: {}'.format(result))
            return (False, False, always)
    if regexSkip is not None:
        result = re.findall(regexSkip, text)
        if result != []:
            pywikibot.output(
                'Exception! regex (or word) used with -except '
                'is in the page. Skip!\n'
                'Match was: {}'.format(result))
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
            newtext += '{}{}'.format(config.line_separator, addText)
            # Reputting the categories
            newtext = textlib.replaceCategoryLinks(newtext,
                                                   categoriesInside, site,
                                                   True)
            # Adding the interwiki
            newtext = textlib.replaceLanguageLinks(newtext, interwikiInside,
                                                   site)
        else:
            newtext += '{}{}'.format(config.line_separator, addText)
    else:
        newtext = addText + config.line_separator + text

    if putText and text != newtext:
        pywikibot.output(color_format(
            '\n\n>>> {lightpurple}{0}{default} <<<', page.title()))
        pywikibot.showDiff(text, newtext)

    # Let's put the changes.
    error_count = 0
    while True:
        # If someone load it as module, maybe it's not so useful to put the
        # text in the page
        if not putText:
            return (text, newtext, always)

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
            result = put_text(page, newtext, summary, error_count,
                              asynchronous=not always)
            if result is not None:
                return (result, result, always)
            error_count += 1


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: str
    """
    # If none, the var is set only for check purpose.
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


if __name__ == '__main__':
    main()
