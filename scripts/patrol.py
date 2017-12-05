#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
The bot is meant to mark the edits based on info obtained by whitelist.

This bot obtains a list of recent changes and newpages and marks the
edits as patrolled based on a whitelist.

Whitelist format
================

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

An example can be found at:

https://en.wikisource.org/wiki/User:Wikisource-bot/patrol_whitelist

&params;

Commandline parameters
======================

-namespace         Filter the page generator to only yield pages in
                    specified namespaces
-ask               If True, confirm each patrol action
-whitelist         page title for whitelist (optional)
-autopatroluserns  Takes user consent to automatically patrol
-versionchecktime  Check versionchecktime lapse in sec

"""
#
# (C) Pywikibot team, 2011-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import time

from collections import defaultdict

import mwparserfromhell

import pywikibot

from pywikibot import pagegenerators

from pywikibot.bot import SingleSiteBot

_logger = 'patrol'

# This is required for the text that is shown when you run this script
# with the parameter -help.
docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}


class PatrolBot(SingleSiteBot):

    """Bot marks the edits as patrolled based on info obtained by whitelist."""

    # Localised name of the whitelist page
    whitelist_subpage_name = {
        'en': u'patrol_whitelist',
    }

    def __init__(self, site=True, **kwargs):
        """
        Constructor.

        @kwarg feed: The changes feed to work on (Newpages or Recentchanges)
        @kwarg ask: If True, confirm each patrol action
        @kwarg whitelist: page title for whitelist (optional)
        @kwarg autopatroluserns: Takes user consent to automatically patrol
        @kwarg versionchecktime: Check versionchecktime lapse in sec
        """
        self.availableOptions.update({
            'ask': False,
            'feed': None,
            'whitelist': None,
            'versionchecktime': 300,
            'autopatroluserns': False
        })
        super(PatrolBot, self).__init__(site, **kwargs)
        self.recent_gen = True
        self.user = None
        if self.getOption('whitelist'):
            self.whitelist_pagename = self.getOption('whitelist')
        else:
            local_whitelist_subpage_name = pywikibot.translate(
                self.site, self.whitelist_subpage_name, fallback=True)
            self.whitelist_pagename = u'%s:%s/%s' % (
                                      self.site.namespace(2),
                                      self.site.username(),
                                      local_whitelist_subpage_name)
        self.whitelist = self.getOption('whitelist')
        self.whitelist_ts = 0
        self.whitelist_load_ts = 0

        self.highest_rcid = 0  # used to track loops
        self.last_rcid = 0
        self.repeat_start_ts = 0

        self.rc_item_counter = 0  # counts how many items have been reviewed
        self.patrol_counter = 0  # and how many times an action was taken
        for entry in self.site.siteinfo['specialpagealiases']:
            if entry['realname'] == 'Prefixindex':
                self._prefixindex_aliases = set(alias.lower()
                                                for alias in entry['aliases'])
                break
        else:
            raise RuntimeError('No alias for "prefixindex"')

    def load_whitelist(self):
        """Load most recent watchlist_page for further processing."""
        # Check for a more recent version after versionchecktime in sec.
        if (self.whitelist_load_ts and (time.time() - self.whitelist_load_ts <
                                        self.getOption('versionchecktime'))):
            if pywikibot.config.verbose_output:
                pywikibot.output(u'Whitelist not stale yet')
            return

        whitelist_page = pywikibot.Page(self.site,
                                        self.whitelist_pagename)

        if not self.whitelist:
            pywikibot.output(u'Loading %s' % self.whitelist_pagename)

        try:
            if self.whitelist_ts:
                # check for a more recent version
                h = whitelist_page.revisions()
                last_edit_ts = next(h).timestamp
                if last_edit_ts == self.whitelist_ts:
                    # As there hasn't been any change to the whitelist
                    # it has been effectively reloaded 'now'
                    self.whitelist_load_ts = time.time()
                    if pywikibot.config.verbose_output:
                        pywikibot.output(u'Whitelist not modified')
                    return

            if self.whitelist:
                pywikibot.output(u'Reloading whitelist')

            # Fetch whitelist
            wikitext = whitelist_page.get()
            # Parse whitelist
            self.whitelist = self.parse_page_tuples(wikitext, self.user)
            # Record timestamp
            self.whitelist_ts = whitelist_page.editTime()
            self.whitelist_load_ts = time.time()
        except Exception as e:
            # cascade if there isnt a whitelist to fallback on
            if not self.whitelist:
                raise
            pywikibot.error(u'%s' % e)

    def in_list(self, pagelist, title):
        """Check if title present in pagelist."""
        if pywikibot.config.verbose_output:
            pywikibot.output(u'Checking whitelist for: %s' % title)

        # quick check for exact match
        if title in pagelist:
            return title

        # quick check for wildcard
        if '' in pagelist:
            if pywikibot.config.verbose_output:
                pywikibot.output(u'wildcarded')
            return '.*'

        for item in pagelist:
            if pywikibot.config.verbose_output:
                pywikibot.output('checking against whitelist item = %s' % item)

            if isinstance(item, LinkedPagesRule):
                if pywikibot.config.verbose_output:
                    pywikibot.output(u'invoking programmed rule')
                if item.match(title):
                    return item

            elif title_match(item, title):
                return item

        if pywikibot.config.verbose_output:
            pywikibot.output(u'not found')

    def parse_page_tuples(self, wikitext, user=None):
        """Parse page details apart from 'user:' for use."""
        whitelist = defaultdict(list)

        current_user = False
        parsed = mwparserfromhell.parse(wikitext)
        for node in parsed.nodes:
            if isinstance(node, mwparserfromhell.nodes.tag.Tag):
                if node.tag == 'li':
                    current_user = None
            elif isinstance(node, mwparserfromhell.nodes.text.Text):
                if node.endswith('\n'):
                    current_user = False
            elif isinstance(node, mwparserfromhell.nodes.wikilink.Wikilink):
                if current_user is False:
                    pywikibot.debug('Link to "{0}" ignored as outside '
                                    'list'.format(node.title), _logger)
                    continue

                obj = pywikibot.Link(node.title, self.site)
                if obj.namespace == -1:
                    # the parser accepts 'special:prefixindex/' as a wildcard
                    # this allows a prefix that doesnt match an existing page
                    # to be a blue link, and can be clicked to see what pages
                    # will be included in the whitelist
                    name, sep, prefix = obj.title.partition('/')
                    if name.lower() in self._prefixindex_aliases:
                        if not prefix:
                            if pywikibot.config.verbose_output:
                                pywikibot.output(u'Whitelist everything')
                            page = ''
                        else:
                            page = prefix
                            if pywikibot.config.verbose_output:
                                pywikibot.output(u'Whitelist prefixindex hack '
                                                 u'for: %s' % page)
                            # p = pywikibot.Page(self.site, obj.target[20:])
                            # obj.namespace = p.namespace
                            # obj.target = p.title()

                elif obj.namespace == 2 and not current_user:
                    # if a target user hasn't been found yet, and the link is
                    # 'user:'
                    # the user will be the target of subsequent rules
                    current_user = obj.title
                    if pywikibot.config.verbose_output:
                        pywikibot.output(u'Whitelist user: %s' % current_user)
                    continue
                else:
                    page = obj.canonical_title()

                if current_user:
                    if not user or current_user == user:
                        if self.is_wikisource_author_page(page):
                            if pywikibot.config.verbose_output:
                                pywikibot.output('Whitelist author: %s' % page)
                            page = LinkedPagesRule(page)
                        else:
                            if pywikibot.config.verbose_output:
                                pywikibot.output(u'Whitelist page: %s' % page)
                        if pywikibot.config.verbose_output:
                            pywikibot.output('Adding {0}:{1}'
                                             .format(current_user, page))
                        whitelist[current_user].append(page)
                    elif pywikibot.config.verbose_output:
                        pywikibot.output(u'Discarding whitelist page for '
                                         u'another user: %s' % page)
                else:
                    raise Exception(u'No user set for page %s' % page)

        return dict(whitelist)

    def is_wikisource_author_page(self, title):
        """Initialise author_ns if site family is 'wikisource' else pass."""
        if self.site.family.name != 'wikisource':
            return

        author_ns = 0
        try:
            author_ns = self.site.family.authornamespaces[self.site.lang][0]
        except Exception:
            pass
        if author_ns:
            author_ns_prefix = self.site.namespace(author_ns)
        pywikibot.debug(u'Author ns: %d; name: %s'
                        % (author_ns, author_ns_prefix), _logger)
        if title.find(author_ns_prefix + ':') == 0:
            if pywikibot.config.verbose_output:
                author_page_name = title[len(author_ns_prefix) + 1:]
                pywikibot.output(u'Found author %s' % author_page_name)
            return True

    def run(self, feed=None):
        """Process 'whitelist' page absent in generator."""
        if self.whitelist is None:
            self.load_whitelist()
        if not feed:
            feed = self.getOption('feed')
        for page in feed:
            self.treat(page)

    def treat(self, page):
        """It loads the given page, does some changes, and saves it."""
        choice = False
        try:
            # page: title, date, username, comment, loginfo, rcid, token
            username = page['user']
            # when the feed isnt from the API, it used to contain
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
                self.load_whitelist()
                self.repeat_start_ts = time.time()

            if pywikibot.config.verbose_output or self.getOption('ask'):
                pywikibot.output(u'User %s has created or modified page %s'
                                 % (username, title))

            if self.getOption('autopatroluserns') and (page['ns'] == 2 or
                                                       page['ns'] == 3):
                # simple rule to whitelist any user editing their own userspace
                if title.partition(':')[2].split('/')[0].startswith(username):
                    if pywikibot.config.verbose_output:
                        pywikibot.output(u'%s is whitelisted to modify %s'
                                         % (username, title))
                    choice = True

            if not choice and username in self.whitelist:
                if self.in_list(self.whitelist[username], title):
                    if pywikibot.config.verbose_output:
                        pywikibot.output(u'%s is whitelisted to modify %s'
                                         % (username, title))
                    choice = True

            if self.getOption('ask'):
                choice = pywikibot.input_yn(
                    'Do you want to mark page as patrolled?',
                    automatic_quit=False)

            # Patrol the page
            if choice:
                # list() iterates over patrol() which returns a generator
                list(self.site.patrol(rcid))
                self.patrol_counter = self.patrol_counter + 1
                pywikibot.output(u'Patrolled %s (rcid %d) by user %s'
                                 % (title, rcid, username))
            else:
                if pywikibot.config.verbose_output:
                    pywikibot.output(u'Skipped')

            if rcid > self.highest_rcid:
                self.highest_rcid = rcid
            self.last_rcid = rcid
            self.rc_item_counter = self.rc_item_counter + 1

        except pywikibot.NoPage:
            pywikibot.output(u'Page %s does not exist; skipping.'
                             % title(asLink=True))
        except pywikibot.IsRedirectPage:
            pywikibot.output(u'Page %s is a redirect; skipping.'
                             % title(asLink=True))


def title_match(prefix, title):
    """Match title substring with given prefix."""
    if pywikibot.config.verbose_output:
        pywikibot.output(u'Matching %s to prefix %s' % (title, prefix))
    if title.startswith(prefix):
        if pywikibot.config.verbose_output:
            pywikibot.output(u'substr match')
        return True
    return


class LinkedPagesRule(object):

    """Matches of page site title and linked pages title."""

    def __init__(self, page_title):
        """Constructor.

        @param page_title: The page title for this rule
        @type page_title: pywikibot.Page
        """
        self.site = pywikibot.Site()
        self.page_title = page_title
        self.linkedpages = None

    def title(self):
        """Obtain page title."""
        return self.page_title

    def match(self, page_title):
        """Match page_title to linkedpages elements."""
        if page_title == self.page_title:
            return True

        if not self.site.family.name == 'wikisource':
            raise Exception('This is a wikisource rule')

        if not self.linkedpages:
            if pywikibot.config.verbose_output:
                pywikibot.output(u'loading page links on %s' % self.page_title)
            p = pywikibot.Page(self.site, self.page_title)
            linkedpages = []
            for linkedpage in p.linkedPages():
                linkedpages.append(linkedpage.title())

            self.linkedpages = linkedpages
            if pywikibot.config.verbose_output:
                pywikibot.output(u'Loaded %d page links' % len(linkedpages))

        for p in self.linkedpages:
            if pywikibot.config.verbose_output:
                pywikibot.output(u"Checking against '%s'" % p)
            if title_match(p, page_title):
                if pywikibot.config.verbose_output:
                    pywikibot.output(u'Matched.')
                return p


def api_feed_repeater(gen, delay=0, repeat=False, namespaces=None,
                      user=None, recent_new_gen=True):
    """Generator which loads pages details to be processed."""
    while True:
        if recent_new_gen:
            generator = gen(namespaces=namespaces, user=user,
                            showPatrolled=False)
        else:
            generator = gen(namespaces=namespaces, user=user,
                            returndict=True, showPatrolled=False)
        for page in generator:
            if recent_new_gen:
                yield page
            else:
                yield page[1]
        if repeat:
            pywikibot.output(u'Sleeping for %d seconds' % delay)
            time.sleep(delay)
        else:
            break


def main(*args):
    """Process command line arguments and invoke PatrolBot."""
    # This factory is responsible for processing command line arguments
    # that are also used by other scripts and that determine on which pages
    # to work on.
    usercontribs = None
    gen = None
    recentchanges = False
    newpages = False
    repeat = False
    genFactory = pagegenerators.GeneratorFactory()
    options = {}

    # Parse command line arguments
    for arg in pywikibot.handle_args(args):
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
        elif arg.startswith("-whitelist:"):
            options['whitelist'] = arg[len('-whitelist:'):]
        else:
            generator = genFactory.handleArg(arg)
            if not generator:
                if ':' in arg:
                    m = arg.split(':')
                    options[m[0]] = m[1]

    site = pywikibot.Site()
    site.login()

    if usercontribs:
        pywikibot.output(u'Processing user: %s' % usercontribs)

    if not newpages and not recentchanges and not usercontribs:
        if site.family.name == 'wikipedia':
            newpages = True
        else:
            recentchanges = True

    bot = PatrolBot(**options)

    if newpages or usercontribs:
        pywikibot.output(u'Newpages:')
        gen = site.newpages
        feed = api_feed_repeater(gen, delay=60, repeat=repeat,
                                 user=usercontribs,
                                 namespaces=genFactory.namespaces,
                                 recent_new_gen=False)
        bot.run(feed)

    if recentchanges or usercontribs:
        pywikibot.output(u'Recentchanges:')
        gen = site.recentchanges
        feed = api_feed_repeater(gen, delay=60, repeat=repeat,
                                 namespaces=genFactory.namespaces,
                                 user=usercontribs)
        bot.run(feed)

    pywikibot.output(u'%d/%d patrolled'
                     % (bot.patrol_counter, bot.rc_item_counter))


if __name__ == '__main__':
    main()
