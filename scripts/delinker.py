#!/usr/bin/env python3
"""Delink removed files from wiki.

This script keeps track of image deletions and delinks removed files
from current wiki in namespace 0. This script is suitable to delink
files from an image repository as well as for local images.

The following parameters are supported:

-category:  Retrieve pages to delink from "Pages with missing files"
            category. Usually the category is found on Q4989282 wikibase
            item but can be overwritten by giving the category title
            with that option. *-since* option is ignored.

-exclude:   If the deletion log contains this pattern, the file is not
            delinked (default is 'no-delink').

-localonly  Retrieve deleted File pages from local log only

-since:     Start the deletion log with this timestamp given in MediaWiki
            timestamp format. If no `-since` option is given, the start
            timestamp is read from setting file. If the option is empty,
            the processing starts from the very beginning. If the script
            stops, the last timestamp is written to the settings file and
            the next script call starts there if no `-since` is given.

.. note:: This script is a :class:`ConfigParserBot <bot.ConfigParserBot>`.
   All settings can be made either by giving option with the command
   line or with a settings file which is scripts.ini by default. If you
   don't want the default values you can add any option you want to
   change to that settings file below the [delinker] section like.

.. versionadded:: 7.2
   This script is completely rewriten from compat branch.
.. versionchanged:: 9.4
   *-category* option was added.
"""
#
# (C) Pywikibot team, 2006-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import configparser
import heapq
import re
from difflib import get_close_matches

import pywikibot
from pywikibot.backports import removeprefix
from pywikibot.bot import (
    AutomaticTWSummaryBot,
    ConfigParserBot,
    SingleSiteBot,
    calledModuleName,
)
from pywikibot.textlib import case_escape, ignore_case


class CommonsDelinker(SingleSiteBot, ConfigParserBot, AutomaticTWSummaryBot):

    """Base Delinker Bot."""

    summary_key = 'delinker-delink'

    def skip_page(self, page) -> bool:
        """Skip pages which either exists locally or on shared repository."""
        pywikibot.info('.', newline=False)
        if page.exists() or page.file_is_shared():
            return True
        return super().skip_page(page)

    def treat(self, file_page):
        """Set page to current page and delink that page."""
        # use image_regex from image.py
        namespace = file_page.site.namespaces[6]
        escaped = case_escape(namespace.case,
                              file_page.title(with_ns=False),
                              underscore=True)
        self.image_regex = re.compile(
            r'\[\[ *(?:{})\s*:\s*{} *(?P<parameters>\|'
            r'(?:[^\[\]]|\[\[[^\]]+\]\]|\[[^\]]+\])*|) *\]\]'
            .format('|'.join(ignore_case(s) for s in namespace), escaped))

        shown = False
        for page in file_page.using_pages(
                content=True, namespaces=self.site.namespaces.MAIN):
            if not shown:
                pywikibot.info('\n>>> Delinking <<lightgreen>>'
                               f'{file_page.title()}<<default>> <<<')
                shown = True
            super().treat(page)

    def treat_page(self):
        """Delink a single page."""
        new = re.sub(self.image_regex, '', self.current_page.text)
        self.put_current(new)


class DelinkerFromCategory(CommonsDelinker):

    """Bot to delink deleted images from pages found in category."""

    pages_with_missing_files = 'Q4989282'

    update_options = {
        'exclude': 'no-delink',
        'localonly': False,
        'category': True,
    }

    @property
    def generator(self):
        """Retrieve pages with missing files and yield there image links."""
        if self.opt.category is True:
            cat = self.site.page_from_repository(self.pages_with_missing_files)
        else:
            cat = pywikibot.Category(self.site, self.opt.category)
            if not cat.exists():
                cat = None

        if not cat:
            pywikibot.warning('No valid category given for generator')
            return

        for article in cat.articles(namespaces=self.site.namespaces.MAIN):
            yield from article.imagelinks()

    def init_page(self, item) -> pywikibot.page.FilePage:
        """Upcast logevent to FilePage and combine edit summary."""
        return pywikibot.FilePage(item, ignore_extension=True)

    def skip_page(self, page) -> pywikibot.page.FilePage:
        """Skip pages which aren't deleted on any repository."""
        if super().skip_page(page):
            return True

        title = page.title(with_ns=False)
        params = {
            'logtype': 'delete',
            'page': 'File:' + title,
            'total': 1,
        }
        entries = list(self.site.logevents(**params))
        if not entries:
            entries = list(self.site.image_repository().logevents(**params))

        if not entries:
            pywikibot.info()
            pywikibot.warning(
                f'unable to delink missing {page.title(as_link=True)}')
            possibilities = [
                p.title(with_ns=False)
                for p in self.site.search(page.title(),
                                          namespaces=self.site.namespaces.MAIN,
                                          total=5)
            ]
            found = get_close_matches(title, possibilities, n=1)
            if found:
                pywikibot.info(
                    f'probably <<lightblue>>{found[0]}<<default>> is meant')
            return True

        self.summary_parameters = dict(entries[0])
        return False


class DelinkerFromLog(CommonsDelinker):

    """Bot to delink deleted images from deletion log."""

    update_options = {
        'exclude': 'no-delink',
        'localonly': False,
        'since': '',
    }

    @property
    def generator(self):
        """Read deletion logs and yield the oldest entry first."""
        ts = (pywikibot.Timestamp.fromtimestampformat(self.opt.since)
              if self.opt.since else None)
        params = {
            'logtype': 'delete',
            'namespace': 6,
            'reverse': True,
            'start': ts,
        }

        iterables = [self.site.logevents(**params)]
        repo = self.site.image_repository() if not self.opt.localonly else None
        if repo:
            iterables.append(repo.logevents(**params))

        for entry in heapq.merge(*iterables,
                                 key=lambda event: event.timestamp()):
            self.last_ts = entry.timestamp()
            if entry['action'] == 'delete' \
               and self.opt.exclude not in entry.get('comment', ''):
                yield entry

    def init_page(self, item) -> pywikibot.page.FilePage:
        """Upcast logevent to FilePage and combine edit summary."""
        self.summary_parameters = dict(item)
        return pywikibot.FilePage(item.page(), ignore_extension=True)

    def teardown(self):
        """Save the last used logevent timestamp."""
        if not hasattr(self, 'last_ts'):
            return

        pywikibot.info(f"\nUpdate 'since' to {self.INI} file")
        conf = configparser.ConfigParser(inline_comment_prefixes=[';'])
        conf.read(self.INI)
        section = calledModuleName()
        if not conf.has_section(section):
            conf.add_section(section)
        conf.set(section, 'since', self.last_ts.totimestampformat())
        with open(self.INI, 'w') as f:
            conf.write(f)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    options = {}
    local_args = pywikibot.handle_args()
    for arg in local_args:
        opt, _, value = arg.partition(':')
        opt = removeprefix(opt, '-')
        if opt == 'localonly':
            options[opt] = True
        elif opt == 'category':
            options[opt] = value or True
        else:
            options[opt] = value

    bot = DelinkerFromCategory if options.get('category') else DelinkerFromLog
    bot(**options).run()


if __name__ == '__main__':
    main()
