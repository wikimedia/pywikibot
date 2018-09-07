#!/usr/bin/python
# -*- coding: UTF-8 -*-
"""
Bot to add new or existing categories to pages.

This bot takes as its argument the name of a new or existing category.
Multiple categories may be given. It will then try to find new articles
for these categories (pages linked to and from pages already in the category),
asking the user which pages to include and which not.

The following command line parameters are supported:

-nodates     Automatically skip all pages that are years or dates
             (years only work AD, dates only for certain languages).

-forward     Only check pages linked from pages already in the category,
             not pages linking to them. Is less precise but quite a bit faster.

-exist       Only ask about pages that do actually exist;
             drop any titles of non-existing pages silently.
             If -forward is chosen, -exist is automatically implied.

-keepparent  Do not remove parent categories of the category to be worked on.

-all         Work on all pages (default: only main namespace)

When running the bot, you will get one by one a number by pages.
You can choose:

* [y]es      - include the page
* [n]o       - do not include the page or
* [i]gnore   - do not include the page, but if you meet it again, ask again.

Other possibilities:

* [m]ore     - show more content of the page starting from the beginning
* sort [k]ey - add with sort key like [[Category|Title]]
* [s]kip     - add the page, but skip checking links to and from it
* [c]heck    - check links to and from the page, but do not add the page itself
* [o]ther    - add another page, which may have been included before
* [l]ist     - show current list of pages to include or to check

"""
# (C) Andre Engels, 2004
# (C) Pywikibot team, 2005-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import codecs

import pywikibot

from pywikibot.bot import NoRedirectPageBot, SingleSiteBot
from pywikibot import pagegenerators, i18n, textlib

from pywikibot.tools import DequeGenerator


class MakeCatBot(SingleSiteBot, NoRedirectPageBot):

    """Bot tries to find new articles for a given category."""

    def __init__(self, **kwargs):
        """Initializer."""
        self.availableOptions.update({
            'all': False,
            'exist': False,
            'forward': False,
            'keepparent': False,
            'nodate': False,
        })
        super(MakeCatBot, self).__init__(**kwargs)
        self.skipdates = self.getOption('nodate')
        self.checkforward = True
        self.checkbackward = not self.getOption('forward')
        self.checkbroken = not (self.getOption('forward')
                                and self.getOption('exist'))
        self.removeparent = not self.getOption('keepparent')
        self.main = not self.getOption('all')

    def needcheck(self, page):
        """Verify whether the current page may be processed."""
        global checked
        return not (self.main and page.namespace() != 0
                    or page in checked
                    or self.skipdates and page.autoFormat()[0] is not None)

    def change_category(self, page, catlist):
        """Change the category of page."""
        pass

    def include(self, pl, checklinks=True, realinclude=True, linkterm=None,
                summary=''):
        """Include the current page to the working category."""
        global workingcat, parentcats
        global checked, tocheck
        cl = checklinks
        mysite = self.site
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
                            if self.removeparent:
                                pl.change_category(actualworkingcat,
                                                   summary=summary)
                                break
                    else:
                        pl.put(textlib.replaceCategoryLinks(
                            text, cats + [actualworkingcat], site=pl.site),
                            summary=summary)
        if cl:
            if self.checkforward:
                for page2 in pl.linkedPages():
                    if self.needcheck(page2):
                        tocheck.append(page2)
                        checked[page2] = page2
            if self.checkbackward:
                for ref_page in pl.getReferences():
                    if self.needcheck(ref_page):
                        tocheck.append(ref_page)
                        checked[ref_page] = ref_page

    def skip_page(self, page):
        """Check whether the page is to be skipped."""
        pass

    def asktoadd(self, pl, summary):
        """Work on current page and ask to add article to category."""
        global checked, tocheck
        global excludefile
        mysite = self.site
        if pl.site != mysite:
            return
        if pl.isRedirectPage():
            pl2 = pl.getRedirectTarget()
            if self.needcheck(pl2):
                tocheck.append(pl2)
                checked[pl2] = pl2
            return
        ctoshow = 500
        pywikibot.output('')
        pywikibot.output('== {} =='.format(pl.title()))
        while True:
            answer = pywikibot.input('[y]es/[n]o/[i]gnore/[h]elp for options?')
            if answer == 'y':
                self.include(pl, summary=summary)
                break
            if answer == 'c':
                self.include(pl, realinclude=False)
                break
            if answer == 'k':
                if pl.exists() and not pl.isRedirectPage():
                    linkterm = pywikibot.input(
                        'In what manner should it be alphabetized?')
                    self.include(pl, linkterm=linkterm, summary=summary)
                    break
                self.include(pl, summary=summary)
                break
            elif answer == 'n':
                excludefile.write('%s\n' % pl.title())
                break
            elif answer == 'i':
                break
            elif answer == 'h':
                pywikibot.output("""
[m]ore:     show more content of the page starting from the beginning
sort [k]ey: Add with sort key like [[Category|Title]]
[s]kip:     Add the page, but skip checking links
[c]heck:    Do not add the page, but do check links
[o]ther:    Add another page
[l]ist:     Show a list of the pages to check
""")
            elif answer == 'o':
                pagetitle = pywikibot.input('Specify page to add:')
                page = pywikibot.Page(pywikibot.Site(), pagetitle)
                if page not in checked.keys():
                    self.include(page, summary=summary)
            elif answer == 's':
                if not pl.exists():
                    pywikibot.output('Page does not exist; not added.')
                elif pl.isRedirectPage():
                    pywikibot.output(
                        'Redirect page. Will be included normally.')
                    self.include(pl, realinclude=False)
                else:
                    self.include(pl, checklinks=False, summary=summary)
                break
            elif answer == 'l':
                pywikibot.output('Number of pages still to check: {}'
                                 .format(len(tocheck)))
                pywikibot.output('Pages to be checked:')
                pywikibot.output(' - '.join(page.title() for page in tocheck))
                pywikibot.output('== {} =='.format(pl.title()))
            elif answer == 'm':
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
    global workingcat, parentcats
    global checked, tocheck
    global excludefile

    checked = {}
    tocheck = DequeGenerator()

    workingcatname = ''

    options = {}
    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        option = arg[1:]
        if not arg.startswith('-'):
            if not workingcatname:
                workingcatname = arg
            else:
                pywikibot.warning('Working category "{}" is already given.'
                                  .format(workingcatname))
        else:
            options[option] = True

    if not workingcatname:
        pywikibot.bot.suggest_help(missing_parameters=['working category'])
        return

    mysite = pywikibot.Site()
    summary = i18n.twtranslate(mysite, 'makecat-create',
                               {'cat': workingcatname})

    bot = MakeCatBot(site=mysite, **options)

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
        bot.include(pl, summary=summary)

    gen = pagegenerators.DequePreloadingGenerator(tocheck)

    for page in gen:
        if bot.checkbroken or page.exists():
            bot.asktoadd(page, summary)


if __name__ == '__main__':
    try:
        main()
    finally:
        try:
            excludefile.close()
        except Exception:
            pass
