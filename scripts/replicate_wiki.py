#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot replicates pages in a wiki to a second wiki within one family.

Example:

    python pwb.py replicate_wiki [-r] -ns 10 -family:wikipedia -o nl li fy

or

    python pwb.py replicate_wiki [-r] -ns 10 -family:wikipedia -lang:nl li fy

to copy all templates from an nlwiki to liwiki and fywiki. It will show which
pages have to be changed if -r is not present, and will only actually write
pages if -r /is/ present.

You can add replicate_replace to your user_config.py, which has the following
format:

replicate_replace = {
    'wikipedia:li': {'Hoofdpagina': 'Veurblaad'}
}

to replace all occurrences of 'Hoofdpagina' with 'Veurblaad' when writing to
liwiki. Note that this does not take the origin wiki into account.

The following parameters are supported:
-r                actually replace pages (without this option
--replace         you will only get an overview page)

-o                original wiki
--original        (you may use -lang:<code> option instead)

destination_wiki  destination wiki(s)

-ns               specify namespace
--namespace

-dns              destination namespace (if different)
--dest-namespace
"""
#
# (C) Kasper Souren, 2012-2013
# (C) Pywikibot team, 2013-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import sys

from argparse import ArgumentParser

import pywikibot

from pywikibot import config, Page
from pywikibot.tools import deprecated


@deprecated('BaseSite.namespaces')
def namespaces(site):
    """Return a dictionary from namespace number to prefix."""
    return dict((n.id, n.custom_name) for n in site.namespaces)


def multiple_replace(text, word_dict):
    """Replace all occurrences in text of key value pairs in word_dict."""
    for key in word_dict:
        text = text.replace(key, word_dict[key])
    return text


class SyncSites(object):

    """Work is done in here."""

    def __init__(self, options):
        """Constructor."""
        self.options = options

        if options.original_wiki:
            original_wiki = options.original_wiki
        else:
            original_wiki = config.mylang

        pywikibot.output("Syncing from " + original_wiki)

        family = config.family

        sites = options.destination_wiki

        self.original = pywikibot.Site(original_wiki, family)
        self.original.login()

        if options.namespace and 'help' in options.namespace:
            for namespace in self.original.namespaces.values():
                pywikibot.output(
                    '{0} {1}'.format(namespace.id, namespace.custom_name))
            sys.exit()

        self.sites = [pywikibot.Site(s, family) for s in sites]

        self.differences = {}
        self.user_diff = {}
        pywikibot.output('Syncing to ', newline=False)
        for s in self.sites:
            s.login()
            self.differences[s] = []
            self.user_diff[s] = []
            pywikibot.output(str(s), newline=False)
        pywikibot.output('')

    def check_sysops(self):
        """Check if sysops are the same on all wikis."""
        def get_users(site):
            userlist = [ul['name'] for ul in site.allusers(group='sysop')]
            return set(userlist)

        ref_users = get_users(self.original)
        for site in self.sites:
            users = get_users(site)
            diff = list(ref_users.difference(users))
            diff.sort()
            self.user_diff[site] = diff

    def check_namespaces(self):
        """Check all namespaces, to be ditched for clarity."""
        namespaces = [
            0,    # Main
            8,    # MediaWiki
            152,  # DPL
            102,  # Eigenschap
            104,  # Type
            106,  # Formulier
            108,  # Concept
            10,   # Sjabloon
        ]

        if self.options.namespace:
            pywikibot.output(str(self.options.namespace))
            namespaces = [int(self.options.namespace)]
        pywikibot.output("Checking these namespaces: %s\n" % (namespaces,))

        for ns in namespaces:
            self.check_namespace(ns)

    def check_namespace(self, namespace):
        """Check an entire namespace."""
        pywikibot.output("\nCHECKING NAMESPACE %s" % namespace)
        pages = (p.title() for p in self.original.allpages(
            '!', namespace=namespace))
        for p in pages:
            if p not in ['MediaWiki:Sidebar', 'MediaWiki:Mainpage',
                         'MediaWiki:Sitenotice', 'MediaWiki:MenuSidebar']:
                try:
                    self.check_page(p)
                except pywikibot.exceptions.NoPage:
                    pywikibot.output('Bizarre NoPage exception that we are '
                                     'just going to ignore')
                except pywikibot.exceptions.IsRedirectPage:
                    pywikibot.output(
                        'error: Redirectpage - todo: handle gracefully')
        pywikibot.output('')

    def generate_overviews(self):
        """Create page on wikis with overview of bot results."""
        for site in self.sites:
            sync_overview_page = Page(site,
                                      'User:%s/sync.py overview' % site.user())
            output = "== Pages that differ from original ==\n\n"
            if self.differences[site]:
                output += "".join('* [[:%s]]\n' % l for l in
                                  self.differences[site])
            else:
                output += "All important pages are the same"

            output += (
                '\n\n== Admins from original that are missing here ==\n\n')
            if self.user_diff[site]:
                output += "".join('* %s\n' % l.replace('_', ' ') for l in
                                  self.user_diff[site])
            else:
                output += (
                    'All users from original are also present on this wiki')

            pywikibot.output(output)
            sync_overview_page.text = output
            sync_overview_page.save(self.put_message(site))

    def put_message(self, site):
        """Return synchonization message."""
        return ('%s replicate_wiki.py synchronization from %s'
                % (site.user(), str(self.original)))

    def check_page(self, pagename):
        """Check one page."""
        pywikibot.output("\nChecking %s" % pagename)
        sys.stdout.flush()
        page1 = Page(self.original, pagename)
        txt1 = page1.text

        if self.options.dest_namespace:
            dest_ns = int(self.options.dest_namespace)
        else:
            dest_ns = None

        for site in self.sites:
            if dest_ns is not None:
                page2 = Page(site, page1.title(withNamespace=False), dest_ns)
                pywikibot.output("\nCross namespace, new title: %s"
                                 % page2.title())
            else:
                page2 = Page(site, pagename)

            if page2.exists():
                txt2 = page2.text
            else:
                txt2 = ''

            if str(site) in config.replicate_replace:
                txt_new = multiple_replace(txt1,
                                           config.replicate_replace[str(site)])
                if txt1 != txt_new:
                    pywikibot.output(
                        'NOTE: text replaced using config.sync_replace')
                    pywikibot.output('%s %s %s' % (txt1, txt_new, txt2))
                    txt1 = txt_new

            if txt1 != txt2:
                pywikibot.output("\n %s DIFFERS" % site)
                self.differences[site].append(pagename)

        if self.options.replace:
            page2.text = txt1
            page2.save(self.put_message(site))
        else:
            sys.stdout.write('.')
            sys.stdout.flush()


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    my_args = pywikibot.handle_args(args)

    parser = ArgumentParser(add_help=False)
    parser.add_argument("-r", "--replace", action="store_true",
                        help="actually replace pages (without this "
                             "option you will only get an overview page)")
    parser.add_argument("-o", "--original", dest="original_wiki",
                        help="original wiki")
    parser.add_argument('destination_wiki', metavar='destination',
                        type=str, nargs='+', help='destination wiki(s)')
    parser.add_argument("-ns", "--namespace", dest="namespace",
                        help="specify namespace")
    parser.add_argument("-dns", "--dest-namespace", dest="dest_namespace",
                        help="destination namespace (if different)")

    options = parser.parse_args(my_args)

    sync = SyncSites(options)
    sync.check_sysops()
    sync.check_namespaces()
    sync.generate_overviews()


if __name__ == '__main__':
    main()
