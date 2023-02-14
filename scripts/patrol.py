#!/usr/bin/env python3
"""
The bot is meant to mark the edits based on info obtained by whitelist.

This bot obtains a list of recent changes and newpages and marks the
edits as patrolled based on a whitelist.

Whitelist Format
~~~~~~~~~~~~~~~~

The whitelist is formatted as a number of list entries. Any links outside of
lists are ignored and can be used for documentation. In a list the first link
must be to the username which should be white listed and any other link
following is adding that page to the white list of that username. If the user
edited a page on their white list it gets patrolled. It will also patrol pages
which start with the mentioned link (e.g. [[foo]] will also patrol [[foobar]]).

To avoid redlinks it's possible to use Special:PrefixIndex as a prefix so that
it will list all pages which will be patrolled. The page after the slash will
be used then.

On Wikisource, it'll also check if the page is on the author namespace in which
case it'll also patrol pages which are linked from that page.

An example can be found at
https://en.wikisource.org/wiki/User:Wikisource-bot/patrol_whitelist

Commandline parameters:

-namespace         Filter the page generator to only yield pages in
                   specified namespaces
-ask               If True, confirm each patrol action
-whitelist         page title for whitelist (optional)
-autopatroluserns  Takes user consent to automatically patrol
-versionchecktime  Check versionchecktime lapse in sec
-repeat            Repeat run after 60 seconds
-newpages          Run on unpatrolled new pages
                   (default for Wikipedia Projects)
-recentchanges     Run on complete unpatrolled recentchanges
                   (default for any project except Wikipedia Projects)
-usercontribs      Filter generators above to the given user

"""
#
# (C) Pywikibot team, 2011-2023
#
# Distributed under the terms of the MIT license.
#
import time
from collections import defaultdict
from contextlib import suppress

import mwparserfromhell

import pywikibot
from pywikibot import pagegenerators
from pywikibot.backports import Container, removeprefix
from pywikibot.bot import BaseBot


def verbose_output(string) -> None:
    """Verbose output."""
    if pywikibot.config.verbose_output:
        pywikibot.info(string)


class PatrolBot(BaseBot):

    """Bot marks the edits as patrolled based on info obtained by whitelist."""

    update_options = {
        'ask': False,
        'whitelist': None,
        'versionchecktime': 300,
        'autopatroluserns': False,
    }
    # Localised name of the whitelist page
    whitelist_subpage_name = {
        'en': 'patrol_whitelist',
    }

    def __init__(self, site=None, **kwargs) -> None:
        """
        Initializer.

        :keyword ask: If True, confirm each patrol action
        :keyword whitelist: page title for whitelist (optional)
        :keyword autopatroluserns: Takes user consent to automatically patrol
        :keyword versionchecktime: Check versionchecktime lapse in sec
        """
        super().__init__(**kwargs)
        self.site = site or pywikibot.Site()
        self.recent_gen = True
        self.user = None
        if self.opt.whitelist:
            self.whitelist_pagename = self.opt.whitelist
        else:
            local_whitelist_subpage_name = pywikibot.translate(
                self.site, self.whitelist_subpage_name, fallback=True)
            self.whitelist_pagename = '{}:{}/{}'.format(
                self.site.namespace(2), self.site.username(),
                local_whitelist_subpage_name)
        self.whitelist = None
        self.whitelist_ts = 0
        self.whitelist_load_ts = 0

        self.highest_rcid = 0  # used to track loops
        self.last_rcid = 0

        self._load_prefix_index_aliases()

    def _load_prefix_index_aliases(self):
        """Load _prefixindex_aliases."""
        for entry in self.site.siteinfo['specialpagealiases']:
            if entry['realname'] == 'Prefixindex':
                self._prefixindex_aliases = {alias.lower()
                                             for alias in entry['aliases']}
                break
        else:
            raise RuntimeError('No alias for "prefixindex"')

    def setup(self):
        """Load most recent watchlist_page for further processing."""
        # Check for a more recent version after versionchecktime in sec.
        if (self.whitelist_load_ts and (time.time() - self.whitelist_load_ts
                                        < self.opt.versionchecktime)):
            verbose_output('Whitelist not stale yet')
            return

        whitelist_page = pywikibot.Page(self.site,
                                        self.whitelist_pagename)

        if not self.whitelist:
            pywikibot.info('Loading ' + self.whitelist_pagename)

        try:
            if self.whitelist_ts:
                # check for a more recent version
                h = whitelist_page.revisions()
                last_edit_ts = next(h).timestamp
                if last_edit_ts == self.whitelist_ts:
                    # As there hasn't been any change to the whitelist
                    # it has been effectively reloaded 'now'
                    self.whitelist_load_ts = time.time()
                    verbose_output('Whitelist not modified')
                    return

            if self.whitelist:
                pywikibot.info('Reloading whitelist')

            # Fetch whitelist
            wikitext = whitelist_page.get()
            # Parse whitelist
            self.whitelist = self.parse_page_tuples(wikitext, self.user)
            # Record timestamp
            self.whitelist_ts = whitelist_page.latest_revision.timestamp
            self.whitelist_load_ts = time.time()
        except Exception as e:
            # cascade if there isn't a whitelist to fallback on
            if not self.whitelist:
                raise
            pywikibot.error(str(e))

    @staticmethod
    def in_list(pagelist: Container, title: str) -> bool:
        """Check if title present in pagelist."""
        verbose_output('Checking whitelist for: ' + title)

        # quick check for exact match
        if title in pagelist:
            return True

        # quick check for wildcard
        if '' in pagelist:
            verbose_output('wildcarded')
            return True

        for item in pagelist:
            verbose_output('checking against whitelist item = ' + item)

            if isinstance(item, LinkedPagesRule):
                verbose_output('invoking programmed rule')
                if item.match(title):
                    return True

            elif title.startswith(item):
                return True
        verbose_output('not found')
        return False

    def parse_page_tuples(self, wikitext, user=None):
        """Parse page details apart from 'user:' for use."""
        whitelist = defaultdict(set)

        current_user = False
        parsed = mwparserfromhell.parse(wikitext)
        for node in parsed.nodes:
            if isinstance(node, mwparserfromhell.nodes.tag.Tag):
                if node.tag == 'li':
                    current_user = None
                continue
            if isinstance(node, mwparserfromhell.nodes.text.Text):
                if node.endswith('\n'):
                    current_user = False
                continue
            if isinstance(node, mwparserfromhell.nodes.wikilink.Wikilink):
                if current_user is False:
                    pywikibot.debug('Link to "{}" ignored as outside list'
                                    .format(node.title))
                    continue

                obj = pywikibot.Link(node.title, self.site)
                if obj.namespace == -1:
                    # the parser accepts 'special:prefixindex/' as a wildcard
                    # this allows a prefix that doesn't match an existing page
                    # to be a blue link, and can be clicked to see what pages
                    # will be included in the whitelist
                    name, _, prefix = obj.title.partition('/')
                    if name.lower() in self._prefixindex_aliases:
                        if not prefix:
                            verbose_output('Whitelist everything')
                            page = ''
                        else:
                            page = prefix
                            verbose_output('Whitelist prefixindex hack for: '
                                           + page)

                elif obj.namespace == 2 and not current_user:
                    # if a target user hasn't been found yet, and the link is
                    # 'user:'
                    # the user will be the target of subsequent rules
                    current_user = obj.title
                    verbose_output('Whitelist user: ' + current_user)
                    continue
                else:
                    page = obj.canonical_title()

                if current_user:
                    if not user or current_user == user:
                        if self.is_wikisource_author_page(page):
                            verbose_output('Whitelist author: ' + page)
                            page = LinkedPagesRule(page)
                        else:
                            verbose_output('Whitelist page: ' + page)
                        verbose_output('Adding {}:{}'
                                       .format(current_user, page))
                        whitelist[current_user].add(page)
                    else:
                        verbose_output(
                            'Discarding whitelist page for another user: '
                            + page)
                else:
                    raise Exception('No user set for page ' + page)

        return dict(whitelist)

    def is_wikisource_author_page(self, title) -> bool:
        """Patrol a single item."""
        if self.site.family.name != 'wikisource':
            return False

        author_ns = 0
        with suppress(AttributeError, KeyError):
            author_ns = self.site.family.authornamespaces[self.site.lang][0]

        author_ns_prefix = self.site.namespace(author_ns) + ':'
        author_page_name = removeprefix(title, author_ns_prefix)
        if title != author_page_name:
            verbose_output('Found author ' + author_page_name)
            return True
        return False

    def treat(self, page):
        """It loads the given page, does some changes, and saves it."""
        choice = False

        # page: title, date, username, comment, loginfo, rcid, token
        username = page['user']
        # when the feed isn't from the API, it used to contain
        # '(not yet written)' or '(page does not exist)' when it was
        # a redlink
        rcid = page['rcid']
        title = page['title']
        if not rcid:
            raise Exception('rcid not present')

        # check whether we have wrapped around to higher rcids
        # which indicates a new RC feed is being processed
        if rcid > self.last_rcid:
            # refresh the whitelist
            self.setup()

        if pywikibot.config.verbose_output or self.opt.ask:
            pywikibot.info(
                f'User {username} has created or modified page {title}')

        # simple rule to whitelist any user editing their own userspace
        if self.opt.autopatroluserns and page['ns'] in (2, 3) \
           and title.partition(':')[2].split('/')[0].startswith(username):
            verbose_output(f'{username} is whitelisted to modify {title}')
            choice = True

        if not choice and username in self.whitelist \
           and self.in_list(self.whitelist[username], title):
            verbose_output(f'{username} is whitelisted to modify {title}')
            choice = True

        if self.opt.ask:
            choice = pywikibot.input_yn(
                'Do you want to mark page as patrolled?')

        # Patrol the page
        if choice:
            # list() iterates over patrol() which returns a generator
            list(self.site.patrol(rcid))
            pywikibot.info(
                f'Patrolled {title} (rcid {rcid}) by user {username}')
        else:
            verbose_output('Skipped')

        if rcid > self.highest_rcid:
            self.highest_rcid = rcid
        self.last_rcid = rcid


class LinkedPagesRule:

    """Matches of page site title and linked pages title."""

    def __init__(self, page_title: str) -> None:
        """Initializer.

        :param page_title: The page title for this rule
        """
        self.site = pywikibot.Site()
        self.page_title = page_title
        self.linkedpages = None

    def match(self, page_title) -> bool:
        """Match page_title to linkedpages elements."""
        if page_title == self.page_title:
            return True

        if not self.site.family.name == 'wikisource':
            raise Exception('This is a wikisource rule')

        if not self.linkedpages:
            verbose_output('loading page links on ' + self.page_title)
            p = pywikibot.Page(self.site, self.page_title)
            linkedpages = []
            for linkedpage in p.linkedPages():
                linkedpages.append(linkedpage.title())

            self.linkedpages = linkedpages
            verbose_output(f'Loaded {len(linkedpages)} page links')

        for p in self.linkedpages:
            verbose_output(f"Checking against '{p}'")
            if page_title.startswith(p):
                verbose_output('Matched.')
                return True
        return False


def api_feed_repeater(
    gen,
    delay: float = 0,
    repeat: bool = False,
    namespaces=None,
    user=None,
    recent_new_gen: bool = True
):
    """Generator which loads pages details to be processed."""
    while True:
        if recent_new_gen:
            generator = gen(namespaces=namespaces, user=user, patrolled=False)
        else:
            generator = gen(namespaces=namespaces, user=user,
                            returndict=True, patrolled=False)
        for page in generator:
            if recent_new_gen:
                yield page
            else:
                yield page[1]
        if repeat:
            pywikibot.info(f'Sleeping for {delay} seconds')
            pywikibot.sleep(delay)
        else:
            break


def main(*args: str) -> None:
    """Process command line arguments and invoke PatrolBot."""
    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    usercontribs = None
    recentchanges = False
    newpages = False
    repeat = False
    options = {}

    # Parse command line arguments
    local_args = pywikibot.handle_args(args)
    site = pywikibot.Site()
    gen_factory = pagegenerators.GeneratorFactory(site)
    for arg in local_args:
        if arg.startswith('-ask'):
            options['ask'] = True
        elif arg.startswith('-autopatroluserns'):
            options['autopatroluserns'] = True
        elif arg.startswith('-repeat'):
            repeat = True
        elif arg.startswith('-newpages'):
            newpages = True
        elif arg.startswith('-recentchanges'):
            recentchanges = True
        elif arg.startswith('-usercontribs:'):
            usercontribs = arg[14:]
        elif arg.startswith('-versionchecktime:'):
            versionchecktime = arg[len('-versionchecktime:'):]
            options['versionchecktime'] = int(versionchecktime)
        elif arg.startswith('-whitelist:'):
            options['whitelist'] = arg[len('-whitelist:'):]
        else:
            generator = gen_factory.handle_arg(arg)
            if not generator and ':' in arg:
                m = arg.split(':')
                options[m[0]] = m[1]

    if usercontribs:
        user = pywikibot.User(site, usercontribs)
        if user.isAnonymous() or user.isRegistered():
            pywikibot.info(f'Processing user: {usercontribs}')
        else:
            pywikibot.warning('User {} does not exist on site {}.'
                              .format(usercontribs, site))

    # default behaviour
    if not any((newpages, recentchanges, usercontribs)):
        if site.family.name == 'wikipedia':
            newpages = True
        else:
            recentchanges = True

    if newpages or usercontribs:
        pywikibot.info('Newpages:')
        gen = site.newpages
        feed = api_feed_repeater(gen, delay=60, repeat=repeat,
                                 user=usercontribs,
                                 namespaces=gen_factory.namespaces,
                                 recent_new_gen=False)
        bot = PatrolBot(site=site, generator=feed, **options)
        bot.treat_page_type = dict
        bot.run()

    if recentchanges or usercontribs:
        pywikibot.info('Recentchanges:')
        gen = site.recentchanges
        feed = api_feed_repeater(gen, delay=60, repeat=repeat,
                                 namespaces=gen_factory.namespaces,
                                 user=usercontribs)
        bot = PatrolBot(site=site, generator=feed, **options)
        bot.treat_page_type = dict
        bot.run()


if __name__ == '__main__':
    main()
