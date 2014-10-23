#!/usr/bin/python
# -*- coding: utf-8  -*-

"""
This bot searches for selflinks and allows removing them.

These command line parameters can be used to specify which pages to work on:

&params;

-always           Unlink always but don't prompt you for each replacement.
                  ATTENTION: Use this with care!
"""
#
# (C) Pywikibot team, 2006-2014
#
# Distributed under the terms of the MIT license.
#

import re
import pywikibot
from pywikibot import i18n, Bot
from pywikibot.editor import TextEditor
from pywikibot.pagegenerators import GeneratorFactory, PreloadingGenerator, \
    parameterHelp

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': parameterHelp,
}


class SelflinkBot(Bot):

    """Self-link removal bot."""

    def __init__(self, generator, **kwargs):
        super(SelflinkBot, self).__init__(**kwargs)
        self.generator = generator
        linktrail = pywikibot.Site().linktrail()
        # The regular expression which finds links. Results consist of four
        # groups:
        # group title is the target page title, everything before | or ].
        # group section is the page section. It'll include the # to make life
        # easier for us.
        # group label is the alternative link title, that's everything between
        # | and ].
        # group linktrail is the link trail, that's letters after ]] which are
        # part of the word.
        # note that the definition of 'letter' varies from language to
        # language.
        self.linkR = re.compile(
            r'\[\[(?P<title>[^\]\|#]*)'
            r'(?P<section>#[^\]\|]*)?'
            '(\|(?P<label>[^\]]*))?\]\]'
            r'(?P<linktrail>' + linktrail + ')')

    def handleNextLink(self, page, match, context=100):
        """Process the next link on a page, offering the user choices.

        @param page: The page being edited
        @type page: pywikibot.Page
        @param match: The match object for the current link.
        @type match: re.MatchObject
        @param context: The amount of context around the link shown to the user
        @type context: int
        @return: jumpToBeginning, a boolean, which specifies if the cursor
        position should be reset to 0. This is required after the user has
        edited the article.
        """
        # ignore interwiki links and links to sections of the same page as well
        # as section links
        if not match.group('title') \
           or page.site.isInterwikiLink(match.group('title')) \
           or match.group('section'):
            return False
        try:
            linkedPage = pywikibot.Page(page.site, title=match.group('title'))
        except pywikibot.InvalidTitle as err:
            pywikibot.warning(u'%s' % err)
            return False

        # Check whether the link found is to the current page itself.
        if linkedPage != page:
            # not a self-link, nothing to do
            return False

        # at the beginning of the link, start red color.
        # at the end of the link, reset the color to default
        if self.getOption('always'):
            choice = 'a'
        else:
            pre = page.text[max(0, match.start() - context):match.start()]
            post = page.text[match.end():match.end() + context]
            matchText = match.group(0)
            pywikibot.output(
                pre + '\03{lightred}' + matchText + '\03{default}' + post)
            choice = pywikibot.input_choice(
                u'\nWhat shall be done with this selflink?\n',
                [('unlink', 'u'), ('make bold', 'b'), ('skip', 's'),
                 ('edit', 'e'), ('more context', 'm'), ('unlink all')], 'u')
            pywikibot.output(u'')

            if choice == 's':
                # skip this link
                return False
            elif choice == 'e':
                editor = TextEditor()
                newText = editor.edit(page.text, jumpIndex=match.start())
                # if user didn't press Cancel
                if newText:
                    page.text = newText
                    return True
                else:
                    return True
            elif choice == 'm':
                # show more context by recursive self-call
                return self.handleNextLink(page, match, context=context + 100)
            elif choice == 'a':
                self.always = True

        # choice was 'U', 'b', or 'a'
        new = match.group('label') or match.group('title')
        new += match.group('linktrail')
        preMatch = page.text[:match.start()]
        postMatch = page.text[match.end():]
        if choice == 'b':
            # make bold
            page.text = preMatch + "'''" + new + "'''" + postMatch
            return False
        else:
            page.text = preMatch + new + postMatch
            return False

    def treat(self, page):
        self.current_page = page
        try:
            oldText = page.text
            # Inside image maps, don't touch selflinks, as they're used
            # to create tooltip labels. See for example:
            # https://de.wikipedia.org/w/index.php?diff=next&oldid=35721641
            if '<imagemap>' in page.text:
                pywikibot.output(
                    u'Skipping page %s because it contains an image map.'
                    % page.title(asLink=True))
                return
            curpos = 0
            while curpos < len(page.text):
                match = self.linkR.search(page.text, pos=curpos)
                if not match:
                    break
                # Make sure that next time around we will not find this same
                # hit.
                curpos = match.start() + 1
                jumpToBeginning = self.handleNextLink(page, match)
                if jumpToBeginning:
                    curpos = 0

            if oldText == page.text:
                pywikibot.output(u'No changes necessary.')
            else:
                pywikibot.showDiff(oldText, page.text)
                comment = i18n.twtranslate(page.site, "selflink-remove")
                page.save(async=True, comment=comment)
        except pywikibot.NoPage:
            pywikibot.output(u"Page %s does not exist."
                             % page.title(asLink=True))
        except pywikibot.IsRedirectPage:
            pywikibot.output(u"Page %s is a redirect; skipping."
                             % page.title(asLink=True))
        except pywikibot.LockedPage:
            pywikibot.output(u"Page %s is locked." % page.title(asLink=True))


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    # Page generator
    gen = None
    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = GeneratorFactory()
    botArgs = {}

    for arg in local_args:
        if arg == '-always':
            botArgs['always'] = True
        else:
            genFactory.handleArg(arg)

    gen = genFactory.getCombinedGenerator()
    if not gen:
        pywikibot.showHelp()
        return

    preloadingGen = PreloadingGenerator(gen)
    bot = SelflinkBot(preloadingGen, **botArgs)
    bot.run()

if __name__ == "__main__":
    main()
