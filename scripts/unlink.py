#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot unlinks a page on every page that links to it.

This script understands this command-line argument:

    -namespace:n   Number of namespace to process. The parameter can be used
                   multiple times. It works in combination with all other
                   parameters, except for the -start parameter. If you e.g.
                   want to iterate over all user pages starting at User:M, use
                   -start:User:M.

Any other parameter will be regarded as the title of the page
that should be unlinked.

Example:

python unlink.py "Foo bar" -namespace:0 -namespace:6

    Removes links to the page [[Foo bar]] in articles and image descriptions.
"""
#
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import re
import pywikibot
from pywikibot.editor import TextEditor
from pywikibot import pagegenerators, i18n, Bot


class UnlinkBot(Bot):

    def __init__(self, pageToUnlink, **kwargs):
        self.availableOptions.update({
            'namespaces': [],
            # Which namespaces should be processed?
            # default to [] which means all namespaces will be processed
        })

        super(UnlinkBot, self).__init__(**kwargs)
        self.pageToUnlink = pageToUnlink
        linktrail = self.pageToUnlink.site.linktrail()

        gen = pagegenerators.ReferringPageGenerator(pageToUnlink)
        if self.getOption('namespaces') != []:
            gen = pagegenerators.NamespaceFilterPageGenerator(gen, self.getOption('namespaces'))
        self.generator = pagegenerators.PreloadingGenerator(gen)
        # The regular expression which finds links. Results consist of four
        # groups:
        #
        # group title is the target page title, that is, everything
        # before | or ].
        #
        # group section is the page section.
        # It'll include the # to make life easier for us.
        #
        # group label is the alternative link title, that's everything
        # between | and ].
        #
        # group linktrail is the link trail, that's letters after ]] which are
        # part of the word.
        # note that the definition of 'letter' varies from language to language.
        self.linkR = re.compile(r'\[\[(?P<title>[^\]\|#]*)(?P<section>#[^\]\|]*)?(\|(?P<label>[^\]]*))?\]\](?P<linktrail>%s)'
                                % linktrail)
        self.comment = i18n.twtranslate(self.pageToUnlink.site, 'unlink-unlinking',
                                        self.pageToUnlink.title())

    def handleNextLink(self, text, match, context=100):
        """
        Returns a tuple (text, jumpToBeginning).

        text is the unicode string after the current link has been processed.
        jumpToBeginning is a boolean which specifies if the cursor position
        should be reset to 0. This is required after the user has edited the
        article.
        """
        # ignore interwiki links and links to sections of the same page as well
        # as section links
        if not match.group('title') \
           or self.pageToUnlink.site.isInterwikiLink(match.group('title')) \
           or match.group('section'):
            return text, False
        linkedPage = pywikibot.Page(self.pageToUnlink.site,
                                    match.group('title'))
        # Check whether the link found is to the current page itself.
        if linkedPage != self.pageToUnlink:
            # not a self-link
            return text, False
        else:
            # at the beginning of the link, start red color.
            # at the end of the link, reset the color to default
            if self.getOption('always'):
                choice = 'a'
            else:
                pywikibot.output(
                    text[max(0, match.start() - context):match.start()]
                    + '\03{lightred}' + text[match.start():match.end()]
                    + '\03{default}' + text[match.end():match.end() + context])
                choice = pywikibot.inputChoice(
                    u'\nWhat shall be done with this link?\n',
                    ['unlink', 'skip', 'edit', 'more context',
                     'unlink all', 'quit'],
                    ['U', 's', 'e', 'm', 'a', 'q'], 'u')
                pywikibot.output(u'')

                if choice == 's':
                    # skip this link
                    return text, False
                elif choice == 'e':
                    editor = TextEditor()
                    newText = editor.edit(text, jumpIndex=match.start())
                    # if user didn't press Cancel
                    if newText:
                        return newText, True
                    else:
                        return text, True
                elif choice == 'm':
                    # show more context by recursive self-call
                    return self.handleNextLink(text, match,
                                               context=context + 100)
                elif choice == 'a':
                    self.options['always'] = True
                elif choice == 'q':
                    self.quit()
            new = match.group('label') or match.group('title')
            new += match.group('linktrail')
            return text[:match.start()] + new + text[match.end():], False

    def treat(self, page):
        self.current_page = page
        try:
            oldText = page.get()
            text = oldText
            curpos = 0
            while curpos < len(text):
                match = self.linkR.search(text, pos=curpos)
                if not match:
                    break
                # Make sure that next time around we will not find this same
                # hit.
                curpos = match.start() + 1
                text, jumpToBeginning = self.handleNextLink(text, match)
                if jumpToBeginning:
                    curpos = 0
            if oldText == text:
                pywikibot.output(u'No changes necessary.')
            else:
                pywikibot.showDiff(oldText, text)
                page.text = text
                page.save(self.comment)
        except pywikibot.NoPage:
            pywikibot.output(u"Page %s does not exist?!"
                             % page.title(asLink=True))
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"Page %s is a redirect; skipping."
                             % page.title(asLink=True))
        except pywikibot.LockedPage:
            pywikibot.output(u"Page %s is locked?!" % page.title(asLink=True))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    # This temporary string is used to read the title
    # of the page that should be unlinked.
    page_title = None
    options = {}

    for arg in pywikibot.handle_args(args):
        if arg.startswith('-namespace:'):
            if 'namespaces' not in options:
                options['namespaces'] = []
            try:
                options['namespaces'].append(int(arg[11:]))
            except ValueError:
                options['namespaces'].append(arg[11:])
        elif arg == '-always':
            options['always'] = True
        else:
            page_title = arg

    if page_title:
        page = pywikibot.Page(pywikibot.Site(), page_title)
        bot = UnlinkBot(page, **options)
        bot.run()
    else:
        pywikibot.showHelp()

if __name__ == "__main__":
    main()
