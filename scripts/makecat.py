#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
This bot takes as its argument the name of a new or existing category.

It will then try to find new articles for this category
(pages linked to and from pages already in the category),
asking the user which pages to include and which not.

The following command line parameters are supported:

-nodates    Automatically skip all pages that are years or dates
            (years only work AD, dates only for certain languages).

-forward    Only check pages linked from pages already in the category,
            not pages linking to them. Is less precise but quite a bit faster.

-exist      Only ask about pages that do actually exist;
            drop any titles of non-existing pages silently.
            If -forward is chosen, -exist is automatically implied.

-keepparent Do not remove parent categories of the category to be worked on.

-all        Work on all pages (default: only main namespace)

When running the bot, you will get one by one a number by pages. You can
choose:
Y(es) - include the page
N(o) - do not include the page or
I(gnore) - do not include the page, but if you meet it again, ask again.
X - add the page, but do not check links to and from it

Other possiblities:
A(dd) - add another page, which may have been one that was included before
C(heck) - check links to and from the page, but do not add the page itself
R(emove) - remove a page that is already in the list
L(ist) - show current list of pages to include or to check
"""
# (C) Andre Engels, 2004
# (C) Pywikibot team, 2005-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import codecs
import sys

import pywikibot

from pywikibot.bot import NoRedirectPageBot, SingleSiteBot
from pywikibot import pagegenerators, i18n, textlib

from pywikibot.tools import DequeGenerator


class MakeCatBot(SingleSiteBot, NoRedirectPageBot):

    """Bot tries to find new articles for a given category."""

    @staticmethod
    def needcheck(pl):
        """Verify whether the current page may be processed."""
        global main_ns, checked, skipdates
        if main_ns:
            if pl.namespace() != 0:
                return False
        if pl in checked:
            return False
        if skipdates:
            if pl.autoFormat()[0] is not None:
                return False
        return True

    def change_category(self, page, catlist):
        """Change the category of page."""
        pass

    @classmethod
    def include(cls, pl, checklinks=True, realinclude=True, linkterm=None,
                summary=''):
        """Include the current page to the working category."""
        global mysite
        global workingcat, parentcats, removeparent
        global checkforward, checkbackward
        global checked, tocheck
        cl = checklinks
        if linkterm:
            actualworkingcat = pywikibot.Category(mysite, workingcat.title(),
                                                  sort_key=linkterm)
        else:
            actualworkingcat = workingcat
        if realinclude:
            try:
                text = pl.get()
            except pywikibot.NoPage:
                pass
            except pywikibot.IsRedirectPage:
                cl = True
            else:
                cats = [x for x in pl.categories()]
                if workingcat not in cats:
                    cats = [x for x in pl.categories()]
                    for c in cats:
                        if c in parentcats:
                            if removeparent:
                                pl.change_category(actualworkingcat,
                                                   summary=summary)
                                break
                    else:
                        pl.put(textlib.replaceCategoryLinks(
                            text, cats + [actualworkingcat], site=pl.site),
                            summary=summary)
        if cl:
            if checkforward:
                for page2 in pl.linkedPages():
                    if cls.needcheck(page2):
                        tocheck.append(page2)
                        checked[page2] = page2
            if checkbackward:
                for ref_page in pl.getReferences():
                    if cls.needcheck(ref_page):
                        tocheck.append(ref_page)
                        checked[ref_page] = ref_page

    def skip_page(self, page):
        """Check whether the page is to be skipped."""
        pass

    @classmethod
    def asktoadd(cls, pl, summary):
        """Work on current page and ask to add article to category."""
        global mysite
        global checked, tocheck
        global excludefile
        if pl.site != mysite:
            return
        if pl.isRedirectPage():
            pl2 = pl.getRedirectTarget()
            if cls.needcheck(pl2):
                tocheck.append(pl2)
                checked[pl2] = pl2
            return
        ctoshow = 500
        pywikibot.output('')
        pywikibot.output('== {} =='.format(pl.title()))
        while True:
            answer = pywikibot.input('[y]es/[n]o/[i]gnore/[o]ther options?')
            if answer == 'y':
                cls.include(pl, summary=summary)
                break
            if answer == 'c':
                cls.include(pl, realinclude=False)
                break
            if answer == 'z':
                if pl.exists():
                    if not pl.isRedirectPage():
                        linkterm = pywikibot.input(
                            'In what manner should it be alphabetized?')
                        cls.include(pl, linkterm=linkterm, summary=summary)
                        break
                cls.include(pl, summary=summary)
                break
            elif answer == 'n':
                excludefile.write('%s\n' % pl.title())
                break
            elif answer == 'i':
                break
            elif answer == 'o':
                pywikibot.output(
                    't: Give the beginning of the text of the page')
                pywikibot.output(
                    'z: Add under another title (as [[Category|Title]])')
                pywikibot.output(
                    'x: Add the page, but do not check links to and from it')
                pywikibot.output('c: Do not add the page, but do check links')
                pywikibot.output('a: Add another page')
                pywikibot.output('l: Give a list of the pages to check')
            elif answer == 'a':
                pagetitle = pywikibot.input('Specify page to add:')
                page = pywikibot.Page(pywikibot.Site(), pagetitle)
                if page not in checked.keys():
                    cls.include(page, summary=summary)
            elif answer == 'x':
                if pl.exists():
                    if pl.isRedirectPage():
                        pywikibot.output(
                            'Redirect page. Will be included normally.')
                        cls.include(pl, realinclude=False)
                    else:
                        cls.include(pl, checklinks=False, summary=summary)
                else:
                    pywikibot.output('Page does not exist; not added.')
                break
            elif answer == 'l':
                pywikibot.output('Number of pages still to check: {}'
                                 .format(len(tocheck)))
                pywikibot.output('Pages to be checked:')
                pywikibot.output(' - '.join(page.title() for page in tocheck))
                pywikibot.output('== {} =='.format(pl.title()))
            elif answer == 't':
                pywikibot.output('== {} =='.format(pl.title()))
                try:
                    pywikibot.output('' + pl.get(get_redirect=True)[0:ctoshow])
                except pywikibot.NoPage:
                    pywikibot.output('Page does not exist.')
                ctoshow += 500
            else:
                pywikibot.output('Not understood.')


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    global main_ns, skipdates
    global mysite
    global workingcat, parentcats, removeparent
    global checkforward, checkbackward
    global checked, tocheck
    global excludefile

    main_ns = True
    skipdates = False
    removeparent = True
    checkforward = True
    checkbackward = True
    checked = {}
    tocheck = DequeGenerator()

    checkbroken = True
    workingcatname = ''

    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        if arg.startswith('-nodate'):
            skipdates = True
        elif arg.startswith('-forward'):
            checkbackward = False
            checkbroken = False
        elif arg.startswith('-exist'):
            checkbroken = False
        elif arg.startswith('-keepparent'):
            removeparent = False
        elif arg.startswith('-all'):
            main_ns = False
        elif not workingcatname:
            workingcatname = arg

    if not workingcatname:
        pywikibot.bot.suggest_help(missing_parameters=['working category'])
        sys.exit(0)

    mysite = pywikibot.Site()
    summary = i18n.twtranslate(mysite, 'makecat-create',
                               {'cat': workingcatname})
    workingcat = pywikibot.Category(mysite,
                                    '%s%s'
                                    % (mysite.namespaces.CATEGORY,
                                       workingcatname))
    filename = pywikibot.config.datafilepath(
        'category',
        workingcatname.encode('ascii', 'xmlcharrefreplace').decode('ascii') +
        '_exclude.txt')
    try:
        with codecs.open(filename, 'r', encoding=mysite.encoding()) as f:
            for line in f.readlines():
                # remove leading and trailing spaces, LF and CR
                line = line.strip()
                if not line:
                    continue
                pl = pywikibot.Page(mysite, line)
                checked[pl] = pl

        excludefile = codecs.open(filename, 'a', encoding=mysite.encoding())
    except IOError:
        # File does not exist
        excludefile = codecs.open(filename, 'w', encoding=mysite.encoding())

    # Get parent categories in order to `removeparent`
    try:
        parentcats = workingcat.categories()
    except pywikibot.Error:
        parentcats = []

    # Do not include articles already in subcats; only checking direct subcats
    subcatlist = list(workingcat.subcategories())
    if subcatlist:
        subcatlist = pagegenerators.PreloadingGenerator(subcatlist)
        for cat in subcatlist:
            artlist = list(cat.articles())
            for page in artlist:
                checked[page] = page

    # Fetch articles in category, and mark as already checked (seen)
    # If category is empty, ask user if they want to look for pages
    # in a diferent category.
    articles = list(workingcat.articles(content=True))
    if not articles:
        pywikibot.output('Category {} does not exist or is empty. '
                         'Which page to start with?'
                         .format(workingcatname))
        answer = pywikibot.input('(Default is [[{}]]):'.format(workingcatname))
        if not answer:
            answer = workingcatname
        pywikibot.output('' + answer)
        pl = pywikibot.Page(mysite, answer)
        articles = [pl]

    for pl in articles:
        checked[pl] = pl
        MakeCatBot.include(pl, summary=summary)

    gen = pagegenerators.DequePreloadingGenerator(tocheck)

    for page in gen:
        if checkbroken or page.exists():
            MakeCatBot.asktoadd(page, summary)


if __name__ == '__main__':
    try:
        main()
    finally:
        try:
            excludefile.close()
        except Exception:
            pass
