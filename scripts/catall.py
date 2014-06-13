# -*- coding: utf-8 -*-
"""
Add or change categories on a number of pages.

Usage:
    catall.py [start]

Provides the categories on the page and asks whether to change them.

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
__version__ = '$Id$'
#

import pywikibot
from pywikibot import i18n, textlib


def choosecats(pagetext):
    chosen = []
    done = False
    length = 1000
    print("""Give the new categories, one per line.
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
            raise pywikibot.QuitKeyboardInterrupt
        else:
            chosen.append(choice)
    return chosen


def make_categories(page, list, site=None):
    if site is None:
        site = pywikibot.Site()
    pllist = []
    for p in list:
        cattitle = "%s:%s" % (site.category_namespace(), p)
        pllist.append(pywikibot.Page(site, cattitle))
    page.put_async(textlib.replaceCategoryLinks(page.get(), pllist,
                                                site=page.site),
                   comment=i18n.twtranslate(site.code, 'catall-changing'))


def main():
    docorrections = True
    start = 'A'

    local_args = pywikibot.handleArgs()

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
                print "No categories"
                print "-" * 40
                newcats = choosecats(text)
                if newcats != [] and newcats is not None:
                    make_categories(p, newcats, mysite)
            elif docorrections:
                pywikibot.output(u"========== %s ==========" % p.title())
                for c in cats:
                    pywikibot.output(c.title())
                print "-" * 40
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
