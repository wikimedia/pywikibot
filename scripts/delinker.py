#!/usr/bin/env python3
"""Delink removed files from wiki.

This script keeps track of image deletions and delinks removed files
from current wiki in namespace 0. This script is suitable to delink
files from an image repository as well as for local images.

The following parameters are supported:

-exclude:   If the deletion log contains this pattern, the file is not
            delinked (default is 'no-delink').

-localonly  Retrieve deleted File pages from local log only

-since:     Start the deletion log with this timestamp given in MediaWiki
            timestamp format. If no `-since` option is given, the start
            timestamp is read from setting file. If the option is empty,
            the processing starts from the very beginning. If the script
            stops, the last timestamp is written to the settings file and
            the next script call starts there if no `-since` is given.

.. note:: This sample script is a
   :class:`ConfigParserBot <bot.ConfigParserBot>`. All
   settings can be made either by giving option with the command line or
   with a settings file which is scripts.ini by default. If you don't
   want the default values you can add any option you want to change to
   that settings file below the [delinker] section like.

.. versionadded:: 7.2
   This script is completely rewriten from compat branch.
"""
#
# (C) Pywikibot team, 2006-2023
#
# Distributed under the terms of the MIT license.
#
import configparser
import heapq
import re

import pywikibot
from pywikibot.backports import removeprefix
from pywikibot.bot import (
    AutomaticTWSummaryBot,
    ConfigParserBot,
    SingleSiteBot,
    calledModuleName,
)
from pywikibot.textlib import case_escape, ignore_case, replaceExcept


class CommonsDelinker(SingleSiteBot, ConfigParserBot, AutomaticTWSummaryBot):

    """Bot to delink deleted images."""

    update_options = {
        'exclude': 'no-delink',
        'localonly': False,
        'since': '',
    }
    summary_key = 'delinker-delink'

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

    def init_page(self, item) -> 'pywikibot.page.FilePage':
        """Upcast logevent to FilePage and combine edit summary."""
        self.summary_parameters = dict(item)
        return pywikibot.FilePage(self.site, item['title'])

    def skip_page(self, page) -> bool:
        """Skip pages which neither exists locally nor on shared repository."""
        pywikibot.info('.', newline=False)
        if page.file_is_shared() or page.exists():
            return True
        return super().skip_page(page)

    def treat(self, file_page):
        """Set page to current page and delink that page."""
        # use image_regex from image.py
        namespace = file_page.site.namespaces[6]
        escaped = case_escape(namespace.case, file_page.title(with_ns=False))
        # Be careful, spaces and _ have been converted to '\ ' and '\_'
        escaped = re.sub('\\\\[_ ]', '[_ ]', escaped)
        self.image_regex = re.compile(
            r'\[\[ *(?:{})\s*:\s*{} *(?P<parameters>\|'
            r'(?:[^\[\]]|\[\[[^\]]+\]\]|\[[^\]]+\])*|) *\]\]'
            .format('|'.join(ignore_case(s) for s in namespace), escaped))

        shown = False
        for page in file_page.using_pages(content=True, namespaces=0):
            if not shown:
                pywikibot.info(
                    '\n>>> <<lightgreen>>Delinking {}<<default>> <<<'
                    .format(file_page.title()))
                shown = True
            super().treat(page)

    def treat_page(self):
        """Delink a single page."""
        new = replaceExcept(self.current_page.text, self.image_regex, '', [])
        self.put_current(new)

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
        else:
            options[opt] = value

    bot = CommonsDelinker(site=pywikibot.Site(), **options)
    bot.run()


if __name__ == '__main__':
    main()
