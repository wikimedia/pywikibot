#!/usr/bin/env python3
"""
Correct all redirect links in featured pages or only one page of each wiki.

Can be used with:

-always           The bot won't ask for confirmation when putting a page

-featured         Run over featured pages (for some Wikimedia wikis only)

-overwrite        Usually only the link is changed ([[Foo]] -> [[Bar|Foo]]).
                  This parameters sets the script to completly overwrite the
                  link text ([[Foo]] -> [[Bar]]).

-ignoremoves      Do not try to solve deleted pages after page move.

&params;
"""
#
# (C) Pywikibot team, 2004-2022
#
# Distributed under the terms of the MIT license.
#
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import suppress

import pywikibot
from pywikibot import pagegenerators
from pywikibot.bot import (
    AutomaticTWSummaryBot,
    ExistingPageBot,
    SingleSiteBot,
    suggest_help,
)
from pywikibot.exceptions import (
    CircularRedirectError,
    InterwikiRedirectPageError,
    InvalidPageError,
    InvalidTitleError,
    NoMoveTargetError,
)
from pywikibot.textlib import does_text_contain_section, isDisabled
from pywikibot.tools import first_lower
from pywikibot.tools import first_upper as firstcap


# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

# Featured articles categories
FEATURED_ARTICLES = 'Q4387444'


class FixingRedirectBot(SingleSiteBot, ExistingPageBot, AutomaticTWSummaryBot):

    """Run over pages and resolve redirect links."""

    use_redirects = False
    ignore_save_related_errors = True
    ignore_server_errors = True
    summary_key = 'fixing_redirects-fixing'
    update_options = {
        'overwrite': False,
        'ignoremoves': False,
    }

    def replace_links(self, text, linked_page, target_page):
        """Replace all source links by target."""
        mysite = pywikibot.Site()
        linktrail = mysite.linktrail()

        # make a backup of the original text so we can show the changes later
        link_regex = re.compile(
            r'\[\[(?P<title>[^\]\|#]*)(?P<section>#[^\]\|]*)?'
            r'(\|(?P<label>[^\]]*))?\]\](?P<linktrail>' + linktrail + ')')
        curpos = 0
        # This loop will run until we have finished the current page
        while True:
            m = link_regex.search(text, pos=curpos)
            if not m:
                break
            # Make sure that next time around we will not find this same hit.
            curpos = m.start() + 1

            try:
                is_interwikilink = mysite.isInterwikiLink(m['title'])
            except InvalidTitleError:
                continue  # skip invalid title

            # ignore interwiki links, links in the disabled area
            # and links to sections of the same page
            if (m['title'].strip() == ''
                    or is_interwikilink
                    or isDisabled(text, m.start())):
                continue
            actual_link_page = pywikibot.Page(target_page.site, m['title'])
            # Check whether the link found is to page.
            try:
                actual_link_page.title()
            except InvalidTitleError as e:
                pywikibot.error(e)
                continue
            if actual_link_page != linked_page:
                continue

            # The link looks like this:
            # [[page_title|link_text]]trailing_chars
            page_title = m['title']
            link_text = m['label']

            if not link_text:
                # or like this: [[page_title]]trailing_chars
                link_text = page_title
            if m['section'] is None:
                section = ''
            else:
                section = m['section']
            if section and target_page.section():
                pywikibot.warning(
                    'Source section {} and target section {} found. '
                    'Skipping.'.format(section, target_page))
                continue
            trailing_chars = m['linktrail']
            if trailing_chars:
                link_text += trailing_chars

            # remove preleading ":"
            if link_text[0] == ':':
                link_text = link_text[1:]
            if link_text[0].isupper() or link_text[0].isdigit():
                new_page_title = target_page.title()
            else:
                new_page_title = first_lower(target_page.title())

            # remove preleading ":"
            if new_page_title[0] == ':':
                new_page_title = new_page_title[1:]

            if ((new_page_title == link_text and not section)
                    or self.opt.overwrite):
                newlink = f'[[{new_page_title}]]'
            # check if we can create a link with trailing characters instead of
            # a pipelink
            elif (len(new_page_title) <= len(link_text)
                  and (firstcap(link_text[:len(new_page_title)])
                       == firstcap(new_page_title))
                  and re.sub(re.compile(linktrail), '',
                             link_text[len(new_page_title):]) == ''
                  and not section):
                newlink = '[[{}]]{}'.format(link_text[:len(new_page_title)],
                                            link_text[len(new_page_title):])
            else:
                newlink = '[[{}{}|{}]]'.format(new_page_title,
                                               section, link_text)
            text = text[:m.start()] + newlink + text[m.end():]
            continue
        return text

    def get_target(self, page):
        """Get the target page for a given page."""
        target = None
        if not page.exists():
            if not self.opt.ignoremoves:
                with suppress(NoMoveTargetError,
                              CircularRedirectError,
                              InvalidTitleError):
                    target = page.moved_target()
        elif page.isRedirectPage():
            try:
                target = page.getRedirectTarget()
            except (CircularRedirectError,
                    InvalidTitleError,
                    InterwikiRedirectPageError):
                pass
            except RuntimeError as e:
                pywikibot.error(e)
            else:
                section = target.section()
                if section and not does_text_contain_section(target.text,
                                                             section):
                    pywikibot.warning(
                        'Section #{} not found on page {}'
                        .format(section, target.title(as_link=True,
                                                      with_section=False)))
                    target = None

        if target is not None \
           and target.namespace() in [2, 3] and page.namespace() not in [2, 3]:
            target = None
        return page, target

    def treat_page(self) -> None:
        """Change all redirects from the current page to actual links."""
        try:
            newtext = self.current_page.text
        except InvalidPageError as e:
            pywikibot.error(e)
            return

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(self.get_target, p)
                       for p in self.current_page.linkedPages()}
            for future in as_completed(futures):
                page, target = future.result()
                if target:
                    newtext = self.replace_links(newtext, page, target)

        self.put_current(newtext)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    featured = False
    options = {}
    gen = None

    # Process global args and prepare generator args parser
    gen_factory = pagegenerators.GeneratorFactory()
    local_args = pywikibot.handle_args(args)
    local_args = gen_factory.handle_args(local_args)

    unknown = []
    for arg in local_args:
        if arg == '-featured':
            featured = True
        elif arg in ('-always', '-ignoremoves', '-overwrite'):
            options[arg[1:]] = True
        else:
            unknown.append(arg)

    suggest_help(unknown_parameters=unknown)

    mysite = pywikibot.Site()
    if mysite.sitename == 'wikipedia:nl':
        pywikibot.info(
            '<<lightred>>There is consensus on the Dutch Wikipedia that '
            'bots should not be used to fix redirects.')
        return

    if featured:
        ref = mysite.page_from_repository(FEATURED_ARTICLES)
        if ref is not None:
            gen = ref.articles(namespaces=0, content=True)
        if not gen:
            suggest_help(
                unknown_parameters=['-featured'],
                additional_text='Option is not available for this site.')
            return
    else:
        gen = gen_factory.getCombinedGenerator(preload=True)
    if gen:
        bot = FixingRedirectBot(generator=gen, **options)
        bot.run()
    else:
        suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
