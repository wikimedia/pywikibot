#!/usr/bin/python
r"""
This is a Bot to add text to the top or bottom of a page.

By default this adds the text to the bottom above the categories and interwiki.

These command line parameters can be used to specify which pages to work on:

&params;

Furthermore, the following command line parameters are supported:

-talkpage         Put the text onto the talk page instead
-talk

-text             Define what text to add. "\n" are interpreted as newlines.

-textfile         Define a texfile name which contains the text to add

-summary          Define the summary to use

-excepturl        Use the html page as text where you want to see if there's
                  the text, not the wiki-page.

-newimages        Add text in the new images

-always           If used, the bot won't ask if it should add the specified
                  text

-up               If used, put the text at the top of the page

-noreorder        Avoid reordering cats and interwiki

Example
-------

1. Append 'hello world' to the bottom of the sandbox:

    python pwb.py add_text -page:Wikipedia:Sandbox \
        -summary:"Bot: pywikibot practice" -text:"hello world"

2. Add a template to the top of the pages with 'category:catname':

    python pwb.py add_text -cat:catname -summary:"Bot: Adding a template" \
        -text:"{{Something}}" -except:"\{\{([Tt]emplate:|)[Ss]omething" -up

3. Command used on it.wikipedia to put the template in the page without any
   category:

    python pwb.py add_text -except:"\{\{([Tt]emplate:|)[Cc]ategorizzare" \
        -text:"{{Categorizzare}}" -excepturl:"class='catlinks'>" -uncat \
        -summary:"Bot: Aggiungo template Categorizzare"
"""
#
# (C) Pywikibot team, 2007-2021
#
# Distributed under the terms of the MIT license.
#
import codecs
import re
import sys
from typing import Optional, Union

import pywikibot
from pywikibot import config, i18n, pagegenerators, textlib
from pywikibot.backports import Tuple
from pywikibot.bot_choice import QuitKeyboardInterrupt
from pywikibot.exceptions import (
    ArgumentDeprecationWarning,
    EditConflictError,
    IsRedirectPageError,
    LockedPageError,
    NoPageError,
    PageSaveRelatedError,
    ServerError,
    SpamblacklistError,
)
from pywikibot.tools import issue_deprecation_warning
from pywikibot.tools.formatter import color_format


docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816


def get_text(page: pywikibot.page.BasePage, old: Optional[str],
             create: bool) -> str:
    """
    Get text on page. If old is not None, return old.

    @param page: The page to get text from
    @param old: If not None, return this rather than the page's text
    @param create: Declare that the page will be created if it doesn't exist
    @return: The page's text or the old parameter if not None
    """
    if old is not None:
        return old

    try:
        return page.get()
    except NoPageError:
        if create:
            pywikibot.output("{} doesn't exist, creating it!"
                             .format(page.title()))
            return ''
        else:
            pywikibot.output("{} doesn't exist, skip!".format(page.title()))
            return None
    except IsRedirectPageError:
        pywikibot.output('{} is a redirect, skip!'.format(page.title()))
        return None


def put_text(page: pywikibot.page.BasePage, new: str, summary: str, count: int,
             asynchronous: bool = False) -> Optional[bool]:
    """
    Save the new text.

    @param page: The page to change the text of
    @param new: The new text for the page
    @param summary: Summary of the page change
    @param count: Maximum number of attempts to reach the server
    @param asynchronous: If True, saves the page asynchronously
    @return: True if successful, False if unsuccessful, and None if
        awaiting the server
    """
    page.text = new
    try:
        page.save(summary=summary, asynchronous=asynchronous,
                  minor=page.namespace() != 3)
    except EditConflictError:
        pywikibot.output('Edit conflict! skip!')
    except ServerError:
        if count <= config.max_retries:
            pywikibot.output('Server Error! Wait..')
            pywikibot.sleep(config.retry_wait)
            return None
        raise ServerError(
            'Server Error! Maximum retries exceeded')
    except SpamblacklistError as e:
        pywikibot.output(
            'Cannot change {} because of blacklist entry {}'
            .format(page.title(), e.url))
    except LockedPageError:
        pywikibot.output('Skipping {} (locked page)'.format(page.title()))
    except PageSaveRelatedError as error:
        pywikibot.output('Error putting page: {}'.format(error.args))
    else:
        return True
    return False


def add_text(page: pywikibot.page.BasePage, addText: str,
             summary: Optional[str] = None,
             regexSkip: Optional[str] = None,
             regexSkipUrl: Optional[str] = None,
             always: bool = False, up: bool = False,
             putText: bool = True, oldTextGiven: Optional[str] = None,
             reorderEnabled: bool = True, create: bool = False
             ) -> Union[Tuple[bool, bool, bool], Tuple[str, str, bool]]:
    """
    Add text to a page.

    @param page: The page to add text to
    @param addText: Text to add
    @param summary: Change summary, if None this uses the beginning of addText
    @param regexSkip: Abort if the text on the page matches this
    @param regexSkipUrl: Abort if the url matches this
    @param always: Edit without user confirmation
    @param up: Append text to the top of the page if True, otherwise the
        bottom
    @param putText: Save changes to the page if True, otherwise return
        (text, newtext, always)
    @param oldTextGiven: If None fetch page text, else use this text
    @param reorderEnabled: If True place text above categories and
        interwiki, else place at page bottom. No effect if up = False.
    @param create: Create the page if it does not exist
    @return: (success, success, always) if putText is True, otherwise
        (text, newtext, always)
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
        addText = addText.replace('\\n', '\n')
        if reorderEnabled:
            # Getting the categories
            categoriesInside = textlib.getCategoryLinks(newtext, site)
            # Deleting the categories
            newtext = textlib.removeCategoryLinks(newtext, site)
            # Getting the interwiki
            interwikiInside = textlib.getLanguageLinks(newtext, site)
            # Removing the interwiki
            newtext = textlib.removeLanguageLinks(newtext, site)

            # Adding the text
            newtext += '\n' + addText
            # Reputting the categories
            newtext = textlib.replaceCategoryLinks(newtext,
                                                   categoriesInside, site,
                                                   True)
            # Adding the interwiki
            newtext = textlib.replaceLanguageLinks(newtext, interwikiInside,
                                                   site)
        else:
            newtext += '\n' + addText
    else:
        newtext = addText + '\n' + text

    if not putText:
        # If someone load it as module, maybe it's not so useful to put the
        # text in the page
        return (text, newtext, always)

    if text != newtext:
        pywikibot.output(color_format(
            '\n\n>>> {lightpurple}{0}{default} <<<', page.title()))
        pywikibot.showDiff(text, newtext)

    # Let's put the changes.
    error_count = 0
    while True:
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
                continue

        # either always or choice == 'y' is selected
        result = put_text(page, newtext, summary, error_count,
                          asynchronous=not always)
        if result is not None:
            return (result, result, always)
        error_count += 1


def main(*args: Tuple[str, ...]) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: Command line arguments
    """
    # If none, the var is set only for check purpose.
    summary = None
    addText = None
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
            new_arg = ''.join(['-grepnot', sep, value])
            issue_deprecation_warning(arg, new_arg,
                                      2, ArgumentDeprecationWarning,
                                      since='20201224')
            genFactory.handle_arg(new_arg)
        elif option == '-up':
            up = True
        elif option == '-noreorder':
            reorderEnabled = False
        elif option == '-always':
            always = True
        elif option in ('-talk', '-talkpage'):
            talkPage = True
        else:
            genFactory.handle_arg(arg)

    if textfile and not addText:
        with codecs.open(textfile, 'r', config.textfile_encoding) as f:
            addText = f.read()

    generator = genFactory.getCombinedGenerator()
    additional_text = '' if addText else "The text to add wasn't given."
    if pywikibot.bot.suggest_help(missing_generator=not generator,
                                  additional_text=additional_text):
        return

    if talkPage:
        generator = pagegenerators.PageWithTalkPageGenerator(generator, True)
    for page in generator:
        add_text(page, addText, summary,
                 regexSkipUrl=regexSkipUrl, always=always, up=up,
                 reorderEnabled=reorderEnabled, create=talkPage)


if __name__ == '__main__':
    main()
