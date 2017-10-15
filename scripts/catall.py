#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script shows the categories on each page and lets you change them.

For each page in the target wiki:

- If the page contains no categories, you can specify a list of categories to
  add to the page.
- If the page already contains one or more categories, you can specify a new
  list of categories to replace the current list of categories of the page.

Usage:

    python pwb.py catall [start]

If no starting name is provided, the bot starts at 'A'.

Options:
-onlynew : Only run on pages that do not yet have a category.
"""
#
# (C) Rob W.W. Hooft, Andre Engels, 2004
# (C) Pywikibot team, 2004-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot
from pywikibot import i18n, textlib
from pywikibot.bot import QuitKeyboardInterrupt


def choosecats(pagetext):
    """Coose categories."""
    chosen = []
    done = False
    length = 1000
    # TODO: → input_choice
    pywikibot.output("""Give the new categories, one per line.
Empty line: if the first, don't change. Otherwise: Ready.
-: I made a mistake, let me start over.
?: Give the text of the page with GUI.
??: Give the text of the page in console.
xx: if the first, remove all categories and add no new.
q: quit.""")
    while not done:
        choice = pywikibot.input(u"?")
        if choice == "":
            done = True
        elif choice == "-":
            chosen = choosecats(pagetext)
            done = True
        elif choice == "?":
            from pywikibot import editor as editarticle
            editor = editarticle.TextEditor()
            editor.edit(pagetext)
        elif choice == "??":
            pywikibot.output(pagetext[0:length])
            length = length + 500
        elif choice == "xx" and chosen == []:
            chosen = None
            done = True
        elif choice == "q":
            raise QuitKeyboardInterrupt
        else:
            chosen.append(choice)
    return chosen


def make_categories(page, list, site=None):
    """Make categories."""
    if site is None:
        site = pywikibot.Site()
    pllist = []
    for p in list:
        cattitle = "%s:%s" % (site.namespaces.CATEGORY, p)
        pllist.append(pywikibot.Page(site, cattitle))
    page.put_async(textlib.replaceCategoryLinks(page.get(), pllist,
                                                site=page.site),
                   summary=i18n.twtranslate(site, 'catall-changing'))


def main(*args):
    """
    Process command line arguments and perform task.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    docorrections = True
    start = 'A'

    local_args = pywikibot.handle_args(args)

    for arg in local_args:
        if arg == '-onlynew':
            docorrections = False
        else:
            start = arg

    mysite = pywikibot.Site()

    for p in mysite.allpages(start=start):
        try:
            text = p.get()
            cats = p.categories()
            if not cats:
                pywikibot.output(u"========== %s ==========" % p.title())
                pywikibot.output('No categories')
                pywikibot.output('-' * 40)
                newcats = choosecats(text)
                if newcats != [] and newcats is not None:
                    make_categories(p, newcats, mysite)
            elif docorrections:
                pywikibot.output(u"========== %s ==========" % p.title())
                for c in cats:
                    pywikibot.output(c.title())
                pywikibot.output('-' * 40)
                newcats = choosecats(text)
                if newcats is None:
                    make_categories(p, [], mysite)
                elif newcats != []:
                    make_categories(p, newcats, mysite)
        except pywikibot.IsRedirectPage:
            pywikibot.output(u'%s is a redirect' % p.title())


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pywikibot.output('\nQuitting program...')
