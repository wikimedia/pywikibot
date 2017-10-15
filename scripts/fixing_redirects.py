#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Correct all redirect links in featured pages or only one page of each wiki.

Can be using with:
&params;

-featured         Run over featured pages (for some wikimedia wikis only)

Run fixing_redirects.py -help to see all the command-line
options -file, -ref, -links, ...

"""
#
# (C) Pywikibot team, 2004-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import re

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (SingleSiteBot, ExistingPageBot, NoRedirectPageBot,
                           AutomaticTWSummaryBot, suggest_help)
from pywikibot.textlib import does_text_contain_section
from pywikibot.tools.formatter import color_format
from pywikibot.tools import first_lower, first_upper as firstcap

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp,
}

# Featured articles categories
featured_articles = 'Q4387444'


class FixingRedirectBot(SingleSiteBot, ExistingPageBot, NoRedirectPageBot,
                        AutomaticTWSummaryBot):

    """Run over pages and resolve redirect links."""

    ignore_save_related_errors = True
    ignore_server_errors = True
    summary_key = 'fixing_redirects-fixing'

    def replace_links(self, text, linkedPage, targetPage):
        """Replace all source links by target."""
        mysite = pywikibot.Site()
        linktrail = mysite.linktrail()

        # make a backup of the original text so we can show the changes later
        linkR = re.compile(r'\[\[(?P<title>[^\]\|#]*)(?P<section>#[^\]\|]*)?'
                           r'(\|(?P<label>[^\]]*))?\]\](?P<linktrail>' + linktrail + ')')
        curpos = 0
        # This loop will run until we have finished the current page
        while True:
            m = linkR.search(text, pos=curpos)
            if not m:
                break
            # Make sure that next time around we will not find this same hit.
            curpos = m.start() + 1
            # ignore interwiki links and links to sections of the same page
            if m.group('title').strip() == '' or \
               mysite.isInterwikiLink(m.group('title')):
                continue
            else:
                actualLinkPage = pywikibot.Page(targetPage.site, m.group('title'))
                # Check whether the link found is to page.
                if actualLinkPage != linkedPage:
                    continue

            # The link looks like this:
            # [[page_title|link_text]]trailing_chars
            page_title = m.group('title')
            link_text = m.group('label')

            if not link_text:
                # or like this: [[page_title]]trailing_chars
                link_text = page_title
            if m.group('section') is None:
                section = ''
            else:
                section = m.group('section')
            if section and targetPage.section():
                pywikibot.warning(
                    'Source section {0} and target section {1} found. '
                    'Skipping.'.format(section, targetPage))
                continue
            trailing_chars = m.group('linktrail')
            if trailing_chars:
                link_text += trailing_chars

            # remove preleading ":"
            if link_text[0] == ':':
                link_text = link_text[1:]
            if link_text[0].isupper() or link_text[0].isdigit():
                new_page_title = targetPage.title()
            else:
                new_page_title = first_lower(targetPage.title())

            # remove preleading ":"
            if new_page_title[0] == ':':
                new_page_title = new_page_title[1:]

            if (new_page_title == link_text and not section):
                newlink = "[[%s]]" % new_page_title
            # check if we can create a link with trailing characters instead of a
            # pipelink
            elif (len(new_page_title) <= len(link_text) and
                  firstcap(link_text[:len(new_page_title)]) ==
                  firstcap(new_page_title) and
                  re.sub(re.compile(linktrail), '',
                         link_text[len(new_page_title):]) == '' and
                  not section):
                newlink = "[[%s]]%s" % (link_text[:len(new_page_title)],
                                        link_text[len(new_page_title):])
            else:
                newlink = "[[%s%s|%s]]" % (new_page_title, section, link_text)
            text = text[:m.start()] + newlink + text[m.end():]
            continue
        return text

    def treat_page(self):
        """Change all redirects from the current page to actual links."""
        links = self.current_page.linkedPages()
        newtext = self.current_page.text
        i = None
        for i, page in enumerate(links):
            if not page.exists():
                try:
                    target = page.moved_target()
                except (pywikibot.NoMoveTarget,
                        pywikibot.CircularRedirect,
                        pywikibot.InvalidTitle):
                    continue
            elif page.isRedirectPage():
                try:
                    target = page.getRedirectTarget()
                except (pywikibot.CircularRedirect,
                        pywikibot.InvalidTitle):
                    continue
                else:
                    section = target.section()
                    if section and not does_text_contain_section(target.text,
                                                                 section):
                        pywikibot.warning(
                            'Section #{0} not found on page {1}'.format(
                                section, target.title(asLink=True,
                                                      withSection=False)))
                        continue
            else:
                continue
            # no fix to user namespaces
            if target.namespace() in [2, 3] and page.namespace() not in [2, 3]:
                continue
            newtext = self.replace_links(newtext, page, target)

        if i is None:
            pywikibot.output('Nothing left to do.')
        else:
            self.put_current(newtext)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    featured = False
    gen = None

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-featured':
            featured = True
        elif genFactory.handleArg(arg):
            pass

    mysite = pywikibot.Site()
    if mysite.sitename == 'wikipedia:nl':
        pywikibot.output(color_format(
            '{lightred}There is consensus on the Dutch Wikipedia that '
            'bots should not be used to fix redirects.{default}'))
        return

    if featured:
        ref = mysite.page_from_repository(featured_articles)
        if ref is not None:
            gen = ref.articles(namespaces=0, content=True)
        if not gen:
            suggest_help(
                unknown_parameters=['-featured'],
                additional_text='Option is not available for this site.')
            return False
    else:
        gen = genFactory.getCombinedGenerator()
        if gen:
            gen = mysite.preloadpages(gen)
    if gen:
        bot = FixingRedirectBot(generator=gen)
        bot.run()
        return True
    else:
        suggest_help(missing_generator=True)
        return False


if __name__ == "__main__":
    main()
